# backend/utils/whatsapp.py

import os
import requests
import logging

def send_whatsapp_message(to, message):
    """
    Sends a WhatsApp message using the WhatsApp Business API.

    Parameters:
        to (str): Recipient's WhatsApp number in the format 'whatsapp:+1234567890'
        message (str): Message body
    """
    whatsapp_api_url = os.getenv('WHATSAPP_API_URL')  # e.g., https://graph.facebook.com/v13.0/YOUR_PHONE_NUMBER_ID/messages
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')  # Your access token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }

    try:
        response = requests.post(whatsapp_api_url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Sent message to {to}: {message}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message to {to}: {e}")
        return {"error": str(e)}
