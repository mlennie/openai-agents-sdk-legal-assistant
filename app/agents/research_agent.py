from agents import Agent, WebSearchTool
from ..utils.guardrails import input_guardrails, output_guardrails
import logging
import os

logger = logging.getLogger(__name__)

def create_research_agent():
    """Create and configure the research assistant agent."""
    try:
        agent = Agent(
            name="Research Assistant",
            instructions="""You are a research assistant specializing in Mexican law and regulations. Your role is to:
              1. Search and gather information from reliable sources
              2. Stay updated with the latest changes in Mexican law
              3. Provide detailed citations and references
              4. Focus on official sources and regulations
              5. Always browse the internet for the most up to date information
              
            IMPORTANT: Always include these disclaimers at the beginning of your response:
            "DISCLAIMER: This information is provided for general informational purposes only and should not be considered as legal advice for your specific situation. Please consult with a licensed attorney for personalized legal guidance."
              
            When providing information:
            1. Always cite your sources with URLs
            2. Clarify that this is general information
            3. Include dates of your sources
            4. Organize information chronologically
            5. Highlight key changes and updates""",
            input_guardrails=input_guardrails,
            output_guardrails=output_guardrails,
            tools=[WebSearchTool(user_location={"type": "approximate", "city": "Mexico City"})],
            model="gpt-4"
        )
        logger.info("Research agent created successfully")
        return agent
    except Exception as e:
        logger.error(f"Error creating research agent: {str(e)}")
        raise 