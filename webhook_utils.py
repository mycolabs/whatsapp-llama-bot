import os
import base64
import asyncio
import requests
import httpx
from PIL import Image
from dotenv import load_dotenv
from io import BytesIO
from pathlib import Path

# Load .env file from the same directory as this file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
MEDIA_URL = "https://graph.facebook.com/v20.0/{media_id}"
BASE_URL = os.getenv("BASE_URL")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8000/process")

# Debug: Print loaded environment variables (mask sensitive data)
print(f"DEBUG: WHATSAPP_API_URL loaded: {WHATSAPP_API_URL is not None}")
print(f"DEBUG: META_ACCESS_TOKEN loaded: {META_ACCESS_TOKEN is not None}")
print(f"DEBUG: GROQ_API_KEY loaded: {GROQ_API_KEY is not None}")
if WHATSAPP_API_URL:
    print(f"DEBUG: WHATSAPP_API_URL value: {WHATSAPP_API_URL}")

def send_message(to: str, text: str):
    if not text:
        print("Error: Message text is empty.")
        return

    if not WHATSAPP_API_URL:
        print("Error: WHATSAPP_API_URL is not set in environment variables.")
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
        print("Message sent")
    else:
        print(f"Send failed: {response.text}")



async def send_message_async(user_phone: str, message: str):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, send_message, user_phone, message)



        
async def send_audio_message(to: str, file_path: str):
    if not WHATSAPP_API_URL:
        print("Error: WHATSAPP_API_URL is not set in environment variables.")
        return
    
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/media"
    with open(file_path, "rb") as f:
        files = { "file": ("reply.mp3", open(file_path, "rb"), "audio/mpeg")}
        params = {
            "messaging_product": "whatsapp",
            "type": "audio",
            "access_token": META_ACCESS_TOKEN
        }
        response = requests.post(url, params=params, files=files)

    if response.status_code == 200:
        media_id = response.json().get("id")
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
        requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
    else:
        print("Audio upload failed:", response.text)






async def llm_reply_to_text_v2(user_input: str, user_phone: str, media_id: str = None,kind: str = None):
    try:
        # print("inside this function")
        headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

        json_data = {
            'text': user_input
        }
        
        print("AGENT_URL USED:", AGENT_URL)
        
        async with httpx.AsyncClient() as client:
          response = await client.post(AGENT_URL, json=json_data, headers=headers,timeout=60)
          
          # Check if response has content before parsing JSON
          if response.status_code == 200:
              try:
                  response_data = response.json()
                  # print(response_data)
                  # The /process endpoint returns {"reply": "..."}
                  message_content = response_data.get('reply')
                  if message_content:
                      loop = asyncio.get_running_loop()
                      await loop.run_in_executor(None, send_message, user_phone, message_content)
                  else:
                      print("Error: Empty message content from LLM API")
                      if WHATSAPP_API_URL:
                          await send_message_async(user_phone, "Received empty response from LLM API.")
              except Exception as json_error:
                  print(f"Error parsing LLM API response: {json_error}")
                  print(f"Response status: {response.status_code}")
                  print(f"Response text: {response.text[:200]}")
                  if WHATSAPP_API_URL:
                      await send_message_async(user_phone, "Sorry, I received an invalid response from the server.")
          else:
              print(f"Error: LLM API returned status {response.status_code}")
              print(f"Response text: {response.text[:200]}")
              if WHATSAPP_API_URL:
                  await send_message_async(user_phone, "Sorry, the server is currently unavailable.")

    except Exception as e:
        print("LLM error:", e)
        if WHATSAPP_API_URL:
            await send_message_async(user_phone, "Sorry, something went wrong while generating a response.")
        else:
            print("Cannot send error message: WHATSAPP_API_URL is not set.")