import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask settings
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5001))
    
    # Twilio settings
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    
    # Agent settings
    DEFAULT_AGENT_LOCATION = {"type": "approximate", "city": "Mexico City"}
    
    # Tracing settings
    DISABLE_TRACING = os.getenv('DISABLE_TRACING', 'False').lower() == 'true' 