from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from ..config import Config
import logging

logger = logging.getLogger(__name__)

class MessagingService:
    def __init__(self):
        """Initialize the messaging service with Twilio credentials."""
        self.client = Client(
            Config.TWILIO_ACCOUNT_SID,
            Config.TWILIO_AUTH_TOKEN
        )
        
    def create_response(self, message: str) -> MessagingResponse:
        """
        Create a TwiML response with the given message.
        
        Args:
            message: The message to send back to the user
            
        Returns:
            MessagingResponse: A TwiML response object
        """
        resp = MessagingResponse()
        resp.message(message)
        return resp
        
    async def send_message(self, to: str, body: str) -> None:
        """
        Send a message using Twilio.
        
        Args:
            to: The recipient's phone number
            body: The message content
        """
        try:
            message = self.client.messages.create(
                to=to,
                from_=Config.TWILIO_PHONE_NUMBER,
                body=body
            )
            logger.info(f"Message sent successfully. SID: {message.sid}")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise 