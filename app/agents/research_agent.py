from agents import Agent
import logging
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)

def create_research_agent():
    """Create and configure the research agent."""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found")

        # Create the agent with instructions
        agent = Agent(
            name="Research Agent",
            instructions="""You are a Mexican legal research specialist. Your role is to research and provide information about Mexican law.
            
            When conducting research:
            1. Review previous research in conversation history
            2. Build upon previous findings
            3. Maintain research continuity
            4. Track what has been covered and what needs more investigation
            
            Always include this disclaimer:
            "DISCLAIMER: This research information is provided for general reference only and may not reflect the most current legal developments. Please consult with a legal professional for up-to-date guidance."
            
            If the user needs professional legal research, add:
            "Need professional legal research? Visit https://www.lexlinker.com to connect with qualified Mexican lawyers who can provide thorough legal research at 40-75% lower fees than traditional firms."
            """,
            model="gpt-4-turbo"
        )
        
        logger.info("Research agent created successfully")
        return agent
    except Exception as e:
        logger.error(f"Error creating research agent: {str(e)}")
        raise 