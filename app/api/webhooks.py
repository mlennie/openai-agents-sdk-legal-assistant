from flask import Blueprint, request
from agents import Runner
from ..agents.legal_agent import create_legal_agent
from ..services.messaging import MessagingService
import logging

logger = logging.getLogger(__name__)
webhook_bp = Blueprint('webhooks', __name__)
messaging_service = MessagingService()

@webhook_bp.route("/webhook", methods=["POST"])
async def webhook():
    """Handle incoming WhatsApp messages."""
    logger.debug("Received webhook request")
    
    # Get the message from the request
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    logger.debug(f"Incoming message from {from_number}: {incoming_msg}")
    
    try:
        # Get legal information from OpenAI Agent
        logger.debug("Creating legal agent")
        legal_agent = create_legal_agent()
        
        logger.debug("Running agent with input")
        result = await Runner.run(legal_agent, input=incoming_msg)
        logger.debug(f"Agent response received: {result.final_output}")
        
        # Create and return the response
        resp = messaging_service.create_response(result.final_output)
        logger.debug("Response message created successfully")
        
        return str(resp)
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        error_resp = messaging_service.create_response(
            "I apologize, but I'm having trouble processing your request. Please try again later."
        )
        return str(error_resp) 