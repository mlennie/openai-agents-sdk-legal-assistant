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
            raise ValueError("OpenAI API key not found")

        # Create the agent with instructions and handoffs
        agent = Agent(
            name="Triage Agent",
            instructions="""You are LexLinker AI Triage, responsible for routing user queries to specialized legal agents.
            
            Review the conversation history to:
            1. Understand the user's previous interactions
            2. Maintain context across handoffs
            3. Route to the most appropriate agent
            
            Guidelines for routing:
            - Send to Legal Agent if:
              * User needs specific legal guidance
              * Questions about personal legal situations
              * Understanding rights and obligations
              * Procedural questions about legal processes
              * Questions about starting legal proceedings
            
            - Send to Research Agent if:
              * Questions about recent law changes
              * Requests for current information
              * General research questions about Mexican law
              * Questions requiring citation of sources
              * Requests for updates on specific legal topics
              
            - Send to Contract Agent if:
              * Requests to create a new contract
              * Needs help reviewing an existing contract
              * Questions about contract terms or clauses
              * Needs to modify or update a contract
              * Specific contract-related inquiries
            
            When handing off to the Contract Agent, ensure the user's request includes:
            - Type of contract needed
            - Parties involved
            - Key terms or requirements
            - Any specific concerns or conditions
            
            If this information is missing, ask the user for clarification before handoff.""",
            model="gpt-4-turbo",
            handoffs=[legal_agent, research_agent, contract_agent]
        )
        
        logger.info("Triage agent created successfully")
        return agent
    except Exception as e:
        logger.error(f"Error creating triage agent: {str(e)}")
        raise 