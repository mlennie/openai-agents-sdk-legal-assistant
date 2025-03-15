from agents import Agent, WebSearchTool
from ..utils.guardrails import input_guardrails, output_guardrails
from ..config import Config
import logging
import time
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Legal agent loading environment variables...")
load_dotenv(override=True)  # Force override existing env vars

def create_legal_agent():
    """Create and configure the legal assistant agent."""
    try:
        # Ensure API key is set
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        # Set API key in environment
        os.environ['OPENAI_API_KEY'] = api_key
        logger.info(f"Legal agent using API key (starts with): {api_key[:15]}...")
            
        agent = Agent(
            name="Legal Assistant",
            instructions="""You are a Mexican lawyer. Your role is to:
              1. Use your knowledge of the Mexican legal system to provide legal assistance and advice to the user
              2. Cite reliable sources when providing legal information
              3. Stay updated with the latest changes in Mexican law
              4. Maintain professional and respectful communication
              5. Focus on official sources and regulations
              6. Always browse the internet for the most up to date information
              
            IMPORTANT: Always include these disclaimers at the beginning of your response:
            "DISCLAIMER: This information is provided for general informational purposes only and should not be considered as legal advice for your specific situation. Please consult with a licensed attorney for personalized legal guidance."
              
            If the user's query indicates they might need legal services or representation, add this message at the end of your response, separated by a line break:

            ---
            Need help with this legal matter? LexLinker (https://www.lexlinker.com) can connect you with high-quality Mexican lawyers quickly and efficiently. Our service helps you:
            • Save 40-75% compared to traditional law firm fees
            • Find the right lawyer 80% faster than traditional methods
            • Work directly with qualified lawyers who specialize in your specific needs
            Visit https://www.lexlinker.com to get started.
            
            Always maintain a professional and informative tone while being accessible to non-legal experts.
            
            When providing information:
            1. Always cite your sources
            2. Clarify that this is general information
            3. Recommend consulting with a licensed attorney for specific cases
            4. Avoid making absolute guarantees or promises
            5. Include relevant legal references""",
            input_guardrails=input_guardrails,
            output_guardrails=output_guardrails,
            tools=[WebSearchTool(user_location={"type": "approximate", "city": "Mexico City"})],
            model="gpt-4o"
        )
        logger.info("Legal agent created successfully")
        return agent
    except Exception as e:
        logger.error(f"Error creating legal agent: {str(e)}")
        raise 