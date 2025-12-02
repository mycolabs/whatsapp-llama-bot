import os
import base64
import asyncio
import requests
import httpx
from PIL import Image
from dotenv import load_dotenv
from io import BytesIO

# ---------------------------------
# Load environment variables safely
# ---------------------------------
load_dotenv()

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")   # full API url
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AGENT_URL = os.getenv("AGENT_URL")

# Correct media fetch URL
MEDIA_URL = f"https://graph.facebook.com/v20.0/{{media_id}}?access_token={META_ACCESS_TOKEN}"

# Debug
print("UTILS LOADED →")
print("META_ACCESS_TOKEN:", bool(META_ACCESS_TOKEN))
print("PHONE_NUMBER_ID:", PHONE_NUMBER_ID)
print("WHATSAPP_API_URL:", WHATSAPP_API_URL)
print("AGENT_URL:", AGENT_URL)


# -----------------------------------------------------------------
# SEND WHATSAPP TEXT MESSAGE
# -----------------------------------------------------------------
def send_message(to: str, text: str):
    if not text:
        print("Error: empty message")
        return

    if not WHATSAPP_API_URL:
        print("Error: WHATSAPP_API_URL missing")
        return

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        print("✔ WhatsApp message sent successfully")
    else:
        print("❌ Failed to send message:", response.text)



# Async wrapper
async def send_message_async(user_phone: str, message: str):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, send_message, user_phone, message)



# -----------------------------------------------------------------
# SEND AUDIO FILE
# -----------------------------------------------------------------
async def send_audio_message(to: str, file_path: str):

    media_upload_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/media"

    with open(file_path, "rb") as f:
        files = {
            "file": ("reply.mp3", f, "audio/mpeg")
        }
        params = {
            "messaging_product": "whatsapp",
            "access_token": META_ACCESS_TOKEN
        }
        upload_response = requests.post(media_upload_url, params=params, files=files)

    if upload_response.status_code != 200:
        print("❌ Audio upload failed:", upload_response.text)
        return

    media_id = upload_response.json().get("id")

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "audio",
        "audio": {"id": media_id}
    }

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    msg_response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)

    if msg_response.status_code == 200:
        print("✔ Audio sent")
    else:
        print("❌ Failed to send audio:", msg_response.text)



# -----------------------------------------------------------------
# PROCESS TEXT → SEND TO AGENT → SEND BACK TO USER
# -----------------------------------------------------------------
async def llm_reply_to_text_v2(user_input: str, user_phone: str, media_id: str = None, kind: str = None):

    try:
        payload = {"text": user_input}

        print("AGENT_URL USED:", AGENT_URL)

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(AGENT_URL, json=payload)

        if resp.status_code != 200:
            print("❌ LLM error:", resp.text)
            await send_message_async(user_phone, "Server error, please try later")
            return

        data = resp.json()
        reply = data.get("reply")

        if not reply:
            await send_message_async(user_phone, "Received empty response")
            return

        await send_message_async(user_phone, reply)

    except Exception as e:
        print("LLM CRASH:", e)
        await send_message_async(user_phone, "Unexpected server error")
