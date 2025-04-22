import logging
from autogen_flows.utils.llm_utils import generate_response

logger = logging.getLogger(__name__)

class AgentBase:
    """Base class for all agents in the system"""
    
    def __init__(self, name, description, system_message):
        """
        Initialize the agent
        
        Args:
            name (str): Agent name
            description (str): Brief description of agent's role
            system_message (str): System message for LLM
        """
        self.name = name
        self.description = description
        self.system_message = system_message
        self.conversation_history = []
    
    def add_message(self, role, content):
        """
        Add a message to the conversation history
        
        Args:
            role (str): Message role (system, user, assistant)
            content (str): Message content
        """
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def get_messages(self):
        """
        Get all messages in the conversation
        
        Returns:
            list: List of message dictionaries
        """
        # Always include the system message first
        return [{"role": "system", "content": self.system_message}] + self.conversation_history
    
    def generate_response(self, user_message, **kwargs):
        """
        Generate a response to a user message
        
        Args:
            user_message (str): User message to respond to
            **kwargs: Additional arguments for the LLM API call
        
        Returns:
            str: Agent's response
        """
        # Add user message to conversation
        self.add_message("user", user_message)
        
        # Get messages for LLM
        messages = self.get_messages()
        
        # Generate response
        response_content = generate_response(messages, **kwargs)
        
        # Add assistant response to conversation
        self.add_message("assistant", response_content)
        
        return response_content
    
    def reset_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []
    
    def __str__(self):
        return f"{self.name} - {self.description}"