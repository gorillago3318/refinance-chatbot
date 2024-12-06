# backend/routes/chatbot.py

import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Lead, BankPackage
from decorators import user_required
import openai
from calculation import calculate_repayment
from utils.whatsapp import send_whatsapp_message
from utils.presets import load_presets
from datetime import datetime
import logging
import json

# Initialize the Blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

# Initialize OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Load preset Q&A
PRESET_QA = load_presets()

# Load Admin WhatsApp Numbers from environment variable (comma-separated)
ADMIN_WHATSAPP_NUMBERS = os.getenv('ADMIN_WHATSAPP_NUMBERS', '').split(',')

@chatbot_bp.route('/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """
    Webhook endpoint to receive messages from WhatsApp and handle verification.
    """
    if request.method == 'GET':
        return verify_webhook(request)
    elif request.method == 'POST':
        return handle_incoming_message(request)
    else:
        return jsonify({"error": "Method not allowed"}), 405

def verify_webhook(req):
    """
    Handles the verification of the webhook by WhatsApp.
    """
    verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN')
    mode = req.args.get('hub.mode')
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    current_app.logger.debug(f"Webhook verification attempt: mode={mode}, token={token}, challenge={challenge}")

    if mode and token:
        if mode == 'subscribe' and token == verify_token:
            current_app.logger.info('WEBHOOK_VERIFIED')
            return challenge, 200
        else:
            current_app.logger.warning('WEBHOOK_VERIFICATION_FAILED: Token mismatch')
            return 'Verification token mismatch', 403

    return 'Hello World', 200

def handle_incoming_message(req):
    """
    Processes incoming WhatsApp messages and sends appropriate responses.
    """
    data = req.get_json()
    current_app.logger.debug(f"Received data: {json.dumps(data)}")

    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        messages = value.get('messages', [])

        if not messages:
            current_app.logger.info('No messages found in payload.')
            return jsonify({"status": "no messages"}), 200

        message = messages[0]
        from_number = message['from']  # Sender's WhatsApp number
        text = message.get('text', {}).get('body', '').strip().lower()

        current_app.logger.info(f"Received message from {from_number}: {text}")

    except (KeyError, IndexError) as e:
        current_app.logger.error(f"Invalid payload structure: {e}")
        return jsonify({"error": "Invalid payload"}), 400

    # Check if the message matches any preset Q&A
    for qa in PRESET_QA:
        if text == qa['question'].strip().lower():
            bot_reply = qa['answer']
            current_app.logger.info(f"Sending preset answer to {from_number}")
            send_whatsapp_message(from_number, bot_reply)
            return jsonify({"status": "preset answer sent"}), 200

    # If no preset answer, process the message with GPT-3
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for refinancing loans."},
                {"role": "user", "content": text}
            ]
        )
        bot_reply = response.choices[0].message['content'].strip()
        current_app.logger.info(f"Sending GPT-3 generated answer to {from_number}")
    except openai.error.OpenAIError as e:
        current_app.logger.error(f"OpenAI API error: {e}")
        bot_reply = "I'm sorry, I'm having trouble processing your request at the moment."

    # Send the reply back to the user via WhatsApp
    send_whatsapp_message(from_number, bot_reply)

    return jsonify({"status": "message processed"}), 200

@chatbot_bp.route('/submit-lead', methods=['POST'])
@jwt_required()
@user_required
def submit_lead():
    """
    Endpoint to submit a lead via API (can be used for web portal integration).
    """
    data = request.get_json()
    name = data.get('name')
    age = data.get('age')
    loan_amount = data.get('loan_amount')
    loan_tenure = data.get('loan_tenure')
    current_repayment = data.get('current_repayment')

    if not all([name, age, loan_amount, loan_tenure, current_repayment]):
        return jsonify({'message': 'All fields are required.'}), 400

    # Determine suitable bank packages
    bank_packages = BankPackage.query.all()
    suitable_packages = []
    for pkg in bank_packages:
        if pkg.min_amount <= loan_amount <= pkg.max_amount:
            suitable_packages.append({
                'id': pkg.id,
                'name': pkg.name,
                'interest_rate': pkg.interest_rate,
                'tenure_options': pkg.tenure_options.split(',')
            })

    # Create Lead
    user_id = get_jwt_identity()
    new_lead = Lead(
        referrer_id=user_id,
        name=name,
        age=age,
        loan_amount=loan_amount,
        loan_tenure=loan_tenure,
        current_repayment=current_repayment,
        status='New'  # Assuming default status is 'New'
    )

    db.session.add(new_lead)
    db.session.commit()

    # Calculate Repayment
    repayment = calculate_repayment(loan_amount, loan_tenure, 5.5)  # Example interest rate

    # Notify Admins about the new lead via WhatsApp
    notify_admins_new_lead(new_lead)

    return jsonify({
        'message': 'Lead submitted successfully.',
        'suitable_packages': suitable_packages,
        'calculated_repayment': repayment
    }), 201

def notify_admins_new_lead(lead):
    """
    Notify all admins about a new lead via WhatsApp.
    """
    message_body = (
        f"📣 *New Lead Submitted*\n\n"
        f"*Lead ID:* {lead.id}\n"
        f"*Name:* {lead.name}\n"
        f"*Age:* {lead.age}\n"
        f"*Loan Amount:* ${lead.loan_amount}\n"
        f"*Loan Tenure:* {lead.loan_tenure} years\n"
        f"*Current Repayment:* ${lead.current_repayment}\n"
        f"*Referrer:* {lead.referrer.name}\n"
        f"*Status:* {lead.status}\n"
    )

    for admin_number in ADMIN_WHATSAPP_NUMBERS:
        admin_number = admin_number.strip()
        if admin_number:  # Ensure the number is not empty
            send_whatsapp_message(admin_number, message_body)
            current_app.logger.info(f"Notification sent to admin: {admin_number}")
