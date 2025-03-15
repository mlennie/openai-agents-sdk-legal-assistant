from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ConversationContext:
    phone_number: str
    current_agent: Optional[str] = None
    conversation_history: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    last_interaction: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_interaction = datetime.utcnow()

    def get_recent_history(self, limit: int = 5) -> List[Dict]:
        """Get the most recent messages from the conversation history."""
        return self.conversation_history[-limit:] if self.conversation_history else []

    def set_current_agent(self, agent_name: str):
        """Update the current agent handling the conversation."""
        self.current_agent = agent_name

    def update_metadata(self, new_metadata: Dict):
        """Update conversation metadata."""
        self.metadata.update(new_metadata) 