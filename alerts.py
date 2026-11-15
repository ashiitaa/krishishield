import os
from twilio.rest import Client

# Add your free Twilio trial credentials as environment variables (or paste for local demo)
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID", "YOUR_TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "YOUR_TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")

def send_keypad_alert(phone_number: str, farmer_name: str, verdict: str, safe_window: str, dose_text: str, lang: str = "hi") -> dict:
    if lang == "hi":
        if verdict == "HOLD":
            msg = f"Namaste {farmer_name}. KrishiShield chetavni: Aaj khaad na daalein, baarish se khaad beh jayegi. {safe_window} ko {dose_text} ka upyog karein."
        else:
            msg = f"Namaste {farmer_name}. KrishiShield suchna: Aaj mausam surakshit hai. Aap {dose_text} daal sakte hain."
    else:
        msg = f"Hello {farmer_name}. KrishiShield Alert: Status is {verdict}. Safe window: {safe_window}. {dose_text}."

    # If Twilio keys are not configured yet, return a clean simulated success for testing
    if TWILIO_SID == "YOUR_TWILIO_SID":
        return {"status": "simulated_sent", "to": phone_number, "script": msg}

    client = Client(TWILIO_SID, TWILIO_TOKEN)
    sms = client.messages.create(body=msg, from_=TWILIO_FROM, to=phone_number)
    call = client.calls.create(
        twiml=f'<Response><Say language="hi-IN">{msg}</Say></Response>',
        from_=TWILIO_FROM,
        to=phone_number
    )
    return {"status": "sent", "sms_sid": sms.sid, "call_sid": call.sid, "script": msg}