import sqlite3
from datetime import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ConversationStore:
    def __init__(self):
        # Create db directory if it doesn't exist
        db_dir = Path(__file__).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_dir / "conversations.db"
        self._init_db()

    def _init_db(self):
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        phone_number TEXT PRIMARY KEY,
                        current_agent TEXT,
                        conversation_history TEXT,
                        last_updated TIMESTAMP,
                        metadata TEXT
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

    def get_conversation(self, phone_number: str) -> dict:
        """Retrieve conversation state for a phone number."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT current_agent, conversation_history, metadata FROM conversations WHERE phone_number = ?",
                    (phone_number,)
                )
                result = cursor.fetchone()
                
                if result:
                    return {
                        "current_agent": result[0],
                        "conversation_history": json.loads(result[1]),
                        "metadata": json.loads(result[2]) if result[2] else {}
                    }
                return {
                    "current_agent": None,
                    "conversation_history": [],
                    "metadata": {}
                }
        except Exception as e:
            logger.error(f"Error retrieving conversation: {str(e)}")
            raise

    def update_conversation(self, phone_number: str, current_agent: str = None, 
                          new_message: dict = None, metadata: dict = None):
        """Update conversation state for a phone number."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Get existing conversation
                cursor.execute(
                    "SELECT conversation_history, metadata FROM conversations WHERE phone_number = ?",
                    (phone_number,)
                )
                result = cursor.fetchone()
                
                # Initialize or update conversation history
                if result:
                    history = json.loads(result[0])
                    existing_metadata = json.loads(result[1]) if result[1] else {}
                else:
                    history = []
                    existing_metadata = {}
                
                # Add new message if provided
                if new_message:
                    history.append({
                        **new_message,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Update metadata if provided
                if metadata:
                    existing_metadata.update(metadata)
                
                # Update or insert conversation
                cursor.execute("""
                    INSERT OR REPLACE INTO conversations 
                    (phone_number, current_agent, conversation_history, metadata, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    phone_number,
                    current_agent,
                    json.dumps(history),
                    json.dumps(existing_metadata),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
                logger.debug(f"Updated conversation for {phone_number}")
        except Exception as e:
            logger.error(f"Error updating conversation: {str(e)}")
            raise

    def clear_conversation(self, phone_number: str):
        """Clear conversation history for a phone number."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversations WHERE phone_number = ?", (phone_number,))
                conn.commit()
                logger.info(f"Cleared conversation for {phone_number}")
        except Exception as e:
            logger.error(f"Error clearing conversation: {str(e)}")
            raise 