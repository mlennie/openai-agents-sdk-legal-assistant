import logging
from app.db.mongo_store import store

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mongo():
    try:
        # Test message
        phone_number = "+14155238886"
        test_message = "Test message from test script"
        
        logger.info("Testing MongoDB store...")
        
        # Clear any existing data
        store.clear_conversation(phone_number)
        logger.info("Cleared existing conversation")
        
        # Add a test message
        store.append_to_history(phone_number, "user", test_message)
        logger.info("Added test message")
        
        # Get conversation history
        history = store.get_conversation_history(phone_number)
        logger.info(f"Retrieved history: {history}")
        
        # Get full conversation data
        conversation = store.get_conversation(phone_number)
        logger.info(f"Retrieved conversation: {conversation}")
        
        # Clean up
        store.clear_conversation(phone_number)
        logger.info("Cleaned up test data")
        
        logger.info("All tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    test_mongo() 