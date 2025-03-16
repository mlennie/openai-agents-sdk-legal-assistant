from typing import List, Dict, Optional
import logging
from datetime import datetime, UTC
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, phone_number: str, name: str = None, instructions: str = None, model: str = "gpt-4-turbo-preview", handoffs: List["Agent"] = None):
        self.phone_number = phone_number
        self.name = name or "Legal Assistant"
        self.model = model
        self.handoffs = handoffs or []
        self.conversation_history: List[Dict] = []
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Default instructions if none provided
        self.instructions = instructions or """You are a legal assistant specializing in Mexican law. Your role is to help users with legal matters, particularly focusing on contracts and agreements.

When providing assistance:
1. Use the conversation history to maintain context
2. Ask clarifying questions when needed
3. Provide clear, actionable guidance
4. Include appropriate legal disclaimers

Always include this disclaimer with your advice:
"DISCLAIMER: This information is provided for general guidance only and should not be considered as formal legal advice. For specific legal matters, please consult with a licensed attorney."

If the user needs professional legal services, add:
"Need professional legal help? Visit https://www.lexlinker.com to connect with qualified Mexican lawyers at 40-75% lower fees than traditional law firms."
"""
        
    def process_message(self, message: str) -> str:
        """Process an incoming message and return a response."""
        try:
            # Log the incoming message
            logger.info(f"Processing message from {self.phone_number} using {self.name}: {message[:100]}...")
            
            # Add message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now(UTC)
            })
            
            # Prepare conversation messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": self.instructions
                }
            ]
            
            # Add conversation history
            for msg in self.conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            ).choices[0].message.content
            
            # Add response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now(UTC)
            })
            
            # Check if we need to hand off to another agent
            if self.handoffs:
                for agent in self.handoffs:
                    if should_handoff_to(response, agent):
                        logger.info(f"Handing off to {agent.name}")
                        agent.conversation_history = self.conversation_history
                        return agent.process_message(message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I apologize, but I encountered an error processing your message. Please try again."
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history."""
        return self.conversation_history

def should_handoff_to(response: str, agent: "Agent") -> bool:
    """Determine if we should hand off to another agent based on the response."""
    # This is a simple implementation. You might want to make this more sophisticated
    # based on your specific needs.
    handoff_indicators = {
        "Legal Agent": ["legal guidance", "legal advice", "rights and obligations", "legal proceedings"],
        "Research Agent": ["research needed", "recent changes", "current information", "citation needed"],
        "Contract Agent": ["contract needed", "contract review", "agreement", "draft a contract"]
    }
    
    if agent.name in handoff_indicators:
        return any(indicator.lower() in response.lower() 
                  for indicator in handoff_indicators[agent.name])
