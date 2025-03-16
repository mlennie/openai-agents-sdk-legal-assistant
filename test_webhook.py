import logging
import asyncio
from app.app import app, normalize_phone_number
from app.db.mongo_store import store
from werkzeug.datastructures import MultiDict

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_webhook():
    try:
        # Test messages
        phone_number = "whatsapp:+14155238886"
        test_messages = [
            "I need help with a rental agreement",
            "It's for a 2-bedroom apartment in San Francisco",
            "The lease term would be 12 months"
        ]
        
        logger.info("Testing webhook with multiple messages...")
        
        # Clear any existing data
        store.clear_conversation(normalize_phone_number(phone_number))
        logger.info("Cleared existing conversation")
        
        # Create test request context
        async with app.test_client() as client:
            # Send messages in sequence
            for message in test_messages:
                logger.info(f"Sending message: {message}")
                form_data = MultiDict([
                    ('From', phone_number),
                    ('Body', message)
                ])
                response = await client.post("/webhook", form=form_data)
                logger.info(f"Webhook response status: {response.status_code}")
                logger.info(f"Webhook response: {await response.get_data()}")
                
                # Get conversation history after each message
                history = store.get_conversation_history(normalize_phone_number(phone_number))
                logger.info(f"Current conversation history ({len(history)} messages):")
                for msg in history:
                    logger.info(f"- {msg['role']}: {msg['content']}")
                logger.info("---")
            
            # Clean up
            store.clear_conversation(normalize_phone_number(phone_number))
            logger.info("Cleaned up test data")
            
            logger.info("All tests passed!")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_webhook()) 