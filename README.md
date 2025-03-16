# Legal AI WhatsApp Assistant

A Flask-based API that connects to Twilio WhatsApp to provide legal information using OpenAI's GPT-4 model.

![ezgif-43371b6673ae12](https://github.com/user-attachments/assets/48eb4f27-4532-4d40-b7f7-7d346bccb783)


## Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   - Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
   - Get your Twilio credentials from [Twilio Console](https://console.twilio.com/)

4. Set up Twilio WhatsApp Sandbox:
   - Go to [Twilio Console](https://console.twilio.com/)
   - Navigate to Messaging > Try it > WhatsApp
   - Follow the instructions to set up your sandbox
   - Set your webhook URL to `https://your-domain.com/webhook`

## Running the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Use ngrok or similar tool to expose your local server:
   ```bash
   ngrok http 5000
   ```
3. Update your Twilio webhook URL with the ngrok URL

## Usage

Users can send WhatsApp messages to your Twilio number, and the AI will respond with legal information while maintaining appropriate disclaimers and ethical boundaries.

## Important Notes

- This is a demonstration project and should not be used as a replacement for professional legal advice
- The AI is programmed to provide general legal information only
- Always recommend users to consult with a qualified attorney for specific legal matters
- Ensure compliance with local laws and regulations regarding legal advice

## Security Considerations

- Never commit your `.env` file
- Keep your API keys secure
- Regularly rotate your credentials
- Monitor usage to prevent abuse 
