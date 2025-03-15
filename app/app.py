from quart import Quart, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
import logging
from openai import OpenAI
from agents import Agent
from .agents.triage_agent import create_triage_agent
import redis
import json
import asyncio
import time
from agents.runner import Runner

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add a stream handler to print to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Initialize Redis for session storage
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True
    )
    # Test connection
    if not redis_client.ping():
        raise Exception("Redis ping test failed")
    logger.info("Successfully connected to Redis")
except Exception as e:
    logger.error(f"Failed to initialize Redis client: {str(e)}")
    raise

HISTORY_LIMIT = 20  # Keep last 20 messages

# Initialize app and Twilio client
app = Quart(__name__)
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

# Initialize triage agent
triage_agent = create_triage_agent()

def normalize_phone_number(phone_number: str) -> str:
    """Normalize phone number by removing 'whatsapp:' prefix."""
    return phone_number.replace('whatsapp:', '')

def get_conversation_history(phone_number: str) -> list:
    """Retrieve conversation history from Redis."""
    normalized_number = normalize_phone_number(phone_number)
    history_key = f"history:{normalized_number}"
    try:
        # Get raw history from Redis
        raw_history = redis_client.lrange(history_key, 0, -1)
        history = []
        
        logger.info(f"=== REDIS RETRIEVAL ===")
        logger.info(f"Phone: {normalized_number}")
        logger.info(f"Raw history length: {len(raw_history)}")
        
        for msg_str in raw_history:
            try:
                msg = json.loads(msg_str)
                # Only include messages with valid role and content
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    if msg['role'] in ['user', 'assistant']:
                        # Only keep the essential fields for the conversation
                        history.append({
                            'role': msg['role'],
                            'content': msg['content']
                        })
                        logger.info(f"Added message - Role: {msg['role']}")
                        logger.info(f"Content: {msg['content'][:100]}..." if len(msg['content']) > 100 else f"Content: {msg['content']}")
            except json.JSONDecodeError:
                logger.error(f"Invalid message format in history: {msg_str}")
                continue
        
        logger.info(f"Processed history length: {len(history)}")
        logger.info(f"==================")
        return history
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        return []

def update_conversation_history(phone_number: str, role: str, content: str):
    """Update conversation history in Redis."""
    if role not in ['user', 'assistant']:
        logger.error(f"Invalid role: {role}")
        return
        
    normalized_number = normalize_phone_number(phone_number)
    history_key = f"history:{normalized_number}"
    try:
        # Create message with only essential fields
        message = json.dumps({
            'role': role,
            'content': content
        })
        
        print(f"\n=== REDIS UPDATE ATTEMPT ===")
        print(f"Key: {history_key}")
        print(f"Message: {message}")
        print(f"Role: {role}")
        print(f"Content length: {len(content)}")
        
        # Test Redis connection
        try:
            ping_result = redis_client.ping()
            print(f"Redis ping test: {ping_result}")
            if not ping_result:
                raise Exception("Redis ping returned False")
        except Exception as e:
            print(f"Redis ping failed: {str(e)}")
            logger.error(f"Redis ping failed: {str(e)}")
            raise
        
        # Add message to history
        try:
            result = redis_client.rpush(history_key, message)
            print(f"Redis rpush result: {result}")
            if not result:
                raise Exception("Redis rpush returned 0 or False")
        except Exception as e:
            print(f"Redis rpush failed: {str(e)}")
            logger.error(f"Redis rpush failed: {str(e)}")
            raise
        
        # Verify the message was stored
        try:
            stored_messages = redis_client.lrange(history_key, -1, -1)
            print(f"Last stored message: {stored_messages}")
            if not stored_messages:
                error_msg = "Message was not stored!"
                print(f"Warning: {error_msg}")
                logger.error(error_msg)
                raise Exception(error_msg)
            elif stored_messages[0] != message:
                error_msg = f"Stored message doesn't match! Expected: {message}, Got: {stored_messages[0]}"
                print(f"Warning: {error_msg}")
                logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            print(f"Redis verification failed: {str(e)}")
            logger.error(f"Redis verification failed: {str(e)}")
            raise
        
        # Get current length
        try:
            current_length = redis_client.llen(history_key)
            print(f"Current length after push: {current_length}")
            if current_length <= 0:
                error_msg = "List length is 0 or negative after push!"
                print(f"Warning: {error_msg}")
                logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            print(f"Redis llen failed: {str(e)}")
            logger.error(f"Redis llen failed: {str(e)}")
            raise
        
        if current_length > HISTORY_LIMIT:
            try:
                redis_client.ltrim(history_key, current_length - HISTORY_LIMIT, -1)
                print(f"Trimmed to last {HISTORY_LIMIT} messages")
                # Verify trim worked
                new_length = redis_client.llen(history_key)
                if new_length > HISTORY_LIMIT:
                    error_msg = f"Trim failed! Length is still {new_length}"
                    print(f"Warning: {error_msg}")
                    logger.error(error_msg)
            except Exception as e:
                print(f"Redis trim failed: {str(e)}")
                logger.error(f"Redis trim failed: {str(e)}")
                raise
            
        print("=== REDIS UPDATE COMPLETE ===\n")
            
        logger.info(f"=== REDIS UPDATE ===")
        logger.info(f"Phone: {normalized_number}")
        logger.info(f"Added message - Role: {role}")
        logger.info(f"Content: {content[:100]}..." if len(content) > 100 else f"Content: {content}")
        logger.info(f"Current history length: {current_length}")
        logger.info(f"===================")
    except Exception as e:
        error_msg = f"Error updating conversation history: {str(e)}"
        logger.error(error_msg)
        print(f"=== REDIS UPDATE FAILED ===")
        print(f"Error: {error_msg}")
        print("===================\n")
        raise

