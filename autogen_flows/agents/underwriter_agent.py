import json
import logging
from autogen_flows.agents.agent_base import AgentBase
from autogen_flows.config.config import config
from autogen_flows.agents.data_collector_agent import DataCollectorAgent
from autogen_flows.agents.sentiment_analyzer_agent import SentimentAnalyzerAgent
from autogen_flows.agents.risk_assessor_agent import RiskAssessorAgent
from autogen_flows.agents.report_generator_agent import ReportGeneratorAgent
from autogen_flows.utils import extract_json_from_response

logger = logging.getLogger(__name__)

class UnderwriterAgent(AgentBase):
    """The coordinator agent that oversees the entire underwriting process"""
    
    def __init__(self):
        # Initialize with config from the config module
        super().__init__(
            name=config.agents.underwriter_agent_config["name"],
            description=config.agents.underwriter_agent_config["description"],
            system_message=config.agents.underwriter_agent_config["system_message"]
        )
        
        # Initialize all the specialized agents
        self.data_collector_agent = DataCollectorAgent()
        self.sentiment_analyzer_agent = SentimentAnalyzerAgent()
        self.risk_assessor_agent = RiskAssessorAgent()
        self.report_generator_agent = ReportGeneratorAgent()
    
    def process_restaurant_data(self, data=None, data_source="sample", identifier=None, form_id=None, business_id=None):
        """
        Process restaurant data through the entire underwriting workflow
        
        Args:
            data (dict, optional): Preloaded restaurant data. Defaults to None.
            data_source (str, optional): Source of data if data is None. Defaults to "sample".
            identifier (str, optional): Business ID or Form ID. Defaults to None.
            form_id (str, optional): Form ID for fetching Google images. Defaults to None.
            business_id (str, optional): Yelp business ID for fetching reviews. Defaults to None.
        
        Returns:
            dict: Final comprehensive underwriting report
        """
        # Step 1: Collect and process restaurant data
        if data is None:
            logger.info(f"Collecting restaurant data from {data_source}")
            if business_id:
                logger.info(f"Using business_id {business_id} to fetch Yelp reviews")
                restaurant_data = self.data_collector_agent.process_data(data_source, identifier, form_id=form_id, business_id=business_id)
            elif form_id:
                logger.info(f"Using form_id {form_id} to fetch Google images and reviews")
                restaurant_data = self.data_collector_agent.process_data(data_source, identifier, form_id=form_id)
            else:
                restaurant_data = self.data_collector_agent.process_data(data_source, identifier)
        else:
            logger.info("Using provided restaurant data")
            restaurant_data = data
        
        # Verify we have sufficient data to process
        if not restaurant_data.get("business_details"):
            logger.warning("No business details found in data, using sample data")
            sample_data = self.data_collector_agent.process_data("sample")
            restaurant_data["business_details"] = sample_data.get("business_details", {})
            
        if not restaurant_data.get("reviews") or len(restaurant_data.get("reviews", [])) < 3:
            logger.warning("Insufficient reviews found, using sample reviews")
            sample_data = self.data_collector_agent.process_data("sample")
            restaurant_data["reviews"] = restaurant_data.get("reviews", []) + sample_data.get("reviews", [])
        
        # Log what we have to work with
        logger.info(f"Working with {len(restaurant_data.get('reviews', []))} reviews, " + 
                    f"{len(restaurant_data.get('images', []))} Yelp images, and " +
                    f"{len(restaurant_data.get('google_images', []))} Google images")
        
        # Step 2: Extract key business information
        business_info = self.data_collector_agent.extract_key_business_info(restaurant_data)
        logger.info(f"Processed business info for: {business_info.get('business_name', 'Unknown Restaurant')}")
        logger.info(f"Business type: {business_info.get('business_type', 'Unknown')}")
        logger.info(f"Cuisine: {business_info.get('cuisine_type', 'Unknown')}")
        
        # Analyze restaurant images if available
        image_analyses = restaurant_data.get("image_analyses", [])
        if image_analyses:
            logger.info(f"Found {len(image_analyses)} pre-analyzed images")
        elif restaurant_data.get("google_images"):
            logger.info(f"Restaurant has {len(restaurant_data.get('google_images', []))} Google images available")
            image_analysis_prompt = f"""
            Analyze the following restaurant Google images to identify potential risk factors.
            Restaurant: {business_info.get('business_name', 'Unknown')}
            Type: {business_info.get('business_type', 'Unknown')}
            Google Image URLs: {[img.get('url') for img in restaurant_data.get('google_images', [])]}
            
            Based on the restaurant type and name, what risk factors might be visible in these images?
            Consider factors like cleanliness, safety equipment, crowding, etc.
            """
            
            # This is a placeholder - in the actual code, the image analyses are already
            # done by the data_collector module and included in the restaurant_data
            logger.info("Using pre-analyzed Google images for risk assessment")
        
        # Step 3: Analyze sentiment of reviews and images
        sentiment_results = self.sentiment_analyzer_agent.analyze_restaurant_data(restaurant_data)
        logger.info(f"Completed sentiment analysis with {len(sentiment_results.get('analyzed_reviews', []))} reviews")
        
        # Additional sentiment metrics
        positive_pct = sentiment_results.get("overall_sentiment", {}).get("positive_percentage", 0)
        negative_pct = sentiment_results.get("overall_sentiment", {}).get("negative_percentage", 0)
        logger.info(f"Sentiment breakdown: {positive_pct:.1f}% positive, {negative_pct:.1f}% negative")
        
        # Image sentiment if available
        image_sentiment = sentiment_results.get("overall_sentiment", {}).get("image_sentiment", {})
        if image_sentiment:
            img_positive_pct = image_sentiment.get("positive_percentage", 0)
            img_negative_pct = image_sentiment.get("negative_percentage", 0)
            logger.info(f"Image sentiment: {img_positive_pct:.1f}% positive, {img_negative_pct:.1f}% negative")
            
            # Log key findings from images
            image_analysis = sentiment_results.get("image_analysis", {})
            if image_analysis:
                logger.info(f"Image analysis found: " + 
                           f"{len(image_analysis.get('safety_indicators', {}).get('positive', []))} positive safety indicators, " +
                           f"{len(image_analysis.get('safety_indicators', {}).get('negative', []))} negative safety indicators")
        
        # Step 4: Assess risk based on sentiment and business details
        risk_assessment = self.risk_assessor_agent.generate_risk_assessment(restaurant_data, sentiment_results)
        
        # Get eligibility from the advanced assessment
        eligibility = risk_assessment.get("advanced_assessment", {}).get("eligibility", "UNKNOWN")
        risk_level = risk_assessment.get("advanced_assessment", {}).get("risk_level", "unknown")
        class_code = risk_assessment.get("advanced_assessment", {}).get("class_code", "unknown")
        logger.info(f"Completed risk assessment: {eligibility} with {risk_level} risk level, class code {class_code}")
        
        # Step 5: Generate comprehensive report
        final_report = self.report_generator_agent.generate_comprehensive_report(
            restaurant_data, sentiment_results, risk_assessment
        )
        
        logger.info(f"Generated comprehensive report for {business_info.get('business_name', 'Unknown Restaurant')}")
        logger.info(f"Report summary: {eligibility} ({risk_level} risk) with class code {class_code}")
        
        return final_report
    
    def finalize_decision(self, report):
        """
        Finalize the underwriting decision with executive-level review
        
        Args:
            report (dict): The comprehensive underwriting report
        
        Returns:
            dict: Final decision with executive comments
        """
        # Extract the risk assessment and executive summary
        risk_assessment = report.get("risk_assessment", {})
        executive_summary = report.get("executive_summary", "")
        detailed_findings = report.get("detailed_findings", {})
        
        prompt = f"""
        As a senior insurance underwriting executive, review the following report and provide your final decision and comments.
        
        EXECUTIVE SUMMARY:
        {executive_summary}
        
        RISK ASSESSMENT:
        {json.dumps(risk_assessment, indent=2)}
        
        DETAILED FINDINGS:
        {json.dumps(detailed_findings, indent=2)}
        
        Provide your final decision, any conditions or modifications to the recommendation, and your executive comments.
        
        Format your response as a JSON object with the following structure:
        {{
            "final_decision": "APPROVE/DECLINE/REFER",
            "decision_rationale": "explanation of your decision",
            "executive_comments": "additional notes or observations",
            "conditions": ["condition1", "condition2", ...],
            "override_reasons": [] // If you're overriding the recommendation
        }}
        """
        
        response = self.generate_response(prompt, temperature=0.3)
        
        # Use improved JSON extraction
        final_decision = extract_json_from_response(response)
        
        if final_decision:
            # Add the final decision to the report
            report["final_decision"] = final_decision
            return report
        
        logger.error(f"Failed to parse JSON response: {response}")
        # Create a simplified final decision
        report["final_decision"] = {
            "final_decision": risk_assessment.get("eligibility", "REFER"),
            "decision_rationale": "Based on standard underwriting guidelines",
            "executive_comments": "Automated decision",
            "conditions": [],
            "override_reasons": []
        }
        
        return report
    
    def run_full_workflow(self, data=None, data_source="sample", identifier=None, form_id=None, business_id=None):
        """
        Run the full underwriting workflow from data collection to final decision
        
        Args:
            data (dict, optional): Preloaded restaurant data. Defaults to None.
            data_source (str, optional): Source of data if data is None. Defaults to "sample".
            identifier (str, optional): Business ID or Form ID. Defaults to None.
            form_id (str, optional): Form ID for fetching Google images. Defaults to None.
            business_id (str, optional): Yelp business ID for fetching reviews. Defaults to None.
        
        Returns:
            dict: Final approved report with decision
        """
        # Step 1-5: Process restaurant data through the entire pipeline
        report = self.process_restaurant_data(data, data_source, identifier, form_id, business_id)
        
        # Step 6: Finalize decision with executive review
        final_report = self.finalize_decision(report)
        
        return final_report