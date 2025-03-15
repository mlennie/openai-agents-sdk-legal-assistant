from quart import Quart, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from openai.agents import Agent, Runner
from app.agents.legal_agent import legal_agent
import os
from dotenv import load_dotenv
import logging
import asyncio
import nest_asyncio

# Enable nested event loops
nest_asyncio.apply()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Quart(__name__)

async def get_legal_advice(query):
    """Get legal advice using OpenAI Agent."""
    try:
        logger.debug(f"Getting legal advice for query: {query}")
        result = await Runner.run(legal_agent, input=query)
        logger.debug(f"Received response: {result.final_output}")
        return result.final_output
    except Exception as e:
        logger.error(f"Error getting legal advice: {str(e)}")
        if "status code" in str(e).lower():
            return "I apologize, but I'm having trouble connecting to the service. Please try again in a few moments."
        return "I apologize, but I'm having trouble processing your request. Please try again later."

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle incoming WhatsApp messages."""
    logger.debug("Received webhook request")
    
    # Get the message from the request
    form = await request.form
    incoming_msg = form.get('Body', '').strip()
    logger.debug(f"Incoming message: {incoming_msg}")
    
    # Create Twilio response object
    resp = MessagingResponse()
    
    try:
        # Get legal information from OpenAI Agent
        logger.debug("Calling get_legal_advice")
        legal_response = await get_legal_advice(incoming_msg)
        logger.debug(f"Legal response received: {legal_response}")
        
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