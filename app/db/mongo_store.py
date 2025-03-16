import json
import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

logger = logging.getLogger(__name__)

class MongoStore:
    def __init__(self):
        logger.info("Initializing MongoDB store...")
        try:
            self.client = MongoClient('mongodb://localhost:27017/')
            self.db: Database = self.client.lexlinker
            self.conversations: Collection = self.db.conversations
            self._ensure_indexes()
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB store: {e}")
            raise

    def _ensure_indexes(self):
        """Create necessary indexes for efficient querying"""
        try:
            logger.info("Creating MongoDB indexes...")
            self.conversations.create_index("phone_number", unique=True)
            self.conversations.create_index("last_updated")
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")
            raise

    def get_conversation(self, phone_number: str) -> Dict:
        """Get conversation data for a phone number"""
        try:
            logger.info(f"Getting conversation data for {phone_number}")
            result = self.conversations.find_one({"phone_number": phone_number})
            if result:
                logger.info(f"Found conversation data for {phone_number}")
                return {
                    "current_agent": result.get("current_agent"),
                    "conversation_history": result.get("conversation_history", []),
                    "metadata": result.get("metadata", {})
                }
            logger.info(f"No conversation data found for {phone_number}")
            return {
                "current_agent": None,
                "conversation_history": [],
                "metadata": {}
            }
        except Exception as e:
            logger.error(f"Error getting conversation data for {phone_number}: {e}")
            raise

    def get_conversation_history(self, phone_number: str) -> List[Dict]:
        """Get conversation history for a phone number"""
        try:
            logger.info(f"Getting conversation history for {phone_number}")
            result = self.conversations.find_one(
                {"phone_number": phone_number},
                {"conversation_history": 1}
            )
            history = result.get("conversation_history", []) if result else []
            logger.info(f"Retrieved {len(history)} messages for {phone_number}")
            return history
        except Exception as e:
            logger.error(f"Error getting conversation history for {phone_number}: {e}")
            raise

    def update_conversation(
        self,
        phone_number: str,
        current_agent: Optional[str] = None,
        conversation_history: Optional[List] = None,
        metadata: Optional[Dict] = None
    ):
        """Update conversation data"""
        try:
            logger.info(f"Updating conversation data for {phone_number}")
            update_data = {"last_updated": datetime.now(UTC)}
            
            if current_agent is not None:
                update_data["current_agent"] = current_agent
            if conversation_history is not None:
                update_data["conversation_history"] = conversation_history
            if metadata is not None:
                update_data["metadata"] = metadata

            result = self.conversations.update_one(
                {"phone_number": phone_number},
                {
                    "$set": update_data
                },
                upsert=True
            )
            logger.info(f"Updated conversation data for {phone_number}: matched={result.matched_count}, modified={result.modified_count}, upserted={result.upserted_id is not None}")
        except Exception as e:
            logger.error(f"Error updating conversation data for {phone_number}: {e}")
            raise

    def append_to_history(self, phone_number: str, role: str, content: str):
        """Append a new message to the conversation history"""
        try:
            logger.info(f"Appending message to history for {phone_number}")
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now(UTC)
            }
            
            result = self.conversations.update_one(
                {"phone_number": phone_number},
                {
                    "$push": {"conversation_history": message},
                    "$set": {"last_updated": datetime.now(UTC)}
                },
                upsert=True
            )
            logger.info(f"Appended message to history for {phone_number}: matched={result.matched_count}, modified={result.modified_count}, upserted={result.upserted_id is not None}")
            
            # Verify the message was stored
            stored = self.conversations.find_one({"phone_number": phone_number})
            if not stored or "conversation_history" not in stored:
                error_msg = f"Failed to store message for {phone_number}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            history = stored["conversation_history"]
            if not history or history[-1]["content"] != content:
                error_msg = f"Stored message doesn't match for {phone_number}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info(f"Successfully verified message storage for {phone_number}")
        except Exception as e:
            logger.error(f"Error appending message to history for {phone_number}: {e}")
            raise

    def clear_conversation(self, phone_number: str):
        """Clear conversation data for a phone number"""
        try:
            logger.info(f"Clearing conversation data for {phone_number}")
            result = self.conversations.delete_one({"phone_number": phone_number})
            logger.info(f"Cleared conversation data for {phone_number}: deleted={result.deleted_count}")
        except Exception as e:
            logger.error(f"Error clearing conversation data for {phone_number}: {e}")
            raise

    def reset_db(self):
        """Reset the entire database by dropping all collections and recreating indexes"""
        try:
            logger.info("Resetting MongoDB database...")
            # Drop all collections
            for collection in self.db.list_collection_names():
                self.db.drop_collection(collection)
                logger.info(f"Dropped collection: {collection}")
            
            # Recreate collections and indexes
            self._ensure_indexes()
            logger.info("Successfully reset MongoDB database")
        except Exception as e:
            logger.error(f"Error resetting MongoDB database: {e}")
            raise

# Global instance
store = MongoStore() 