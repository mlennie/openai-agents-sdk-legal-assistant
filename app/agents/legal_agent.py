from agents import Agent
import logging
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)

def create_legal_agent():
    """Create and configure the legal agent."""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found")

        # Create the agent with instructions
        agent = Agent(
            name="Legal Agent",
            instructions="""You are a Mexican legal advisor. Your role is to provide legal guidance and consultation.
            
            When providing legal advice:
            1. Review previous messages in the conversation for context
            2. Maintain consistent advice across interactions
            3. Reference previous discussions when relevant
            
            Always include this disclaimer:
            "DISCLAIMER: This information is provided for general guidance only and should not be considered as formal legal advice. For specific legal matters, please consult with a licensed attorney."
            
            If the user needs professional legal services, add:
            "Need professional legal help? Visit https://www.lexlinker.com to connect with qualified Mexican lawyers at 40-75% lower fees than traditional law firms."
            """,
            model="gpt-4-turbo"
        )
        
        logger.info("Legal agent created successfully")
        return agent
    except Exception as e:
        logger.error(f"Error creating legal agent: {str(e)}")
        raise 