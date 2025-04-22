import json
import logging
import re
from autogen_flows.agents.agent_base import AgentBase
from autogen_flows.config.config import config
from modules.data_collector import DataCollector
from autogen_flows.utils import extract_json_from_response

logger = logging.getLogger(__name__)

class DataCollectorAgent(AgentBase):
    """Agent responsible for collecting restaurant data from external APIs"""
    
    def __init__(self):
        # Initialize with config from the config module
        super().__init__(
            name=config.agents.data_collector_agent_config["name"],
            description=config.agents.data_collector_agent_config["description"],
            system_message=config.agents.data_collector_agent_config["system_message"]
        )
        # Initialize the data collector module
        self.data_collector = DataCollector()
    
    def get_restaurant_data(self, form_id=None, business_id=None):
        """
        Get complete restaurant data from the Xano API
        
        Args:
            form_id (str, optional): Form ID for Xano API. Defaults to None.
            business_id (str, optional): Yelp business ID. Defaults to None.
            
        Returns:
            dict: Complete restaurant data including reviews and images
        """
        if form_id:
            logger.info(f"Collecting restaurant data with form ID: {form_id}")
            return self.data_collector.get_xano_data(form_id=form_id)
        elif business_id:
            logger.info(f"Collecting restaurant data with business ID: {business_id}")
            return self.data_collector.get_xano_data(business_id=business_id)
        else:
            logger.warning("No form_id or business_id provided, using sample data")
            return self.data_collector.get_sample_data()
    
    def get_sample_data(self):
        """
        Get sample restaurant data for testing
        
        Returns:
            dict: Sample business data
        """
        logger.info("Using sample restaurant data")
        return self.data_collector.get_sample_data()
    
    def process_data(self, data_source, identifier=None, form_id=None, business_id=None):
        """
        Process data from the specified source
        
        Args:
            data_source (str): Source of data (xano, sample)
            identifier (str, optional): Form ID or Business ID. Defaults to None.
            form_id (str, optional): Alternative form ID param. Defaults to None.
            business_id (str, optional): Yelp business ID. Defaults to None.
        
        Returns:
            dict: Processed business data
        """
        # Use form_id if provided, otherwise use identifier
        form_id = form_id or identifier
        # Use business_id if explicitly provided
        business_id = business_id or None
        
        if data_source == "xano":
            if business_id:
                logger.info(f"Processing data using business ID: {business_id}")
                return self.get_restaurant_data(business_id=business_id)
            elif form_id:
                logger.info(f"Processing data using form ID: {form_id}")
                return self.get_restaurant_data(form_id=form_id)
            else:
                logger.warning("No identifier provided for Xano source")
                return self.get_sample_data()
        else:
            return self.get_sample_data()
    
    def analyze_data_completeness(self, data):
        """
        Analyze the completeness of collected data
        
        Args:
            data (dict): Restaurant data
        
        Returns:
            str: Analysis of data completeness
        """
        prompt = f"""
        Analyze the following restaurant data for completeness and quality.
        Identify any missing crucial information, and suggest what additional data might be needed for a thorough risk assessment.
        
        DATA:
        {json.dumps(data, indent=2)}
        
        Format your response as a structured assessment with clear recommendations.
        """
        
        return self.generate_response(prompt, temperature=0.2)
    
    def extract_key_business_info(self, data):
        """
        Extract key business information from the collected data
        
        Args:
            data (dict): Restaurant data
        
        Returns:
            dict: Key business information
        """
        # First, extract what we can directly from the data
        business_details = data.get("business_details", {})
        business_name = business_details.get("name", "Unknown")
        
        # Determine business type from categories
        business_type = "Restaurant"  # Default
        categories = business_details.get("categories", [])
        category_names = [cat.get("title", "").lower() for cat in categories]
        
        if any(cat in ["bar", "pub", "tavern", "brewery", "cocktail"] for cat in category_names):
            business_type = "Bar/Tavern"
        elif any(cat in ["nightclub", "lounge", "cabaret", "dance club"] for cat in category_names):
            business_type = "Nightclub"
        elif any(cat in ["fast food", "quick service", "fast casual", "drive-thru"] for cat in category_names):
            business_type = "Fast Food Restaurant"
        
        # Try to determine cuisine type from categories
        cuisine_type = "General"
        cuisine_categories = [
            cat.get("title") for cat in categories 
            if cat.get("title", "").lower() not in [
                "restaurants", "food", "bar", "nightclub", "establishment", 
                "fast food", "quick service", "pub"
            ]
        ]
        if cuisine_categories:
            cuisine_type = cuisine_categories[0]
        
        # Get location info
        location = business_details.get("location", {})
        address = f"{location.get('address1', '')}, {location.get('city', '')}, {location.get('state', '')} {location.get('zip_code', '')}"
        if address.strip() == ", , ":
            address = "Unknown"
        
        # Extract rating and review count
        rating = business_details.get("rating", 0)
        review_count = business_details.get("review_count", 0)
        
        # Create basic info object
        basic_info = {
            "business_name": business_name,
            "business_type": business_type,
            "cuisine_type": cuisine_type,
            "location": address,
            "rating": rating,
            "review_count": review_count,
            "years_in_operation": "Unknown",
            "additional_relevant_info": {}
        }
        
        # Now enhance with LLM if we have enough data
        if business_name != "Unknown" and len(json.dumps(data)) < 10000:  # Only if data isn't too large
            prompt = f"""
            Extract the key business information from the following restaurant data.
            Pay special attention to the business type categorization, which is crucial for insurance classification.
            
            Business types can include:
            - Full-service Restaurant (default)
            - Bar/Tavern (primary focus on alcohol)
            - Nightclub (late night, entertainment/dancing)
            - Fast Food Restaurant (counter service, limited menu)
            
            Focus on details relevant for insurance underwriting such as business type, location, size, years in operation, etc.
            
            DATA:
            {json.dumps(data, indent=2)}
            
            Format your response as a JSON object with the following structure:
            {{
                "business_name": "Name of the restaurant",
                "business_type": "{business_type}",
                "cuisine_type": "{cuisine_type}",
                "location": "{address}",
                "rating": {rating},
                "review_count": {review_count},
                "years_in_operation": "If available",
                "additional_relevant_info": {{
                    "alcohol_served": true/false,
                    "has_delivery": true/false,
                    "has_outdoor_seating": true/false
                }}
            }}
            
            IMPORTANT: Be very precise with the business_type classification as it affects insurance class codes.
            """
            
            response = self.generate_response(prompt, temperature=0.1)
            
            # Use our improved JSON extraction utility
            enhanced_info = extract_json_from_response(response)
            
            if enhanced_info:
                # Update our basic info with any enhanced data
                for key, value in enhanced_info.items():
                    if value and value != "Unknown" and value != "If available":
                        basic_info[key] = value
                
                return basic_info
            else:
                logger.error(f"Failed to parse JSON response: {response}")
                return basic_info
        
        return basic_info