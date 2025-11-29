# WhatsApp Llama 4 Bot - Multi-modal Chatbot

Welcome to the WhatsApp Llama4 Bot! This bot leverages the power of LLM APIs (Groq, Llama, Together) to provide intelligent and interactive responses to users via WhatsApp. It supports text, image, and audio interactions, making it a versatile tool for various use cases.

## Key Features

- **Text Interaction**: Users can send text messages to the bot, which are processed using LLM APIs to generate accurate and contextually relevant responses.
- **Image Reasoning**: The bot can analyze images sent by users, providing insights, descriptions, or answers related to the image content.
- **Audio-to-Text**: Users can send audio messages, which are transcribed to text using Groq's Whisper model, processed by the LLM, and sent back as text responses.

## Technical Overview

### Architecture

- **FastAPI**: The bot is built using FastAPI, a modern web framework for building APIs with Python.
- **Asynchronous Processing**: Utilizes `httpx` for making asynchronous HTTP requests to external APIs, ensuring efficient handling of media files.
- **Environment Configuration**: Uses `dotenv` to manage environment variables, keeping sensitive information like API keys secure.

### Important Integrations

- **WhatsApp Business Cloud API**: Facilitates sending and receiving messages, images, and audio files.
- **Groq API**: Provides LLM responses and handles speech-to-text (STT) transcription using Whisper.
- **Llama/Together APIs**: Alternative LLM providers for generating responses.

---

## Local Setup and Installation

### Prerequisites

