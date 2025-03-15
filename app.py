from quart import Quart, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from agents import Agent, Runner
from app.agents.legal_agent import create_legal_agent
import os
from dotenv import load_dotenv
import logging
import asyncio
import nest_asyncio
import time
import openai
from openai import OpenAI

# Enable nested event loops
nest_asyncio.apply()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Also enable logging for OpenAI and other libraries
logging.getLogger('openai').setLevel(logging.DEBUG)
logging.getLogger('agents').setLevel(logging.DEBUG)

# Load environment variables
logger.info("Loading environment variables...")
load_dotenv(override=True)  # Force override existing env vars

# Set OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not found in environment variables")

# Ensure API key is in environment
os.environ['OPENAI_API_KEY'] = api_key
logger.info(f"OpenAI API key loaded and set (starts with): {api_key[:15]}...")

app = Quart(__name__)

# Initialize the legal agent
try:
    legal_agent = create_legal_agent()
    logger.info("Legal agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize legal agent: {str(e)}")
    raise

# Initialize Twilio client
try:
    twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    logger.info("Twilio client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Twilio client: {str(e)}")
    raise

async def get_legal_advice(query):
    """Get legal advice using OpenAI Agent."""
    max_retries = 5  # Increased from 3
    initial_delay = 2  # Increased from 1
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Getting legal advice for query: {query} (attempt {attempt + 1}/{max_retries})")
            result = await Runner.run(legal_agent, input=query)
            logger.debug(f"Received response: {result.final_output}")
            return result.final_output
        except Exception as e:
            logger.error(f"Error getting legal advice (attempt {attempt + 1}): {str(e)}")
            if "429" in str(e):
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limited. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    return "I apologize, but our service is experiencing high demand right now. Please try again in a few minutes."
            elif "status code" in str(e).lower():
                return "I apologize, but I'm having trouble connecting to the service. Please try again in a few moments."
            else:
                logger.error(f"Unexpected error: {str(e)}")
                return "I apologize, but I encountered an unexpected error. Please try again later."
    
    return "I apologize, but I'm having trouble processing your request. Please try again later."

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle incoming WhatsApp messages."""
    logger.debug("Received webhook request")
    
    try:
        # Get the message from the request
        form = await request.form
        incoming_msg = form.get('Body', '').strip()
        from_number = form.get('From', '')
        logger.debug(f"Incoming message from {from_number}: {incoming_msg}")
        
        if not incoming_msg:
            logger.error("Empty message received")
            resp = MessagingResponse()
            resp.message("I apologize, but I didn't receive any message. Please try again with your question.")
            return str(resp)
        
        # Get legal information from OpenAI Agent
        logger.debug("Calling get_legal_advice")
        legal_response = await get_legal_advice(incoming_msg)
        logger.debug(f"Legal response received: {legal_response}")
        
        if not legal_response:
            raise ValueError("Empty response received from legal agent")
        
        # Split response if it's too long (WhatsApp limit is 1600 characters)
        if len(legal_response) > 1500:
            parts = [legal_response[i:i+1500] for i in range(0, len(legal_response), 1500)]
            
            # Send all parts through Twilio API in order
            for i, part in enumerate(parts):
                try:
                    suffix = f"\n(Part {i+1}/{len(parts)})" if len(parts) > 1 else ""
                    twilio_client.messages.create(
                        body=part + suffix,
                        from_='whatsapp:+14155238886',  # Default Twilio test number
                        to=from_number
                    )
                    logger.debug(f"Sent part {i+1} of {len(parts)}")
                except Exception as e:
                    logger.error(f"Error sending message part {i+1}: {str(e)}")
            
            # Return empty TwiML response since we've sent all messages via API
            resp = MessagingResponse()
            return str(resp)
        else:
            # For short messages, send through TwiML
            resp = MessagingResponse()
            resp.message(legal_response)
            response_str = str(resp)
            logger.debug(f"Final response XML: {response_str}")
            return response_str
        
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        error_resp = MessagingResponse()
        error_resp.message("I apologize, but I'm having trouble processing your request. Please try again later.")
        return str(error_resp)

@app.route("/test-twilio", methods=["GET"])
async def test_twilio():
    """Test Twilio WhatsApp configuration."""
    try:
        # List available WhatsApp senders
        senders = twilio_client.messaging.v1.services.list(limit=20)
        whatsapp_numbers = []
        
        for service in senders:
            if 'whatsapp' in service.friendly_name.lower():
                whatsapp_numbers.append(service.friendly_name)
        
        return {
            "status": "success",
            "message": "Twilio client is working",
            "account_sid": twilio_client.account_sid,
            "whatsapp_services": whatsapp_numbers
        }
    except Exception as e:
        logger.error(f"Error testing Twilio: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    app.run(debug=True, port=5001) 