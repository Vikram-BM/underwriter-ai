# Restaurant Research Tool for Insurance Underwriting

This tool automatically researches restaurants online and generates comprehensive reports for insurance underwriters. It fetches data from multiple sources including Google, Yelp, and Instagram to provide insights into the restaurant's reputation, appearance, and potential risk factors.

## Features

- Searches for restaurant information using SERP API
- Extracts relevant links using LLM analysis
- Gathers Yelp reviews using SerpApi's Yelp Reviews API (most reliable)
- Downloads Instagram content with intelligent fallbacks 
- Fetches Google Images of the restaurant with multiple backup methods
- Generates a comprehensive underwriting report

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example` with your API keys:
   - OPENAI_API_KEY: Get from [OpenAI](https://platform.openai.com/) - Required for LLM analysis
   - SERP_API_KEY: Get from [SERP API](https://serpapi.com/) - Required for Google search and Yelp reviews
   - FIRECRAWL_API_KEY: Get from [FireCrawl](https://firecrawl.io/) - Optional, used as a fallback for Yelp scraping

## Usage

Run the script with a restaurant name:

```bash
python restaurant_research.py "Restaurant Name"
```

Optionally, provide a location for more targeted results:

```bash
python restaurant_research.py "Restaurant Name" --location "City, State"
```

### Additional Options

```bash
# Run in quiet mode with minimal output
python restaurant_research.py "Restaurant Name" --quiet

# Skip specific data collection components
python restaurant_research.py "Restaurant Name" --skip-instagram
python restaurant_research.py "Restaurant Name" --skip-yelp
python restaurant_research.py "Restaurant Name" --skip-images
```

## Output

The script creates a folder in `scratch/{restaurant_name}` with:

- **underwriting_report.md**: Comprehensive report for underwriters
- **research_summary.txt**: Brief summary of all collected information
- **relevant_links.json**: All relevant links found
- **yelp/**: Yelp reviews and data
- **instagram/**: Instagram profile info and photos
- **images/**: Google images of the restaurant
- **error_log.txt**: Log of any errors encountered during research

## Error Handling

The script is designed to be robust to failures:
- If one component fails, the script will continue with other components
- All errors are logged to error_log.txt
- The script will create reports with whatever data it successfully collected

## Requirements

- Python 3.7+
- Internet connection
- API keys for OpenAI, SERP API, and FireCrawl

## Implementation Details

- Uses asyncio for concurrent execution of different research tasks
- Implements timeouts and retries for web requests
- Gracefully handles API failures and rate limits
- Outputs well-structured data in both machine-readable (JSON) and human-readable (Markdown/TXT) formats