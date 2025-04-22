import json
import logging
from autogen_flows.agents.agent_base import AgentBase
from autogen_flows.config.config import config
from modules.report_generator import ReportGenerator
from autogen_flows.utils import extract_json_from_response

logger = logging.getLogger(__name__)

class ReportGeneratorAgent(AgentBase):
    """Agent responsible for generating comprehensive underwriting reports"""
    
    def __init__(self):
        # Initialize with config from the config module
        super().__init__(
            name=config.agents.report_generator_agent_config["name"],
            description=config.agents.report_generator_agent_config["description"],
            system_message=config.agents.report_generator_agent_config["system_message"]
        )
        # Initialize the report generator module
        self.report_generator = ReportGenerator()
    
    def generate_basic_report(self, business_details, sentiment_analysis, risk_assessment):
        """
        Generate a basic report using the built-in report generator module
        
        Args:
            business_details (dict): Business details
            sentiment_analysis (dict): Overall sentiment analysis
            risk_assessment (dict): Risk assessment
        
        Returns:
            dict: Basic report
        """
        return self.report_generator.generate_report(business_details, sentiment_analysis, risk_assessment)
    
    def generate_executive_summary(self, business_data, sentiment_results, risk_assessment):
        """
        Generate an executive summary of the underwriting analysis
        
        Args:
            business_data (dict): Business details
            sentiment_results (dict): Sentiment analysis results
            risk_assessment (dict): Risk assessment results
        
        Returns:
            str: Executive summary
        """
        # Extract key information for the summary
        business_name = business_data.get("business_details", {}).get("name", "Unknown Restaurant")
        risk_level = risk_assessment.get("advanced_assessment", {}).get("risk_level", "unknown")
        eligibility = risk_assessment.get("advanced_assessment", {}).get("eligibility", "UNKNOWN")
        
        prompt = f"""
        Create a concise executive summary of the underwriting analysis for {business_name}.
        
        BUSINESS DATA:
        {json.dumps(business_data.get("business_details", {}), indent=2)}
        
        SENTIMENT HIGHLIGHTS:
        {json.dumps(sentiment_results.get("overall_sentiment", {}), indent=2)}
        
        RISK ASSESSMENT:
        {json.dumps(risk_assessment.get("advanced_assessment", {}), indent=2)}
        
        The executive summary should:
        1. Clearly state the final eligibility determination
        2. Summarize the key risk factors that led to this determination
        3. Provide a high-level overview of the sentiment analysis
        4. Include any notable coverage considerations
        
        Keep the summary concise (3-5 paragraphs) but comprehensive enough for an underwriting executive to understand the decision.
        """
        
        return self.generate_response(prompt, temperature=0.3)
    
    def generate_detailed_findings(self, business_data, sentiment_results, risk_assessment):
        """
        Generate detailed findings for the report
        
        Args:
            business_data (dict): Business details
            sentiment_results (dict): Sentiment analysis results
            risk_assessment (dict): Risk assessment results
        
        Returns:
            dict: Detailed findings
        """
        # Extract class code information for emphasis
        class_code = "Unknown"
        business_type = "Unknown"
        
        if risk_assessment and "advanced_assessment" in risk_assessment:
            class_code = risk_assessment["advanced_assessment"].get("class_code", "Unknown")
            
            # Map class code to business type
            class_code_map = {
                "16910": "Full-service Restaurant",
                "16911": "Bar/Tavern",
                "16912": "Nightclub",
                "16920": "Fast Food Restaurant"
            }
            business_type = class_code_map.get(class_code, "Unknown Establishment Type")
        
        prompt = f"""
        Generate detailed findings for an insurance underwriting report for this restaurant.
        
        BUSINESS DATA:
        {json.dumps(business_data.get("business_details", {}), indent=2)}
        
        SENTIMENT ANALYSIS:
        {json.dumps(sentiment_results, indent=2)}
        
        RISK ASSESSMENT:
        {json.dumps(risk_assessment, indent=2)}
        
        CLASS CODE DETERMINATION:
        Based on the assessment, this business has been classified as a {business_type} (Class Code: {class_code}).
        
        For each of the following sections, provide detailed, evidence-based findings:
        
        1. Business Classification and Profile Analysis (include explicit verification of the assigned class code and business type)
        2. Customer Sentiment Analysis
        3. Safety and Risk Concerns
        4. Management Quality Assessment
        5. Compliance With Regulations
        
        Format your response as a JSON object with the following structure:
        {{
            "business_profile_analysis": "detailed findings",
            "customer_sentiment_analysis": "detailed findings",
            "safety_risk_concerns": "detailed findings",
            "management_quality_assessment": "detailed findings",
            "compliance_assessment": "detailed findings"
        }}
        """
        
        response = self.generate_response(prompt, temperature=0.3)
        
        # Use improved JSON extraction
        result = extract_json_from_response(response)
        if result:
            return result
            
        logger.error(f"Failed to parse JSON response: {response}")
        # Return a simplified findings
        return {
            "business_profile_analysis": "Could not parse detailed findings",
            "customer_sentiment_analysis": "Could not parse detailed findings",
            "safety_risk_concerns": "Could not parse detailed findings",
            "management_quality_assessment": "Could not parse detailed findings",
            "compliance_assessment": "Could not parse detailed findings"
        }
    
    def generate_comprehensive_report(self, business_data, sentiment_results, risk_assessment):
        """
        Generate a comprehensive underwriting report
        
        Args:
            business_data (dict): Business details
            sentiment_results (dict): Sentiment analysis results
            risk_assessment (dict): Risk assessment results
        
        Returns:
            dict: Comprehensive report
        """
        # Generate basic report from module
        business_details = business_data.get("business_details", {})
        overall_sentiment = sentiment_results.get("overall_sentiment", {})
        basic_risk = risk_assessment.get("basic_assessment", {})
        
        basic_report = self.generate_basic_report(business_details, overall_sentiment, basic_risk)
        
        # Generate executive summary
        executive_summary = self.generate_executive_summary(
            business_data, sentiment_results, risk_assessment
        )
        
        # Generate detailed findings
        detailed_findings = self.generate_detailed_findings(
            business_data, sentiment_results, risk_assessment
        )
        
        # Extract advanced risk assessment and coverage recommendations
        advanced_assessment = risk_assessment.get("advanced_assessment", {})
        coverage_recommendations = risk_assessment.get("coverage_recommendations", {})
        
        # Combine everything into a comprehensive report
        return {
            # Basic business info
            "business_info": basic_report["business_info"],
            
            # Assessment results
            "executive_summary": executive_summary,
            "sentiment_analysis": {
                **basic_report["sentiment_analysis"],
                "deep_analysis": sentiment_results.get("deep_analysis", {})
            },
            "risk_assessment": {
                **basic_report["risk_assessment"],
                "risk_rationale": advanced_assessment.get("risk_rationale", "")
            },
            
            # Detailed findings
            "detailed_findings": detailed_findings,
            
            # Coverage and recommendation
            "coverage_recommendations": coverage_recommendations,
            "recommendation": basic_report["recommendation"],
            
            # Metadata
            "analysis_date": "2025-04-08",  # This would be dynamic in a real system
            "version": "1.0.0"
        }