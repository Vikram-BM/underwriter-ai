import os
import json
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
class LLMConfig:
    def __init__(self):
        # Default to OpenAI if no specific provider is set
        self.provider = os.getenv("LLM_PROVIDER", "openai")
        
        # OpenAI configs
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Azure OpenAI configs
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        
        # Anthropic configs
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-2")

# Agent Configuration
class AgentConfig:
    def __init__(self):
        self.data_collector_agent_config = {
            "name": "DataCollectorAgent",
            "description": "Agent responsible for collecting restaurant data from external APIs",
            "system_message": "You are a data collection specialist. Your job is to gather and organize restaurant data from various sources like Yelp and Xano APIs."
        }
        
        self.sentiment_analyzer_agent_config = {
            "name": "SentimentAnalyzerAgent",
            "description": "Agent responsible for analyzing sentiment of restaurant reviews",
            "system_message": "You are a sentiment analysis expert. Your job is to analyze restaurant reviews to determine sentiment, extract key themes, and identify potential risk factors."
        }
        
        self.risk_assessor_agent_config = {
            "name": "RiskAssessorAgent",
            "description": "Agent responsible for assessing insurance risk based on sentiment analysis and business details",
            "system_message": "You are an insurance risk assessment expert. Your job is to evaluate restaurant data and determine insurance eligibility and risk levels based on underwriting guidelines."
        }
        
        self.report_generator_agent_config = {
            "name": "ReportGeneratorAgent",
            "description": "Agent responsible for generating comprehensive underwriting reports",
            "system_message": "You are a report generation specialist. Your job is to create detailed, well-structured underwriting reports based on risk assessment data."
        }
        
        self.underwriter_agent_config = {
            "name": "UnderwriterAgent",
            "description": "The coordinator agent that oversees the entire underwriting process",
            "system_message": "You are an expert insurance underwriter specializing in restaurant risks. Your job is to coordinate the entire underwriting process and make final eligibility determinations based on all available data."
        }

# Underwriting Guidelines Configuration
class UnderwritingConfig:
    def __init__(self):
        self.risk_factors = {
            'sentiment': {
                'low_risk': {'positive_percentage': 70, 'negative_percentage': 15},
                'medium_risk': {'positive_percentage': 50, 'negative_percentage': 30},
                'high_risk': {'positive_percentage': 30, 'negative_percentage': 50}
            },
            'keywords': {
                'critical_negative': ['violation', 'hazard', 'unsafe', 'accident', 'injury', 'bugs', 
                                     'dirty', 'unsanitary', 'food poisoning', 'fire', 'health code']
            }
        }
        
        self.class_codes = {
            'restaurant': '16910',  # Full-service Restaurant
            'bar': '16911',         # Bar/Tavern
            'nightclub': '16912',   # Nightclub
            'fast_food': '16920'    # Fast Food Restaurant
        }
        
        self.ineligible_business_types = [
            'fast_food',
            'nightclub with dancing',
            'establishments with live entertainment',
            'restaurants with delivery as primary service'
        ]

# Create an all-in-one config object
class Config:
    def __init__(self):
        self.llm = LLMConfig()
        self.agents = AgentConfig()
        self.underwriting = UnderwritingConfig()
        
        # API Configuration
        self.apis = {
            "yelp": {
                "api_key": os.getenv('YELP_API_KEY', 'Qakrz-kwbsziJOy6mjmRiqsbv8b4a-XtlVoASMfm24YAd4oiSU1oBfKSXC-G6ju4yjwB0yDCCnoa_R4Emb3-QFTaBqgeDK_13vWU7cq-2zebRjVMg-WjlqFXUI1nZXYx'),
                "client_id": os.getenv('YELP_CLIENT_ID', 'TBgvEyrXS7brPqddXfncbw'),
                "base_url": "https://api.yelp.com/v3"
            },
            "xano": {
                "api_url": os.getenv('XANO_API_URL', 'https://x0n1-tbv3-v8eo.n7.xano.io/api:ag2Iad7F/reviews_by_formId')
            }
        }
        
        # Application Configuration
        self.app = {
            "debug": os.getenv('DEBUG', 'True').lower() in ('true', '1', 't'),
            "host": os.getenv('HOST', '0.0.0.0'),
            "port": int(os.getenv('PORT', 5000))
        }

# Create a singleton config instance
config = Config()