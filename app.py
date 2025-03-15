from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from agents import Agent, Runner, WebSearchTool, guardrail
import os
from dotenv import load_dotenv
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=3)

# Define content moderation guardrail
content_filter = guardrail(
    name="Content Moderation",
    description="Ensure responses are professional, respectful, and free from inappropriate content",
    check="""
    Verify that the response:
    1. Contains no hate speech, discrimination, or bias
    2. Uses no profanity or offensive language
    3. Contains no violent or threatening content
    4. Maintains professional and respectful tone
    5. Focuses solely on legal advice and information
    """,
)

# Create a legal assistant agent
legal_agent = Agent(
    name="Legal Assistant",
    instructions="""You are a Mexican lawyer. Your role is to:
      1. Use your knowledge of the Mexican legal system to provide legal assistance and advice to the user
      2. Search the internet for current legal information, regulations, and updates when needed
      3. Cite reliable sources when providing legal information
      4. Stay updated with the latest changes in Mexican law
    
    Always maintain a professional and informative tone while being accessible to non-legal experts.
    When searching for information, focus on official government sources, legal databases, and reputable law firms.""",
    tools=[WebSearchTool(user_location={"type": "approximate", "city": "Mexico City"})],
    guardrails=[content_filter]
)

async def get_legal_advice(query):
    """Get legal advice using OpenAI Agent."""
    try:
        logger.debug(f"Getting legal advice for query: {query}")
        result = await Runner.run(legal_agent, input=query)
        logger.debug(f"Received response: {result.final_output}")
        return result.final_output
    except Exception as e:
        logger.error(f"Error getting legal advice: {str(e)}")
        return f"I apologize, but I'm having trouble processing your request. Please try again later. Error: {str(e)}"

def run_async(coro):
    """Run an async function in a new event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming WhatsApp messages."""
    logger.debug("Received webhook request")
    
    # Get the message from the request
    incoming_msg = request.values.get('Body', '').strip()
    logger.debug(f"Incoming message: {incoming_msg}")
    
    # Create Twilio response object
    resp = MessagingResponse()
    
    try:
        # Get legal information from OpenAI Agent using ThreadPoolExecutor
        logger.debug("Calling get_legal_advice")
        future = executor.submit(run_async, get_legal_advice(incoming_msg))
        legal_response = future.result()
        logger.debug(f"Legal response received: {legal_response}")
        
        # Combine disclaimer and response
        full_response = legal_response
        
        # Add the response to the Twilio message
        resp.message(full_response)
        logger.debug("Response message created successfully")
        
        return str(resp)
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return str(e), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000) 