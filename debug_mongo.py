import logging
from datetime import datetime, UTC
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_mongodb():
    try:
        logger.info("Connecting to MongoDB...")
        client = MongoClient('mongodb://localhost:27017/')
        
        # Test connection
        logger.info("Testing connection...")
        client.admin.command('ping')
        logger.info("Connection successful!")
        
        # Get database and collection
        logger.info("Accessing lexlinker database...")
        db = client.lexlinker
        conversations = db.conversations
        
        # Test data
        phone_number = "+14155238886"
        message = {
            "role": "user",
            "content": "Test message",
            "timestamp": datetime.now(UTC)
        }
        
        # Insert test data
        logger.info(f"Inserting test message for {phone_number}...")
        result = conversations.update_one(
            {"phone_number": phone_number},
            {
                "$push": {"conversation_history": message},
                "$set": {"last_updated": datetime.now(UTC)}
            },
            upsert=True
        )
        logger.info(f"Insert result - matched: {result.matched_count}, modified: {result.modified_count}, upserted: {result.upserted_id}")
        
        # Verify the data
        logger.info("Verifying stored data...")
        stored = conversations.find_one({"phone_number": phone_number})
        if stored:
            logger.info(f"Found document: {stored}")
            history = stored.get("conversation_history", [])
            logger.info(f"History length: {len(history)}")
            if history:
                logger.info(f"Last message: {history[-1]}")
        else:
            logger.error("No document found!")
        
        # List all documents
        logger.info("\nListing all documents:")
        all_docs = list(conversations.find())
        logger.info(f"Total documents: {len(all_docs)}")
        for doc in all_docs:
            logger.info(f"Document: {doc}")
        
        # Clean up
        logger.info("\nCleaning up test data...")
        result = conversations.delete_one({"phone_number": phone_number})
        logger.info(f"Deleted {result.deleted_count} document(s)")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        logger.info("Test complete")

if __name__ == "__main__":
    test_mongodb() 