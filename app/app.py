from quart import Quart, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
import json
import asyncio
from app.db.mongo_store import store
from agents import Agent, Runner
from app.agents.triage_agent import create_triage_agent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add a stream handler to print to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Initialize app, Twilio client, and triage agent
app = Quart(__name__)
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

# Initialize triage agent
triage_agent = create_triage_agent()

def normalize_phone_number(phone_number: str) -> str:
    """Normalize phone number by removing 'whatsapp:' prefix and spaces."""
    return phone_number.replace('whatsapp:', '').strip()

def get_conversation_history(phone_number: str) -> list:
    """Retrieve conversation history from MongoDB."""
    normalized_number = normalize_phone_number(phone_number)
    try:
        history = store.get_conversation_history(normalized_number)
        logger.info(f"Retrieved {len(history)} messages from history for {normalized_number}")
        return history
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        return []

def update_conversation_history(phone_number: str, role: str, content: str):
    """Update conversation history in MongoDB."""
    if role not in ['user', 'assistant']:
        logger.error(f"Invalid role: {role}")
        return

    normalized_number = normalize_phone_number(phone_number)
    try:
        store.append_to_history(normalized_number, role, content)
        logger.info(f"Updated conversation history for {normalized_number}")
    except Exception as e:
        logger.error(f"Error updating conversation history: {e}")

def clear_conversation_history(phone_number: str):
    """Clear conversation history for a phone number."""
    normalized_number = normalize_phone_number(phone_number)
    try:
        store.clear_conversation(normalized_number)
        logger.info(f"Cleared conversation history for {normalized_number}")
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle incoming WhatsApp messages."""
    try:
        # Get message details
        form = await request.form
        message_body = form["Body"]
        from_number = form["From"]

        logger.info(f"Received message from {from_number}: {message_body[:100]}...")

        # Get conversation history
        normalized_number = normalize_phone_number(from_number)
        conversation_history = get_conversation_history(normalized_number)

        # Format conversation history as list of input items
        input_messages = []
        for msg in conversation_history:
            input_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add current message
        input_messages.append({
            "role": "user",
            "content": message_body
        })

        # Process message with full conversation history
        result = await Runner.run(triage_agent, input_messages)
        response = result.final_output

        # Store the conversation in MongoDB
        update_conversation_history(normalized_number, "user", message_body)
        update_conversation_history(normalized_number, "assistant", response)

        # Send response through TwiML
        resp = MessagingResponse()
        resp.message(response)
        logger.debug("Sent response through TwiML")
        return str(resp)

    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return "Error processing request", 500

@app.route("/clear_conversation", methods=["POST"])
async def clear_conversation():
    """Clear conversation history for a phone number."""
    try:
        form = await request.form
        phone_number = form["phone_number"]
        clear_conversation_history(phone_number)
        return {"status": "success", "message": f"Conversation cleared for {phone_number}"}
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

@app.route("/debug/conversation/<phone_number>", methods=["GET"])
async def debug_conversation(phone_number: str):
    """Debug endpoint to view raw MongoDB data and processed conversation history."""
    try:
        normalized_number = normalize_phone_number(phone_number)
        logger.info(f"Debug request for {phone_number} (normalized: {normalized_number})")

        # Get full conversation data from store
        conversation = store.get_conversation(normalized_number)
        logger.info(f"Retrieved conversation data: {conversation}")

        # Get processed conversation history
        processed_history = get_conversation_history(normalized_number)
        logger.info(f"Retrieved {len(processed_history)} messages from history")

        return {
            "phone_number": phone_number,
            "normalized_number": normalized_number,
            "raw_data": conversation,
            "processed_history": processed_history
        }

    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return {
            "error": str(e),
            "phone_number": phone_number,
            "normalized_number": normalize_phone_number(phone_number)
        }, 500

if __name__ == "__main__":
    app.run(debug=True, port=5001) 
