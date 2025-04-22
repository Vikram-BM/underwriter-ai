from flask import Flask, render_template, request, jsonify
from modules.data_collector import DataCollector
from modules.sentiment_analyzer import SentimentAnalyzer
from modules.risk_assessor import RiskAssessor
from modules.report_generator import ReportGenerator
import os
import time
from dotenv import load_dotenv
import logging
from autogen_flows.flows import run_underwriter_workflow

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Initialize modules
data_collector = DataCollector()
sentiment_analyzer = SentimentAnalyzer()
risk_assessor = RiskAssessor()
report_generator = ReportGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # Get form data
    data_source = request.form.get('data_source', 'sample')
    form_id = request.form.get('form_id')
    business_id = request.form.get('business_id')
    restaurant_name = request.form.get('restaurant_name')
    restaurant_address = request.form.get('restaurant_address')
    
    # Check if we have sufficient parameters
    if data_source != 'sample' and not (form_id or business_id or (restaurant_name and restaurant_address)):
        return render_template('error.html', error="Either Form ID, Business ID, or Restaurant Name and Address are required"), 400
    
    try:
        # Determine which method to use to fetch data
        if business_id:
            logger.info(f"Fetching data from Yelp API with business ID: {business_id}")
            data = data_collector.get_xano_data(business_id=business_id)
        elif form_id:
            logger.info(f"Fetching data from Xano API with form ID: {form_id}")
            data = data_collector.get_xano_data(form_id=form_id)
        elif restaurant_name and restaurant_address:
            logger.info(f"Fetching data using restaurant name and address: {restaurant_name}, {restaurant_address}")
            # Create a temporary data structure to make a restaurant lookup
            yelp_data = data_collector.get_yelp_reviews(restaurant_name=restaurant_name, restaurant_address=restaurant_address)
            if yelp_data and "data" in yelp_data and yelp_data["data"] and len(yelp_data["data"]) > 0:
                business_id = yelp_data["data"][0].get("id", None)
                if business_id:
                    logger.info(f"Found business ID: {business_id}, fetching full details")
                    data = data_collector.get_xano_data(business_id=business_id)
                else:
                    logger.warning("No business ID found for the provided name and address")
                    data = data_collector.get_sample_data()
            else:
                logger.warning("Failed to find business with provided name and address")
                data = data_collector.get_sample_data()
        else:
            logger.info("Using sample data")
            data = data_collector.get_sample_data()
        
        # Log what we got
        if data:
            review_count = len(data.get('reviews', []))
            google_image_count = len(data.get('google_images', []))
            logger.info(f"Successfully fetched {review_count} reviews and {google_image_count} Google images for {data.get('business_details', {}).get('name', 'Unknown')}")
        else:
            logger.error("Failed to fetch data")
            return render_template('error.html', error="Failed to fetch data"), 500
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return render_template('error.html', error=f"Error fetching data: {str(e)}"), 500
    
    # Run the full analysis through our AutoGen workflow
    try:
        logger.info("Starting underwriter workflow with all collected data")
        # Pass appropriate identifiers to the workflow
        result = run_underwriter_workflow(
            data, 
            data_source="xano", 
            identifier=form_id or business_id,
            form_id=form_id,
            business_id=business_id
        )
        logger.info("Workflow completed successfully")
        
        # Add the data source to the report for transparency
        result["data_source"] = "xano"
        result["analysis_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        result["review_count"] = len(data.get('reviews', []))
        result["image_count"] = len(data.get('google_images', []))
        
        return render_template('report.html', report=result)
    except Exception as e:
        logger.error(f"Error in underwriter workflow: {str(e)}")
        # Fallback to our traditional flow if the AutoGen workflow fails
        try:
            logger.warning("Falling back to traditional flow due to error in underwriter workflow")
            # Make sure we're using sample data for the fallback to avoid further errors
            fallback_data = data_collector.get_sample_data()
            analyzed_reviews = sentiment_analyzer.analyze_reviews(fallback_data['reviews'])
            overall_sentiment = sentiment_analyzer.get_overall_sentiment(analyzed_reviews)
            risk_assessment = risk_assessor.assess_risk(overall_sentiment, fallback_data['business_details'])
            report = report_generator.generate_report(fallback_data['business_details'], overall_sentiment, risk_assessment)
            
            # Add a note that this is a fallback report
            report["fallback_report"] = True
            report["error_message"] = str(e)
            
            return render_template('report.html', report=report)
        except Exception as fallback_error:
            logger.error(f"Error in fallback flow: {str(fallback_error)}")
            return render_template('error.html', error="An error occurred during analysis. Please try again with different data."), 500

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    # Get JSON data
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Extract request parameters
    form_id = data.get('form_id')
    business_id = data.get('business_id')
    restaurant_name = data.get('restaurant_name') 
    restaurant_address = data.get('restaurant_address')
    
    try:
        # Determine which method to use to fetch data
        if business_id:
            # Fetch data using Yelp business ID
            logger.info(f"API: Fetching data with Yelp business ID: {business_id}")
            restaurant_data = data_collector.get_xano_data(business_id=business_id)
            if not restaurant_data:
                return jsonify({"error": "Failed to fetch data from Yelp API with business ID"}), 500
        elif form_id:
            # Fetch data from Xano API using form ID
            logger.info(f"API: Fetching data with form ID: {form_id}")
            restaurant_data = data_collector.get_xano_data(form_id=form_id)
            if not restaurant_data:
                return jsonify({"error": "Failed to fetch data from API with form ID"}), 500
        elif restaurant_name and restaurant_address:
            # Fetch data using restaurant name and address
            logger.info(f"API: Fetching data with restaurant name and address: {restaurant_name}, {restaurant_address}")
            # First lookup the business ID
            yelp_data = data_collector.get_yelp_reviews(restaurant_name=restaurant_name, restaurant_address=restaurant_address)
            if yelp_data and "data" in yelp_data and yelp_data["data"] and len(yelp_data["data"]) > 0:
                business_id = yelp_data["data"][0].get("id", None)
                if business_id:
                    logger.info(f"API: Found business ID: {business_id}, fetching full details")
                    restaurant_data = data_collector.get_xano_data(business_id=business_id)
                    if not restaurant_data:
                        return jsonify({"error": "Failed to fetch data for found business ID"}), 500
                else:
                    logger.warning("API: No business ID found for the provided name and address")
                    restaurant_data = data_collector.get_sample_data()
            else:
                logger.warning("API: Failed to find business with provided name and address")
                restaurant_data = data_collector.get_sample_data()
        else:
            # Use sample data
            logger.info("API: No identifiers provided, using sample data")
            restaurant_data = data_collector.get_sample_data()
    except Exception as e:
        logger.error(f"API: Error fetching data: {str(e)}")
        return jsonify({"error": f"Error fetching data: {str(e)}"}), 500
    
    # Check for required data fields
    if not restaurant_data.get('reviews'):
        logger.warning("API: No reviews found in data, using sample data instead")
        restaurant_data = data_collector.get_sample_data()
        
    if not restaurant_data.get('business_details'):
        logger.warning("API: No business details found in data, using sample data instead")
        restaurant_data = data_collector.get_sample_data()
    
    # Try to use the AutoGen workflow
    try:
        # Pass identifiers to workflow
        identifier = form_id or business_id
        logger.info(f"API: Running workflow with identifier: {identifier}")
        result = run_underwriter_workflow(
            restaurant_data, 
            data_source="xano", 
            identifier=identifier,
            form_id=form_id,
            business_id=business_id
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"API: Error in underwriter workflow: {str(e)}")
        # Fallback to our traditional flow
        try:
            fallback_data = data_collector.get_sample_data()
            analyzed_reviews = sentiment_analyzer.analyze_reviews(fallback_data['reviews'])
            overall_sentiment = sentiment_analyzer.get_overall_sentiment(analyzed_reviews)
            risk_assessment = risk_assessor.assess_risk(overall_sentiment, fallback_data['business_details'])
            report = report_generator.generate_report(fallback_data['business_details'], overall_sentiment, risk_assessment)
            return jsonify(report)
        except Exception as fallback_error:
            logger.error(f"API: Error in fallback flow: {str(fallback_error)}")
            return jsonify({"error": "An error occurred during analysis"}), 500

@app.route('/demo')
def demo():
    # Use sample data
    data = data_collector.get_sample_data()
    
    # Run through the AutoGen workflow for the demo as well
    try:
        result = run_underwriter_workflow(data)
        return render_template('report.html', report=result)
    except Exception as e:
        logger.error(f"Error in underwriter workflow: {str(e)}")
        # Fallback to traditional flow
        try:
            analyzed_reviews = sentiment_analyzer.analyze_reviews(data['reviews'])
            overall_sentiment = sentiment_analyzer.get_overall_sentiment(analyzed_reviews)
            risk_assessment = risk_assessor.assess_risk(overall_sentiment, data['business_details'])
            report = report_generator.generate_report(data['business_details'], overall_sentiment, risk_assessment)
            return render_template('report.html', report=report)
        except Exception as fallback_error:
            logger.error(f"Error in fallback flow: {str(fallback_error)}")
            return render_template('error.html', error="An error occurred during demo. Please try again."), 500

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "version": "1.2.0"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))