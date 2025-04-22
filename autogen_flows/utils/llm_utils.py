import os
import requests
import json
import logging
from autogen_flows.config.config import config

logger = logging.getLogger(__name__)

def get_llm_client():
    """
    Get the appropriate LLM client based on configuration
    """
    if config.llm.provider == "openai":
        if not config.llm.openai_api_key:
            logger.warning("OpenAI API key not found. Using a mock LLM client.")
            return MockLLMClient()
        try:
            import openai
            client = openai.OpenAI(api_key=config.llm.openai_api_key)
            return OpenAIClient(client)
        except ImportError:
            logger.error("openai package not installed.")
            return MockLLMClient()
    
    elif config.llm.provider == "azure":
        if not config.llm.azure_api_key or not config.llm.azure_endpoint:
            logger.warning("Azure OpenAI credentials not found. Using a mock LLM client.")
            return MockLLMClient()
        try:
            import openai
            client = openai.AzureOpenAI(
                api_key=config.llm.azure_api_key,
                api_version="2023-05-15",
                azure_endpoint=config.llm.azure_endpoint
            )
            return AzureOpenAIClient(client, config.llm.azure_deployment)
        except ImportError:
            logger.error("openai package not installed.")
            return MockLLMClient()
    
    elif config.llm.provider == "anthropic":
        if not config.llm.anthropic_api_key:
            logger.warning("Anthropic API key not found. Using a mock LLM client.")
            return MockLLMClient()
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=config.llm.anthropic_api_key)
            return AnthropicClient(client)
        except ImportError:
            logger.error("anthropic package not installed.")
            return MockLLMClient()
    
    else:
        logger.warning(f"Unknown LLM provider: {config.llm.provider}. Using a mock LLM client.")
        return MockLLMClient()

class LLMClient:
    """Base LLM client interface"""
    def chat_completion(self, messages, **kwargs):
        """Send a chat completion request to the LLM"""
        raise NotImplementedError("Subclasses must implement this method")

class OpenAIClient(LLMClient):
    """OpenAI client implementation"""
    def __init__(self, client):
        self.client = client
        self.model = config.llm.openai_model
    
    def chat_completion(self, messages, **kwargs):
        try:
            response = self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000)
            )
            return {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return {"content": f"Error: {str(e)}", "role": "assistant", "finish_reason": "error"}

class AzureOpenAIClient(LLMClient):
    """Azure OpenAI client implementation"""
    def __init__(self, client, deployment_name):
        self.client = client
        self.deployment_name = deployment_name
    
    def chat_completion(self, messages, **kwargs):
        try:
            response = self.client.chat.completions.create(
                deployment_id=self.deployment_name,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000)
            )
            return {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            logger.error(f"Error calling Azure OpenAI API: {str(e)}")
            return {"content": f"Error: {str(e)}", "role": "assistant", "finish_reason": "error"}

class AnthropicClient(LLMClient):
    """Anthropic client implementation"""
    def __init__(self, client):
        self.client = client
        self.model = config.llm.anthropic_model
    
    def chat_completion(self, messages, **kwargs):
        try:
            # Convert messages from OpenAI format to Anthropic format
            prompt = ""
            for message in messages:
                role = message["role"]
                content = message["content"]
                if role == "system":
                    # For system messages, we prefix the first user message
                    continue
                elif role == "user":
                    prompt += f"\n\nHuman: {content}"
                elif role == "assistant":
                    prompt += f"\n\nAssistant: {content}"
            
            # Add the final assistant prompt
            prompt += "\n\nAssistant:"
            
            response = self.client.completions.create(
                model=self.model,
                prompt=prompt,
                max_tokens_to_sample=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7)
            )
            
            return {
                "content": response.completion,
                "role": "assistant",
                "finish_reason": "stop"  # Anthropic doesn't provide this directly
            }
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            return {"content": f"Error: {str(e)}", "role": "assistant", "finish_reason": "error"}

class MockLLMClient(LLMClient):
    """Mock LLM client for testing purposes"""
    def chat_completion(self, messages, **kwargs):
        # Get the last user message
        last_message = "No user message found"
        for message in reversed(messages):
            if message["role"] == "user":
                last_message = message["content"]
                break
        
        return {
            "content": f"Mock LLM response for: {last_message[:50]}...",
            "role": "assistant",
            "finish_reason": "stop"
        }

def generate_response(messages, **kwargs):
    """
    Generate a response from an LLM using the configured client
    
    Args:
        messages (list): List of message dictionaries with 'role' and 'content'
        **kwargs: Additional arguments for the LLM API call
    
    Returns:
        str: The content of the LLM response
    """
    client = get_llm_client()
    response = client.chat_completion(messages, **kwargs)
    return response["content"]