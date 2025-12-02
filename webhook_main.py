from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from webhook_utils import (
    send_message,
    send_audio_message,
    llm_reply_to_text_v2
)
from ec2_services import fetch_media, text_to_speech

import os
import httpx
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# ---------------------------
# LOAD ALL ENV VARIABLES
# ---------------------------
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
AGENT_URL = os.getenv("AGENT_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mysecret123")

print("META_ACCESS_TOKEN:", bool(META_ACCESS_TOKEN))
print("PHONE_NUMBER_ID:", PHONE_NUMBER_ID)
print("WHATSAPP_API_URL:", WHATSAPP_API_URL)
print("AGENT_URL:", AGENT_URL)


# ---------------------------
# MODELS
# ---------------------------
class WhatsAppMessage(BaseModel):
    object: str
    entry: list


# ---------------------------
# HEALTH CHECK
# ---------------------------
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "whatsapp-llama4-bot",
        "version": "1.0.1"
    }


# ---------------------------
# VERIFY WEBHOOK
# ---------------------------
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge)

    return {"error": "Invalid token"}


# ---------------------------
# HANDLE INCOMING WEBHOOK
# ---------------------------
@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    try:
        message_data = WhatsAppMessage(**data)
    except Exception:
        return JSONResponse({"status": "ignored"}, 200)

    change = message_data.entry[0]["changes"][0]["value"]

    # Debug print
    print(change)

    if "messages" not in change:
        return JSONResponse({"status": "no message"}, 200)

    message = change["messages"][-1]
    user_phone = message["from"]

    print("Incoming message:", message)

    # ---------------------------
    # TEXT MESSAGE HANDLING
    # ---------------------------
    if "text" in message:
        user_text = message["text"]["body"].strip()
        print("User text:", user_text)

        background_tasks.add_task(
            llm_reply_to_text_v2, user_text, user_phone, None, None
        )
        return JSONResponse({"status": "ok"}, 200)

    # ---------------------------
    # IMAGE MESSAGE
    # ---------------------------
    if "image" in message:
        media_id = message["image"]["id"]
        caption = message["image"].get("caption", "")

        background_tasks.add_task(
            llm_reply_to_text_v2, caption, user_phone, media_id, "image"
        )
        return JSONResponse({"status": "ok"}, 200)

    # ---------------------------
    # AUDIO MESSAGE
    # ---------------------------
    if message.get("audio"):
        media_id = message["audio"]["id"]

        print("Audio received:", media_id)
        audio_bytes = await fetch_media(media_id)

        if audio_bytes is None:
            send_message(user_phone, "Failed to download audio.")
            return JSONResponse({"status": "error"}, 200)

        transcript = await text_to_speech(audio_bytes)

        if not transcript:
            send_message(user_phone, "Sorry, I could not understand the audio.")
            return JSONResponse({"status": "error"}, 200)

        background_tasks.add_task(
            llm_reply_to_text_v2,
            transcript,
            user_phone,
            media_id,
            "audio"
        )
        return JSONResponse({"status": "ok"}, 200)

    return JSONResponse({"status": "ok"}, 200)


# ---------------------------
# AGENT PROCESSOR (LLM)
# ---------------------------
@app.post("/process")
async def process_message(data: dict):
    try:
        from groq import Groq

        if not GROQ_API_KEY:
            return {"reply": "Error: GROQ_API_KEY missing"}

        client = Groq(api_key=GROQ_API_KEY)

        user_text = data.get("text", "")
        if not user_text:
            return {"reply": "Error: No text provided"}

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": user_text}]
        )

        reply = completion.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        print("Groq Error:", e)
        return {"reply": "Error generating LLM response"}
