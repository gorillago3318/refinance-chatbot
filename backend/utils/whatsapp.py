# backend/utils/whatsapp.py

import os
import requests
import logging

# Retrieve environment variables
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

def send_whatsapp_message(to, message):
    """
    Sends a WhatsApp message to the specified recipient.
    """
    if not WHATSAPP_PHONE_NUMBER_ID:
        logging.error("WhatsApp Phone Number ID is not set in environment variables.")
        return

    if not WHATSAPP_ACCESS_TOKEN:
        logging.error("WhatsApp Access Token is not set in environment variables.")
        return

    # Construct the API URL dynamically
    url = f'https://graph.facebook.com/v13.0/{WHATSAPP_PHONE_NUMBER_ID}/messages'

    headers = {
        'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {
            "body": message
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Message sent to {to}: {message}")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while sending message to {to}: {http_err} - Response: {response.text}")
    except Exception as err:
        logging.error(f"An error occurred while sending message to {to}: {err}")
