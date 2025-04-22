# Restaurant Underwriter AI

An AI-powered platform for analyzing restaurant risk and determining insurance eligibility based on sentiment analysis of reviews and business data.

## Features

- **Dynamic Data Collection**: Fetches real restaurant data from Yelp via Xano API and Google Images
- **Multiple Lookup Methods**: Find restaurants by business ID, name/address, or form ID
- **Sentiment Analysis**: Analyzes customer reviews to identify risk factors
- **Risk Assessment**: Evaluates business risk level based on underwriting guidelines
- **Comprehensive Reports**: Generates detailed underwriting reports with eligibility determination
- **LLM-Powered Agents**: Uses a multi-agent system for sophisticated analysis and decision-making

## Implementation Overview

The system consists of several interconnected modules:

1. **Data Collection**: Fetches restaurant reviews from Yelp and/or custom review forms via Xano
2. **Sentiment Analysis**: Analyzes review text to extract sentiment, keywords, and risk indicators
3. **Risk Assessment**: Evaluates the business against underwriting guidelines
4. **Report Generation**: Creates comprehensive underwriting reports

## Setup

1. Clone this repository
2. Install required dependencies
```
pip install -r requirements.txt
```
3. Create `.env` file (copy from `.env.example`) and add your API credentials
```
cp .env.example .env
```
4. Run the application
```
python app.py
```

## Agent Architecture

The system uses a multi-agent workflow for analysis:

- **Data Collector Agent**: Gathers and processes restaurant data
- **Sentiment Analyzer Agent**: Performs deep analysis of review content
- **Risk Assessor Agent**: Evaluates insurance risk and eligibility
- **Report Generator Agent**: Creates comprehensive reports
- **Underwriter Agent**: Coordinates the entire workflow and makes final decisions

## API Usage

### Yelp API via Xano

The system uses the Yelp API through Xano for restaurant reviews:

- **Endpoint**: `https://x0n1-tbv3-v8eo.n7.xano.io/api:ag2Iad7F/Yelp_review_by_name_address_and_biz_id`
- **Parameters**:
  - `type`: One of "biz_id", "business_name_and_address", or "phone_number"
  - `biz_id`: The Yelp Business ID (when using "biz_id" type)
  - `name` & `address`: Restaurant name and address (when using "business_name_and_address" type)
  - `ph_number`: Restaurant phone number (when using "phone_number" type)

### Custom Review API via Xano

For custom review forms:

- **Endpoint**: `https://x0n1-tbv3-v8eo.n7.xano.io/api:ag2Iad7F/reviews_by_formId`
- **Parameters**: `form_id`

### Google Images API via Xano

For fetching restaurant images:

- **Endpoint**: `https://x0n1-tbv3-v8eo.n7.xano.io/api:0LgARp2Y/place_image_by_insurance_request_form_id`
- **Parameters**: `id` (form ID)

## Usage

- **Web Interface**: Navigate to `/` for the main interface
- **Demo Mode**: Navigate to `/demo` for a quick demonstration
- **API Endpoint**: POST to `/api/analyze` with a JSON body containing one of:
  - `business_id` - Yelp Business ID for direct lookup
  - `form_id` - Form ID for Xano lookup
  - `restaurant_name` AND `restaurant_address` - Name and address for lookup by restaurant details

## Requirements

- Python 3.9+
- Flask
- NLTK
- Transformers
- LLM API access (OpenAI, Anthropic, or Azure OpenAI)

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.