def clear_conversation_history(phone_number: str):
    """Clear conversation history for a phone number."""
    normalized_number = normalize_phone_number(phone_number)
    history_key = f"history:{normalized_number}"
    try:
        redis_client.delete(history_key)
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")

async def get_agent_response(phone_number: str, message: str) -> str:
    """Get response from agent using conversation history."""
    try:
        # Store the current user message in history first
        update_conversation_history(phone_number, "user", message)
        
        # Get conversation history
        conversation_history = get_conversation_history(phone_number)
        print("**** CONVERSATION HISTORY ****")
        print(json.dumps(conversation_history, indent=2))
        print("**** END CONVERSATION HISTORY ****")
        
        logger.debug(f"Retrieved conversation history for {phone_number}: {conversation_history}")
        
        # Add system message at the start of history
        full_history = [
            {
                "role": "system",
                "content": "You are LexLinker AI, a Mexican legal assistant. Review the conversation history to maintain context and provide consistent advice."
            }
        ]
        full_history.extend(conversation_history)
        
        # Use Runner.run_sync with the full conversation history
        result = await Runner.run(
            triage_agent,
            messages=full_history
        )
        
        if not result or not hasattr(result, 'final_output'):
            raise ValueError("Invalid response from agent")
            
        # Add agent response to history
        update_conversation_history(phone_number, "assistant", result.final_output)
        
        return result.final_output
            
    except Exception as e:
        logger.error(f"Error getting agent response: {str(e)}")
        return "I apologize, but I encountered an error. Please try again later."

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle incoming WhatsApp messages."""
    try:
        # Get message details
        form = await request.form
        message_body = form["Body"]
        from_number = form["From"]
        
        logger.info(f"Received message from {from_number}: {message_body[:100]}...")
        
        # Get agent response
        response = await get_agent_response(from_number, message_body)
        logger.info(f"Agent response length: {len(response)}")
        
        # Handle long responses
        if len(response) > 1500:
            parts = [response[i:i+1500] for i in range(0, len(response), 1500)]
            total_parts = len(parts)
            logger.info(f"Splitting response into {total_parts} parts")
            
            # Send parts in reverse order so they appear in correct order in WhatsApp
            for i in range(total_parts - 1, -1, -1):
                try:
                    suffix = f"\n(Part {i+1}/{total_parts})" if total_parts > 1 else ""
                    twilio_client.messages.create(
                        body=parts[i] + suffix,
                        from_='whatsapp:+14155238886',
                        to=from_number
                    )
                    logger.debug(f"Sent part {i+1} of {total_parts}")
                    # Add a small delay between messages to maintain order
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error sending message part {i+1}: {str(e)}")
            
            # Return empty TwiML response since we've sent all messages via API
            resp = MessagingResponse()
            return str(resp)
        else:
            # For short messages, send through TwiML
            resp = MessagingResponse()
            resp.message(response)
            logger.debug("Sent short response through TwiML")
            return str(resp)
            
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return "Error processing request", 500

@app.route("/clear_conversation", methods=["POST"])
async def clear_conversation():
    """Clear conversation history for a phone number."""
    try:
        form = await request.form
        phone_number = form["phone_number"]
        clear_conversation_history(phone_number)
        return {"status": "success", "message": f"Conversation cleared for {phone_number}"}
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

@app.route("/debug/conversation/<phone_number>", methods=["GET"])
async def debug_conversation(phone_number: str):
    """Debug endpoint to view raw Redis data and processed conversation history."""
    try:
        normalized_number = normalize_phone_number(phone_number)
        history_key = f"history:{normalized_number}"
        
        # Get raw Redis data
        raw_data = redis_client.lrange(history_key, 0, -1)
        raw_messages = []
        for msg_str in raw_data:
            try:
                msg = json.loads(msg_str)
                raw_messages.append(msg)
            except json.JSONDecodeError:
                raw_messages.append({"error": "Invalid JSON", "raw": msg_str})
        
        # Get processed conversation history
        processed_history = get_conversation_history(phone_number)
        
        # Get Redis key info
        key_length = redis_client.llen(history_key)
        
        return {
            "phone_number": phone_number,
            "key": history_key,
            "list_length": key_length,
            "raw_data": raw_messages,
            "processed_history": processed_history
        }
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return {
            "error": str(e),
            "phone_number": phone_number
        }, 500

if __name__ == "__main__":
    app.run(debug=True, port=5001) 