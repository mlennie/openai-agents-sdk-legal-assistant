from agents import Agent
from ..utils.guardrails import input_guardrails, output_guardrails
from ..config import Config

def create_legal_agent():
    """Create and configure the legal assistant agent."""
    return Agent(
        name="Legal Assistant",
        instructions="""You are a Mexican lawyer. Your role is to:
          1. Use your knowledge of the Mexican legal system to provide legal assistance and advice to the user
          2. Cite reliable sources when providing legal information
          3. Stay updated with the latest changes in Mexican law
          4. Maintain professional and respectful communication
          5. Focus on official sources and regulations
        
        Always maintain a professional and informative tone while being accessible to non-legal experts.""",
        input_guardrails=input_guardrails,
        output_guardrails=output_guardrails,
        model="gpt-4"
    ) 