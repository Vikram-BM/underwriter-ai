import json
import logging
from autogen_flows.agents.agent_base import AgentBase
from autogen_flows.config.config import config
from modules.risk_assessor import RiskAssessor
from autogen_flows.utils import extract_json_from_response

logger = logging.getLogger(__name__)

class RiskAssessorAgent(AgentBase):
    """Agent responsible for assessing insurance risk based on sentiment analysis and business details"""
    
    def __init__(self):
        # Initialize with config from the config module
        super().__init__(
            name=config.agents.risk_assessor_agent_config["name"],
            description=config.agents.risk_assessor_agent_config["description"],
            system_message=config.agents.risk_assessor_agent_config["system_message"]
        )
        # Initialize the risk assessor module
        self.risk_assessor = RiskAssessor()
    
    def assess_basic_risk(self, sentiment_analysis, business_details):
        """
        Assess risk using the built-in risk assessor module
        
        Args:
            sentiment_analysis (dict): Overall sentiment analysis
            business_details (dict): Business details
        
        Returns:
            dict: Risk assessment results
        """
        return self.risk_assessor.assess_risk(sentiment_analysis, business_details)
    
    def determine_class_code(self, business_details):
        """
        Determine the insurance class code for the business
        
        Args:
            business_details (dict): Business details
        
        Returns:
            str: Insurance class code
        """
        return self.risk_assessor.determine_class_code(business_details)
    
    def advanced_risk_assessment(self, business_data, sentiment_analysis, deep_analysis, risk_factors):
        """
        Perform an advanced risk assessment using LLM and all available data
        
        Args:
            business_data (dict): Business details
            sentiment_analysis (dict): Overall sentiment analysis
            deep_analysis (dict): Deep analysis of reviews
            risk_factors (dict): Identified risk factors
        
        Returns:
            dict: Advanced risk assessment
        """
        # Handle the case where there's no business data
        if not business_data:
            logger.warning("No business data provided for risk assessment")
            return {
                "risk_level": "unknown",
                "class_code": "16910",  # Default to restaurant
                "eligibility": "NEEDS_REVIEW",
                "confidence": 0.5,
                "ineligible_criteria": [],
                "positive_factors": [],
                "negative_factors": ["Insufficient data for proper assessment"],
                "risk_rationale": "Unable to assess risk due to insufficient business data"
            }
            
        # First, get a preliminary class code using the direct method
        preliminary_class_code = self.determine_class_code(business_data)
        
        # Use the actual class code determination instead of randomization
        # Make an enhanced determination based on all available data
        logger.info("Making final class code determination based on all available data")
        
        # Check if we have enough sentiment data to refine our class code
        has_sentiment_data = deep_analysis and deep_analysis.get("common_themes")
        
        if has_sentiment_data:
            # If we have good sentiment data, use additional signals to refine class code
            common_themes = deep_analysis.get("common_themes", [])
            themes_text = " ".join(common_themes).lower()
            
            # Look for strong indicators in review themes
            bar_indicators = ["bar", "alcohol", "cocktail", "drinks", "beer", "wine"]
            nightclub_indicators = ["club", "dance", "dancing", "dj", "late night", "entertainment"]
            fast_food_indicators = ["fast", "quick", "counter", "takeout", "take-out", "drive"]
            
            # Check if any indicators are present in the themes
            if any(indicator in themes_text for indicator in nightclub_indicators) and "club" in themes_text:
                logger.info("Review themes strongly indicate nightclub")
                preliminary_class_code = "16912"  # Nightclub
            elif any(indicator in themes_text for indicator in bar_indicators) and \
                 len([i for i in bar_indicators if i in themes_text]) >= 2:
                logger.info("Review themes strongly indicate bar/tavern")
                preliminary_class_code = "16911"  # Bar
            elif any(indicator in themes_text for indicator in fast_food_indicators) and \
                 len([i for i in fast_food_indicators if i in themes_text]) >= 2:
                logger.info("Review themes strongly indicate fast food")
                preliminary_class_code = "16920"  # Fast food
        
        # Determine business type from class code
        business_type_map = {
            "16910": "Full-service Restaurant",
            "16911": "Bar/Tavern",
            "16912": "Nightclub",
            "16920": "Fast Food Restaurant"
        }
        preliminary_business_type = business_type_map.get(preliminary_class_code, "Restaurant")
        
        logger.info(f"Using preliminary class code {preliminary_class_code} - {preliminary_business_type}")
            
        # Format data for the prompt
        prompt = f"""
        Perform a comprehensive insurance risk assessment for this restaurant using all the available data.
        Apply standard underwriting guidelines for restaurant risks.
        
        GUIDELINES FOR DETERMINING ACCURATE CLASS CODE:
        - Class Code 16910: Full-service Restaurant - Table service, diverse menu, professional staff
        - Class Code 16911: Bar/Tavern - Primary focus on serving alcohol, limited food menu
        - Class Code 16912: Nightclub - Late night hours, entertainment focus, dancing, DJ or live music
        - Class Code 16920: Fast Food Restaurant - Counter service, limited menu, quick turnaround
        
        Based on initial analysis, this appears to be a {preliminary_business_type} (Class Code: {preliminary_class_code}).
        Carefully review to confirm or correct this classification.
        
        
        BUSINESS DETAILS:
        {json.dumps(business_data, indent=2)}
        
        SENTIMENT ANALYSIS:
        {json.dumps(sentiment_analysis, indent=2)}
        
        DEEP ANALYSIS:
        {json.dumps(deep_analysis, indent=2)}
        
        RISK FACTORS:
        {json.dumps(risk_factors, indent=2)}
        
        UNDERWRITING GUIDELINES:
        - Low risk restaurants have >70% positive reviews and <15% negative reviews
        - Medium risk restaurants have >50% positive reviews and <30% negative reviews
        - High risk restaurants have <30% positive reviews or >50% negative reviews
        - Critical negative keywords (unsafe, violation, hazard, dirty, bugs, etc.) indicate high risk
        - Fast food restaurants are considered ineligible per guidelines
        - Nightclubs with dancing are considered ineligible per guidelines
        - Restaurants with clear safety violations are ineligible
        
        Format your response as a JSON object with the following structure:
        {{
            "risk_level": "low/medium/high",
            "class_code": "16910 for full-service restaurant, 16911 for bar/tavern, etc.",
            "eligibility": "ELIGIBLE/INELIGIBLE/NEEDS_REVIEW",
            "confidence": 0.XX,
            "ineligible_criteria": ["reason1", "reason2"] or [],
            "positive_factors": ["factor1", "factor2", ...],
            "negative_factors": ["factor1", "factor2", ...],
            "risk_rationale": "detailed explanation of the risk assessment"
        }}
        """
        
        response = self.generate_response(prompt, temperature=0.2)
        
        # Use improved JSON extraction
        result = extract_json_from_response(response)
        if result:
            return result
            
        logger.error(f"Failed to parse JSON response: {response}")
        # Fall back to the basic risk assessment
        basic_assessment = self.assess_basic_risk(sentiment_analysis, business_data)
        return {
            "risk_level": basic_assessment["risk_level"],
            "class_code": basic_assessment["class_code"],
            "eligibility": basic_assessment["eligibility"],
            "confidence": basic_assessment["confidence"],
            "ineligible_criteria": basic_assessment["ineligible_criteria"],
            "positive_factors": basic_assessment["positive_factors"],
            "negative_factors": basic_assessment["negative_factors"],
            "risk_rationale": "Based on standard risk assessment matrix"
        }
    
    def assess_coverage_recommendations(self, business_data, risk_assessment):
        """
        Generate coverage recommendations based on the risk assessment
        
        Args:
            business_data (dict): Business details
            risk_assessment (dict): Risk assessment results
        
        Returns:
            dict: Coverage recommendations
        """
        prompt = f"""
        Based on the risk assessment for this restaurant, provide specific insurance coverage recommendations.
        
        BUSINESS DETAILS:
        {json.dumps(business_data, indent=2)}
        
        RISK ASSESSMENT:
        {json.dumps(risk_assessment, indent=2)}
        
        Consider standard coverages for restaurants including:
        - General Liability
        - Property Insurance
        - Business Interruption
        - Workers' Compensation
        - Liquor Liability (if applicable)
        - Food Contamination
        - Equipment Breakdown
        
        For each recommended coverage, suggest appropriate limits and any special conditions 
        based on the specific risk factors identified.
        
        Format your response as a JSON object with the following structure:
        {{
            "recommended_coverages": [
                {{
                    "coverage_type": "name of coverage",
                    "recommended_limits": "suggested limits",
                    "justification": "why this coverage is recommended at these limits",
                    "special_conditions": "any special terms or conditions"
                }},
                // more coverages...
            ],
            "premium_considerations": "factors that might impact premium calculation",
            "exclusions_to_consider": ["exclusion1", "exclusion2", ...]
        }}
        """
        
        response = self.generate_response(prompt, temperature=0.3)
        
        # Use improved JSON extraction
        result = extract_json_from_response(response)
        if result:
            return result
            
        logger.error(f"Failed to parse JSON response: {response}")
        # Return a simplified coverage recommendation
        return {
            "recommended_coverages": [
                {
                    "coverage_type": "General Liability",
                    "recommended_limits": "Based on standard restaurant guidelines",
                    "justification": "Standard coverage for all restaurants",
                    "special_conditions": "None"
                }
            ],
            "premium_considerations": "Standard factors apply",
            "exclusions_to_consider": []
        }
    
    def generate_risk_assessment(self, business_data, sentiment_results):
        """
        Generate a complete risk assessment
        
        Args:
            business_data (dict): Business details
            sentiment_results (dict): Sentiment analysis results
        
        Returns:
            dict: Complete risk assessment
        """
        # Extract the components from sentiment results
        overall_sentiment = sentiment_results.get("overall_sentiment", {})
        deep_analysis = sentiment_results.get("deep_analysis", {})
        risk_factors = sentiment_results.get("risk_factors", {})
        
        # Get business details
        business_details = business_data.get("business_details", {})
        
        # Perform basic risk assessment with the module
        basic_assessment = self.assess_basic_risk(overall_sentiment, business_details)
        
        # Perform advanced risk assessment with LLM
        advanced_assessment = self.advanced_risk_assessment(
            business_details, overall_sentiment, deep_analysis, risk_factors
        )
        
        # Generate coverage recommendations
        coverage_recommendations = self.assess_coverage_recommendations(
            business_details, advanced_assessment
        )
        
        # Combine all assessments into a comprehensive result
        return {
            "basic_assessment": basic_assessment,
            "advanced_assessment": advanced_assessment,
            "coverage_recommendations": coverage_recommendations
        }