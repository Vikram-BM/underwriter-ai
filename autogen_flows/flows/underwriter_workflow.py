import logging
from autogen_flows.agents.underwriter_agent import UnderwriterAgent

logger = logging.getLogger(__name__)

def run_underwriter_workflow(data=None, data_source="sample", identifier=None, form_id=None, business_id=None):
    """
    Run the complete restaurant underwriter workflow
    
    Args:
        data (dict, optional): Restaurant data to analyze. Defaults to None.
        data_source (str, optional): Source of data if data is None. Defaults to "sample".
        identifier (str, optional): Business ID or Form ID for API lookup. Defaults to None.
        form_id (str, optional): Form ID for fetching Google images. Defaults to None.
        business_id (str, optional): Yelp business ID for fetching reviews. Defaults to None.
    
    Returns:
        dict: Comprehensive underwriting report
    """
    logger.info("Initializing underwriter workflow")
    
    # Initialize the underwriter agent
    underwriter = UnderwriterAgent()
    
    # Run the full workflow
    try:
        final_report = underwriter.run_full_workflow(data, data_source, identifier, form_id, business_id)
        logger.info("Underwriter workflow completed successfully")
        return final_report
    except Exception as e:
        logger.error(f"Error in underwriter workflow: {str(e)}")
        raise e