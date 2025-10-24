import os
from django.conf import settings


def send_sms(to_number:str, message:str) -> bool:
    backend = getattr(settings, 'SMS_BACKEND', 'console')
    if backend == 'console':
        print(f'[SMS to {to_number}]: {message}')
        return True
    
    if backend == 'twilio':
        from twilio.rest import Client
        sid = os.getenv('TWILIO_ACCOUNT_SID')
        token = os.getenv('TWILIO_AUTH_TOKEN')
        sms_from = os.getenv('TWILIO_FROM')
        if not all(sid, token, sms_from):return False
        client = Client(sid, token)
        client.message.create(body=message, from_=sms_from, to=to_number)
        return True
    return False