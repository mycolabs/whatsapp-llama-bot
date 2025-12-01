Here's the complete fixed `webhook_main.py` - just copy and replace the entire file:

```python
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
# Use absolute imports for Railway/Gunicorn compatibility
# Relative imports (from .webhook_utils) don't work with Gunicorn
# Absolute imports work in both local and production environments
from webhook_utils import (
    send_message,
    send_audio_message,
    llm_reply_to_text_v2
)
from ec2_services import (
    fetch_media,
    text_to_speech
)
import os
import requests
import httpx
from dotenv import load_dotenv
#from utils import handle_image_message

load_dotenv()
app = FastAPI()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
AGENT_URL = os.getenv("AGENT_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mysecret123")  # Default for local dev, override in production

class WhatsAppMessage(BaseModel):
    object: str
    entry: list


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Railway and monitoring.
    Returns 200 OK if the service is running.
    """
    return {
        "status": "healthy",
        "service": "whatsapp-llama4-bot",
        "version": "1.0.0"
    }


@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge)

    return {"error": "Invalid token"}


@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    message_data = WhatsAppMessage(**data)
    
    change = message_data.entry[0]["changes"][0]["value"]
    print(change)
    if 'messages' in change:
        message = change["messages"][-1]
        user_phone = message["from"]
        print(message)
        if "text" in message:
            user_message = message["text"]["body"].lower()
            print(user_message)
            background_tasks.add_task(llm_reply_to_text_v2, user_message, user_phone,None,None)
        elif "image" in message:
            media_id = message["image"]["id"]
            print(media_id)
            caption = message["image"].get("caption", "")
            # background_tasks.add_task(handle_image_message, media_id, user_phone, caption)
            background_tasks.add_task(llm_reply_to_text_v2,caption,user_phone,media_id,'image')
        elif message.get("audio"):
            media_id = message["audio"]["id"]
            print("Audio received:", media_id)

            # Step 1: Download audio from WhatsApp (must await)
            audio_bytes = await fetch_media(media_id)

            if audio_bytes is None:
                send_message(user_phone, "Failed to download audio.")
                return JSONResponse(content={"status": "error"}), 200

            # Step 2: Convert audio -> text using Groq
            transcript = await text_to_speech(audio_bytes)

            if not transcript:
                send_message(user_phone, "Sorry, I could not understand the audio.")
                return JSONResponse(content={"status": "error"}), 200

            # Step 3: Send transcript to LLM
            background_tasks.add_task(
                llm_reply_to_text_v2,
                transcript,
                user_phone,
                media_id,
                "audio"
            )

            return JSONResponse(content={"status": "ok"}), 200
        return JSONResponse(content={"status": "ok"}), 200


@app.post("/process")
async def process_message(data: dict):
    from groq import Groq
    
    if not GROQ_API_KEY:
        return {"reply": "Error: GROQ_API_KEY is not set in environment variables."}
    
    client = Groq(api_key=GROQ_API_KEY)

    user_text = data.get("text", "")
    
    if not user_text:
        return {"reply": "Error: No text provided in request."}

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": user_text}]
        )

        reply = completion.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        print(f"Groq API error: {e}")
        return {"reply": f"Error: Failed to generate response. {str(e)}"}
```

---

**Changes made:**

1. ✅ Added `PlainTextResponse` to the imports (line 2)
2. ✅ Changed `return int(challenge)` to `return PlainTextResponse(content=challenge)` (line 54)

---

**How to update:**

1. Go to GitHub → `webhook_main.py`
2. Click **Edit** (pencil icon)
3. Select all (Ctrl+A) and delete
4. Paste this entire code
5. Click **"Commit changes"**

Railway will auto-redeploy in 1-2 minutes. Then test your webhook again! 🚀
