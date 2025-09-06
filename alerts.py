# alerts.py
import requests
from twilio.rest import Client

def send_telegram(bot_token, chat_id, text):
    if not bot_token or not chat_id:
        return {"ok": False, "msg": "Telegram not configured"}
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": chat_id, "text": text})
        return {"ok": r.status_code==200, "status": r.status_code, "text": r.text}
    except Exception as e:
        return {"ok": False, "msg": str(e)}

def send_whatsapp(twilio_sid, twilio_auth, from_whatsapp, to_whatsapp, text):
    if not twilio_sid or not twilio_auth:
        return {"ok": False, "msg": "Twilio not configured"}
    client = Client(twilio_sid, twilio_auth)
    try:
        msg = client.messages.create(from_=from_whatsapp, body=text, to=to_whatsapp)
        return {"ok": True, "sid": msg.sid}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
