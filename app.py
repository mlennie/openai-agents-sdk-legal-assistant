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
    
    # Get the message from the request
    form = await request.form
    incoming_msg = form.get('Body', '').strip()
    logger.debug(f"Incoming message: {incoming_msg}")
    
    if not incoming_msg:
        logger.error("Empty message received")
        error_resp = MessagingResponse()
        error_resp.message("I apologize, but I didn't receive any message. Please try again with your question.")
        return str(error_resp)
    
    # Create Twilio response object
    resp = MessagingResponse()
    
    try:
        # Get legal information from OpenAI Agent
        logger.debug("Calling get_legal_advice")
        legal_response = await get_legal_advice(incoming_msg)
        logger.debug(f"Legal response received: {legal_response}")
        
        if not legal_response:
            raise ValueError("Empty response received from legal agent")
        
        # Add the response to the Twilio message
        resp.message(legal_response)
        logger.debug("Response message created successfully")
        
        return str(resp)
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        error_resp = MessagingResponse()
        error_resp.message("I apologize, but I'm having trouble processing your request. Please try again later.")
        return str(error_resp)

if __name__ == "__main__":
    app.run(debug=True, port=5001) 