- Python 3.10 or higher
- WhatsApp Business Cloud API account
- API keys for at least one LLM provider (Groq recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/meta-llama/llama-cookbook.git
cd llama-cookbook/end-to-end-use-cases/whatsapp_llama_4_bot
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys and configuration:

```plaintext
# WhatsApp Business API Configuration
PHONE_NUMBER_ID=your_phone_number_id
META_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_API_URL=https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages

# Webhook Configuration
VERIFY_TOKEN=your_webhook_verify_token
AGENT_URL=http://localhost:8000/process

# LLM Provider API Keys (at least one required)
GROQ_API_KEY=your_groq_api_key
LLAMA_API_KEY=your_llama_api_key
TOGETHER_API_KEY=your_together_api_key
OPENAI_API_KEY=your_openai_api_key

# Optional Configuration
BASE_URL=your_base_url_if_needed
ACCESS_TOKEN=your_access_token_if_needed
```

**⚠️ SECURITY WARNING**: Never commit your `.env` file to version control. It contains sensitive API keys and tokens. The `.env` file is already included in `.gitignore` to prevent accidental commits.

### Step 5: Run the Application Locally

Start the FastAPI server:

```bash
python -m uvicorn whatsapp_llama_4_bot.webhook_main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`

### Step 6: Configure WhatsApp Webhook

1. **Get your webhook URL**: Use a service like [ngrok](https://ngrok.com/) to expose your local server:
   ```bash
   ngrok http 8000
   ```
   Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

2. **Set up webhook in Meta Developer Console**:
   - Go to [Meta for Developers](https://developers.facebook.com/apps/)
   - Select your WhatsApp Business App
   - Navigate to WhatsApp > Configuration
   - Set Webhook URL: `https://your-ngrok-url.ngrok.io/webhook`
   - Set Verify Token: (same as `VERIFY_TOKEN` in your `.env`)
   - Subscribe to `messages` events

3. **Test the webhook**:
   - Send a message to your WhatsApp Business number
   - Check the server logs for incoming messages

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `PHONE_NUMBER_ID` | Yes | Your WhatsApp Business Phone Number ID |
| `META_ACCESS_TOKEN` | Yes | WhatsApp Business API access token |
| `WHATSAPP_API_URL` | Yes | WhatsApp API endpoint URL (format: `https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages`) |
| `VERIFY_TOKEN` | Yes | Webhook verification token (must match Meta console) |
| `AGENT_URL` | No | LLM processing endpoint (defaults to `http://localhost:8000/process`) |
| `GROQ_API_KEY` | Yes* | Groq API key for LLM and transcription |
| `LLAMA_API_KEY` | No | Llama API key (alternative LLM provider) |
| `TOGETHER_API_KEY` | No | Together AI API key (alternative LLM provider) |
| `OPENAI_API_KEY` | No | OpenAI API key (if using OpenAI models) |
| `BASE_URL` | No | Base URL for your application (if needed) |
| `ACCESS_TOKEN` | No | Additional access token (if needed) |

*At least one LLM provider API key is required (Groq recommended for full functionality)

---

## Deployment on Railway

### Step 1: Prepare for Deployment

1. Ensure all environment variables are documented in `.env.example`
2. Verify `.gitignore` includes `.env` and other sensitive files
3. Test the application locally

### Step 2: Deploy to Railway

1. **Create Railway Account**:
   - Go to [Railway.app](https://railway.app/)
   - Sign up/login with GitHub

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**:
   - Go to Project Settings > Variables
   - Add all variables from your `.env` file
   - **Important**: Update `AGENT_URL` to your Railway app URL:
     ```
     AGENT_URL=https://your-app-name.railway.app/process
     ```

4. **Configure Build Settings**:
   - Build Command: (leave empty, Railway auto-detects)
   - Start Command: `uvicorn whatsapp_llama_4_bot.webhook_main:app --host 0.0.0.0 --port $PORT`
   - Python Version: 3.10 or higher

5. **Set Webhook URL**:
   - Copy your Railway app URL (e.g., `https://your-app.railway.app`)
   - Update WhatsApp webhook in Meta Console to: `https://your-app.railway.app/webhook`

6. **Deploy**:
   - Railway will automatically build and deploy
   - Check the logs for any errors
   - Test by sending a message to your WhatsApp number

### Railway-Specific Notes

- Railway automatically assigns a `PORT` environment variable
- Use `$PORT` in your start command (Railway handles this)
- Railway provides HTTPS automatically
- Update `AGENT_URL` to use your Railway domain

---

## API Endpoints

### `GET /webhook`
Webhook verification endpoint for WhatsApp.

**Query Parameters**:
- `hub.mode`: Should be "subscribe"
- `hub.verify_token`: Your verify token
- `hub.challenge`: Challenge string from WhatsApp

**Response**: Returns the challenge if verification succeeds.

### `POST /webhook`
Receives incoming WhatsApp messages.

**Request Body**: WhatsApp webhook payload

**Response**: `{"status": "ok"}`

### `POST /process`
Processes text messages using the configured LLM.

**Request Body**:
```json
{
  "text": "Your message here"
}
```

**Response**:
```json
{
  "reply": "LLM generated response"
}
```

---

## Security Best Practices

1. **Never commit `.env` files**: Always use `.env.example` for documentation
2. **Rotate API keys regularly**: Update your API keys periodically
3. **Use strong verify tokens**: Use a random, secure string for `VERIFY_TOKEN`
4. **Limit webhook access**: Use HTTPS and verify requests when possible
5. **Monitor API usage**: Set up alerts for unusual API usage patterns
6. **Keep dependencies updated**: Regularly update `requirements.txt` packages

---

## Troubleshooting

### Webhook Verification Fails
- Ensure `VERIFY_TOKEN` in `.env` matches Meta Console
- Check that the webhook URL is accessible (use ngrok for local testing)
- Verify HTTPS is enabled (required by WhatsApp)

### Messages Not Received
- Check server logs for errors
- Verify `META_ACCESS_TOKEN` is valid and not expired
- Ensure webhook is subscribed to `messages` events in Meta Console

### LLM Not Responding
- Verify at least one LLM API key is set (`GROQ_API_KEY` recommended)
- Check API key validity and quota
- Review server logs for API errors

### Audio Transcription Fails
- Ensure `GROQ_API_KEY` is set (required for Whisper transcription)
- Check audio file format (OGG/Opus supported)
- Verify audio file is downloaded correctly (check logs)

---

## Project Structure

```
whatsapp_llama_4_bot/
├── __init__.py
├── webhook_main.py          # Main FastAPI application
├── webhook_utils.py          # WhatsApp message handling utilities
├── ec2_services.py           # Media processing and LLM services
├── ec2_endpoints.py          # Additional API endpoints
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

---

## License

This project is licensed under the MIT License.

## Contributing

We welcome contributions to enhance the capabilities of this bot. Please feel free to submit issues or pull requests.

**Before contributing**:
1. Ensure `.env` is not committed
2. Follow the existing code style
3. Add tests if applicable
4. Update documentation as needed

---

## Additional Resources

- [WhatsApp Business Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Groq API Documentation](https://console.groq.com/docs)
- [Railway Deployment Guide](https://docs.railway.app/)
