from agents import Agent
from .legal_agent import create_legal_agent
from .research_agent import create_research_agent
from .contract_agent import create_contract_agent
import logging
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)

def create_triage_agent():
    """Create and configure the triage agent."""
    try:
        # Create sub-agents
        legal_agent = create_legal_agent()
        research_agent = create_research_agent()
        contract_agent = create_contract_agent()

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found")

        agent = Agent(
            name="Triage Agent",
            instructions="""You are a triage agent responsible for routing user queries to specialized legal agents. Your role is to:

1. Analyze user queries to determine the most appropriate specialized agent
2. Route queries to one of these agents:

   - Legal Agent: For general legal questions, interpretations, and advice
   - Research Agent: For legal research, updates on laws, and analysis of legal developments
   - Contract Agent: For contract creation, review, and modification

3. When routing to the Contract Agent, ensure you have collected:
   - Type of contract needed
   - Key terms to include
   - Specific requirements or conditions
   - Timeline expectations

Always maintain context across handoffs and ensure a smooth transition between agents.

Include this disclaimer with initial responses:
"DISCLAIMER: This service provides general guidance and should not be considered formal legal advice. For specific legal matters, please consult with a licensed attorney."
""",
            model="gpt-4o",
            handoffs=[legal_agent, research_agent, contract_agent]
        )

        logger.info("Triage agent created successfully")
        return agent

    except Exception as e:
        logger.error(f"Error creating triage agent: {str(e)}")
        raise
