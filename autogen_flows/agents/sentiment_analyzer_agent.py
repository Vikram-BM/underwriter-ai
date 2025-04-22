import json
import logging
from autogen_flows.agents.agent_base import AgentBase
from autogen_flows.config.config import config
from modules.sentiment_analyzer import SentimentAnalyzer
from autogen_flows.utils import extract_json_from_response

logger = logging.getLogger(__name__)

class SentimentAnalyzerAgent(AgentBase):
    """Agent responsible for analyzing sentiment of restaurant reviews and images"""
    
    def __init__(self):
        # Initialize with config from the config module
        super().__init__(
            name=config.agents.sentiment_analyzer_agent_config["name"],
            description=config.agents.sentiment_analyzer_agent_config["description"],
            system_message=config.agents.sentiment_analyzer_agent_config["system_message"]
        )
        # Initialize the sentiment analyzer module
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def batch_analyze_reviews(self, reviews):
        """
        Analyze sentiment for a batch of reviews using the sentiment analyzer module
        
        Args:
            reviews (list): List of review dictionaries
        
        Returns:
            list: List of reviews with sentiment analysis added
        """
        return self.sentiment_analyzer.analyze_reviews(reviews)
    
    def analyze_images(self, image_analyses):
        """
        Analyze sentiment for image analyses
        
        Args:
            image_analyses (list): List of image analysis dictionaries
            
        Returns:
            list: List of image analyses with sentiment added
        """
        return self.sentiment_analyzer.analyze_image_results(image_analyses)
    
    def calculate_overall_sentiment(self, analyzed_reviews, analyzed_images=None):
        """
        Calculate overall sentiment metrics from analyzed reviews
        
        Args:
            analyzed_reviews (list): List of reviews with sentiment analysis
            analyzed_images (list, optional): List of images with sentiment analysis
        
        Returns:
            dict: Overall sentiment metrics
        """
        return self.sentiment_analyzer.get_overall_sentiment(analyzed_reviews, analyzed_images)
    
    def deep_analyze_review_content(self, reviews):
        """
        Perform a deep analysis of review content using LLM
        
        Args:
            reviews (list): List of review dictionaries
        
        Returns:
            dict: Deep analysis results
        """
        # If no reviews, return empty analysis
        if not reviews:
            return {
                "common_themes": [],
                "safety_issues": [],
                "customer_service": {"positive_mentions": [], "negative_mentions": []},
                "cleanliness": {"positive_mentions": [], "negative_mentions": []},
                "food_quality": {"positive_mentions": [], "negative_mentions": []},
                "management": {"positive_indicators": [], "negative_indicators": []},
                "overall_impression": "No reviews available for analysis"
            }
        
        logger.info(f"Performing deep analysis on {len(reviews)} reviews")
        
        # For large review sets, we need to be smart about which reviews we include
        # in our prompt to get good representative coverage
        review_sample = []
        
        # If we have many reviews, we need to sample intelligently
        if len(reviews) > 20:
            # Get a balanced sample of positive, negative, and neutral reviews
            positive_reviews = [r for r in reviews if r.get('rating', 3) >= 4]
            negative_reviews = [r for r in reviews if r.get('rating', 3) <= 2]
            neutral_reviews = [r for r in reviews if r.get('rating', 3) == 3]
            
            # Shuffle each category to increase randomness
            import random
            random.shuffle(positive_reviews)
            random.shuffle(negative_reviews)
            random.shuffle(neutral_reviews)
            
            # Take a balanced sample
            sample_size = min(15, len(reviews) // 3)
            review_sample.extend(positive_reviews[:sample_size])
            review_sample.extend(negative_reviews[:min(sample_size, len(negative_reviews))])
            review_sample.extend(neutral_reviews[:min(sample_size // 2, len(neutral_reviews))])
            
            # Ensure we don't exceed a reasonable sample size
            review_sample = review_sample[:20]
            
            logger.info(f"Using balanced sample of {len(review_sample)} reviews " +
                        f"({len(positive_reviews[:sample_size])} positive, " +
                        f"{len(negative_reviews[:min(sample_size, len(negative_reviews))])} negative, " +
                        f"{len(neutral_reviews[:min(sample_size // 2, len(neutral_reviews))])} neutral)")
        else:
            # For smaller sets, just use all reviews up to a limit
            review_sample = reviews[:min(20, len(reviews))]
            
        # Format the reviews for the prompt
        reviews_text = "\n\n".join([
            f"Review #{i+1} (Rating: {review.get('rating', 'N/A')}): {review.get('text', '')}"
            for i, review in enumerate(review_sample)
        ])
        
        # Add a summary of the full dataset
        overall_stats = self._get_review_summary_stats(reviews)
        
        # Add the stats to the prompt
        reviews_text = (f"REVIEW STATISTICS (Total Reviews: {len(reviews)}):\n" +
                        f"Average Rating: {overall_stats['average_rating']:.1f}/5\n" +
                        f"Rating Distribution: {overall_stats['rating_distribution']}\n" +
                        f"Positive Reviews: {overall_stats['positive_percentage']:.1f}%\n" +
                        f"Negative Reviews: {overall_stats['negative_percentage']:.1f}%\n" +
                        f"Neutral Reviews: {overall_stats['neutral_percentage']:.1f}%\n\n" +
                        f"SAMPLE OF REVIEWS (from {len(reviews)} total):\n" +
                        reviews_text)
        
        prompt = f"""
        Perform a deep analysis of the following restaurant reviews. Focus on:
        
        1. Common themes across reviews
        2. Specific mentions of safety or risk-related issues
        3. Customer service quality
        4. Cleanliness and maintenance
        5. Food quality and consistency
        6. Professional management indicators
        
        REVIEWS:
        {reviews_text}
        
        Format your response as a JSON object with the following structure:
        {{
            "common_themes": ["theme1", "theme2", ...],
            "safety_issues": ["issue1", "issue2", ...],
            "customer_service": {{
                "positive_mentions": ["mention1", "mention2", ...],
                "negative_mentions": ["mention1", "mention2", ...]
            }},
            "cleanliness": {{
                "positive_mentions": ["mention1", "mention2", ...],
                "negative_mentions": ["mention1", "mention2", ...]
            }},
            "food_quality": {{
                "positive_mentions": ["mention1", "mention2", ...],
                "negative_mentions": ["mention1", "mention2", ...]
            }},
            "management": {{
                "positive_indicators": ["indicator1", "indicator2", ...],
                "negative_indicators": ["indicator1", "indicator2", ...]
            }},
            "overall_impression": "brief summary of overall customer impression"
        }}
        """
        
        response = self.generate_response(prompt, temperature=0.2)
        
        # Use improved JSON extraction
        result = extract_json_from_response(response)
        if result:
            return result
            
        logger.error(f"Failed to parse JSON response: {response}")
        # Return a simplified version as fallback
        return {
            "common_themes": ["food quality", "service"],
            "safety_issues": [],
            "overall_impression": "Could not parse full analysis"
        }
    
    def analyze_image_content(self, image_analyses):
        """
        Perform a detailed analysis of image content using LLM
        
        Args:
            image_analyses (list): List of image analysis dictionaries
            
        Returns:
            dict: Deep image analysis results
        """
        # If no images, return empty analysis
        if not image_analyses:
            return {
                "physical_environment": [],
                "safety_indicators": {"positive": [], "negative": []},
                "cleanliness_observations": {"positive": [], "negative": []},
                "organization_observations": {"positive": [], "negative": []},
                "overall_impression": "No images available for analysis"
            }
            
        logger.info(f"Performing deep analysis on {len(image_analyses)} images")
        
        # Format the image analyses for the prompt
        images_text = "\n\n".join([
            f"Image #{i+1} Observations:\n" + 
            "\n".join([f"- {obs}" for obs in analysis.get('observations', [])]) + "\n" +
            f"Risk Factors: {', '.join(analysis.get('risk_factors', ['None noted']))}\n" +
            f"Positive Factors: {', '.join(analysis.get('positive_factors', ['None noted']))}"
            for i, analysis in enumerate(image_analyses)
        ])
        
        prompt = f"""
        Analyze the following observations from restaurant images. Focus on:
        
        1. Physical environment conditions
        2. Safety indicators
        3. Cleanliness observations
        4. Organization and professionalism
        
        IMAGE OBSERVATIONS:
        {images_text}
        
        Format your response as a JSON object with the following structure:
        {{
            "physical_environment": ["observation1", "observation2", ...],
            "safety_indicators": {{
                "positive": ["indicator1", "indicator2", ...],
                "negative": ["indicator1", "indicator2", ...]
            }},
            "cleanliness_observations": {{
                "positive": ["observation1", "observation2", ...],
                "negative": ["observation1", "observation2", ...]
            }},
            "organization_observations": {{
                "positive": ["observation1", "observation2", ...],
                "negative": ["observation1", "observation2", ...]
            }},
            "overall_impression": "brief summary of overall impression from the images"
        }}
        """
        
        response = self.generate_response(prompt, temperature=0.2)
        
        # Use improved JSON extraction
        result = extract_json_from_response(response)
        if result:
            return result
            
        logger.error(f"Failed to parse JSON response: {response}")
        # Return a simplified version as fallback
        return {
            "physical_environment": ["Restaurant interior"],
            "safety_indicators": {"positive": [], "negative": []},
            "cleanliness_observations": {"positive": [], "negative": []},
            "organization_observations": {"positive": [], "negative": []},
            "overall_impression": "Could not parse full image analysis"
        }
    
    def identify_risk_factors(self, reviews, analyzed_reviews, overall_sentiment, image_analyses=None):
        """
        Identify risk factors from the reviews, images, and sentiment analysis
        
        Args:
            reviews (list): List of original review dictionaries
            analyzed_reviews (list): List of reviews with sentiment analysis
            overall_sentiment (dict): Overall sentiment metrics
            image_analyses (list, optional): List of image analyses with sentiment
        
        Returns:
            dict: Identified risk factors
        """
        # If no reviews, return empty analysis
        if not reviews or not overall_sentiment:
            return {
                "high_risk_factors": [],
                "medium_risk_factors": [],
                "low_risk_factors": [],
                "risk_explanation": "No reviews available for risk factor analysis",
                "risk_sentiment_correlation": "No sentiment data available"
            }
        
        logger.info(f"Identifying risk factors from {len(reviews)} reviews and {len(image_analyses) if image_analyses else 0} images")
            
        # Format key data for the prompt
        neg_percentage = overall_sentiment.get('negative_percentage', 0)
        neg_keywords = overall_sentiment.get('negative_keyword_frequency', {})
        
        # For large review sets, be strategic about which reviews to include
        negative_reviews = []
        critical_reviews = []
        
        # Look for reviews with critical keywords first
        critical_keywords = ["violation", "hazard", "unsafe", "accident", "injury", "bug", 
                            "dirty", "unclean", "filthy", "sick", "ill", "food poisoning"]
        
        # First pass - find reviews with critical keywords
        for review in analyzed_reviews:
            # Check if this review contains critical negative keywords
            has_critical = any(kw in review.get('negative_keywords', []) for kw in critical_keywords)
            if has_critical:
                critical_reviews.append(review)
            elif review.get('sentiment_category') == 'negative':
                negative_reviews.append(review)
                
            # If we have enough critical reviews, stop searching
            if len(critical_reviews) >= 5:
                break
                
        # Prepare the review sample
        review_sample = []
        
        # First add critical reviews
        review_sample.extend(critical_reviews[:3])
        
        # Then add other negative reviews
        negative_remaining_slots = min(5 - len(review_sample), len(negative_reviews))
        if negative_remaining_slots > 0:
            # Sort negative reviews by most negative compound score
            negative_reviews.sort(key=lambda x: x.get('sentiment_scores', {}).get('compound', 0))
            review_sample.extend(negative_reviews[:negative_remaining_slots])
            
        # If we still have space, add a few positive/neutral reviews for balance
        if len(review_sample) < 5 and len(analyzed_reviews) > len(review_sample):
            other_reviews = [r for r in analyzed_reviews 
                            if r not in critical_reviews and r not in negative_reviews]
            
            import random
            random.shuffle(other_reviews)
            review_sample.extend(other_reviews[:5 - len(review_sample)])
            
        # Format for better prompt readability
        reviews_text = "No reviews available"
        if review_sample:
            reviews_text = "\n\n".join([
                f"Review #{i+1} (Rating: {review.get('rating', 'N/A')}, " +
                f"Sentiment: {review.get('sentiment_category', 'unknown')}): {review.get('text', '')}"
                for i, review in enumerate(review_sample)
            ])
            
        logger.info(f"Selected {len(review_sample)} reviews for risk factor analysis " +
                   f"({len(critical_reviews[:3])} critical, " +
                   f"{min(negative_remaining_slots, len(negative_reviews))} negative, " +
                   f"{max(0, 5 - len(critical_reviews[:3]) - min(negative_remaining_slots, len(negative_reviews)))} other)")
                   
        # Format image information if available
        images_text = ""
        if image_analyses and len(image_analyses) > 0:
            negative_images = [img for img in image_analyses if img.get('sentiment_category') == 'negative']
            
            # If we have negative images, use those first
            image_sample = negative_images[:2] if negative_images else []
            
            # Add other images if needed
            if len(image_sample) < min(3, len(image_analyses)):
                other_images = [img for img in image_analyses if img not in image_sample]
                image_sample.extend(other_images[:min(3, len(image_analyses)) - len(image_sample)])
            
            # Format image text
            images_text = "\n\nIMAGE OBSERVATIONS:\n" + "\n\n".join([
                f"Image #{i+1}:\n" +
                "\n".join([f"- {obs}" for obs in img.get('observations', [])]) +
                f"\nRisk Factors: {', '.join(img.get('risk_factors', ['None noted']))}"
                for i, img in enumerate(image_sample)
            ])
                   
        # Add overall metrics about all reviews
        reviews_text = (f"OVERALL METRICS (from {len(reviews)} total reviews):\n" +
                      f"Negative reviews: {neg_percentage:.1f}%\n" +
                      f"Negative keywords found: {', '.join(list(neg_keywords.keys())[:10])}\n\n" +
                      f"SAMPLE REVIEWS FOCUSING ON HIGHEST RISK INDICATORS:\n" +
                      reviews_text + 
                      images_text)
        
        prompt = f"""
        Based on the provided restaurant reviews, images, and sentiment analysis, identify specific risk factors that would be relevant for insurance underwriting.
        
        {reviews_text}
        
        Consider factors such as:
        1. Safety concerns
        2. Cleanliness issues
        3. Signs of poor management
        4. Staff training inadequacies
        5. Equipment maintenance issues
        6. Adherence to health codes and regulations
        
        Format your response as a JSON object with the following structure:
        {{
            "high_risk_factors": ["factor1", "factor2", ...],
            "medium_risk_factors": ["factor1", "factor2", ...],
            "low_risk_factors": ["factor1", "factor2", ...],
            "risk_explanation": "brief explanation of the key risk factors",
            "risk_sentiment_correlation": "explanation of how sentiment correlates with identified risks"
        }}
        """
        
        response = self.generate_response(prompt, temperature=0.3)
        
        # Use improved JSON extraction
        result = extract_json_from_response(response)
        if result:
            return result
            
        logger.error(f"Failed to parse JSON response: {response}")
        # Return a simplified version as fallback
        return {
            "high_risk_factors": [],
            "medium_risk_factors": [],
            "low_risk_factors": [],
            "risk_explanation": "Could not parse risk factors analysis"
        }
    
    def _get_review_summary_stats(self, reviews):
        """
        Calculate summary statistics for a set of reviews
        
        Args:
            reviews (list): List of review dictionaries
            
        Returns:
            dict: Summary statistics
        """
        if not reviews:
            return {
                "average_rating": 0,
                "rating_distribution": {},
                "positive_percentage": 0,
                "negative_percentage": 0,
                "neutral_percentage": 0
            }
            
        # Calculate average rating
        ratings = [r.get('rating', 3) for r in reviews]
        average_rating = sum(ratings) / len(ratings)
        
        # Calculate rating distribution
        rating_counts = {}
        for rating in ratings:
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
            
        # Format as percentages
        rating_distribution = {
            f"{rating}★": f"{count/len(reviews)*100:.1f}%" 
            for rating, count in rating_counts.items()
        }
        
        # Calculate sentiment percentages
        positive_count = sum(1 for r in reviews if r.get('rating', 3) >= 4)
        negative_count = sum(1 for r in reviews if r.get('rating', 3) <= 2)
        neutral_count = len(reviews) - positive_count - negative_count
        
        positive_percentage = (positive_count / len(reviews)) * 100
        negative_percentage = (negative_count / len(reviews)) * 100
        neutral_percentage = (neutral_count / len(reviews)) * 100
        
        return {
            "average_rating": average_rating,
            "rating_distribution": rating_distribution,
            "positive_percentage": positive_percentage,
            "negative_percentage": negative_percentage,
            "neutral_percentage": neutral_percentage
        }
    
    def analyze_restaurant_data(self, data):
        """
        Perform complete sentiment analysis on restaurant data including reviews and images
        
        Args:
            data (dict): Restaurant data with reviews and images
        
        Returns:
            dict: Complete sentiment analysis results
        """
        # Handle case where data is None or missing reviews
        if not data:
            data = {}
        
        reviews = data.get('reviews', [])
        image_analyses = data.get('image_analyses', [])
        
        # Log review and image count
        logger.info(f"Starting sentiment analysis on {len(reviews)} reviews and {len(image_analyses)} images")
        
        # Print the first few reviews for debugging
        if reviews:
            logger.info(f"Sample review: {reviews[0].get('text', '')[:150]}...")
        
        # Check if reviews is empty or None
        if not reviews:
            logger.warning("No reviews found in the data, returning empty sentiment analysis")
            return {
                "analyzed_reviews": [],
                "analyzed_images": [],
                "overall_sentiment": {
                    'total_reviews': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'positive_percentage': 0,
                    'negative_percentage': 0,
                    'neutral_percentage': 0,
                    'average_compound_score': 0,
                    'positive_keyword_frequency': {},
                    'negative_keyword_frequency': {}
                },
                "deep_analysis": {
                    "common_themes": [],
                    "safety_issues": [],
                    "overall_impression": "No reviews available for analysis"
                },
                "image_analysis": {
                    "physical_environment": [],
                    "overall_impression": "No images available for analysis"
                },
                "risk_factors": {
                    "high_risk_factors": [],
                    "medium_risk_factors": [],
                    "low_risk_factors": [],
                    "risk_explanation": "No reviews available for risk assessment"
                }
            }
        
        # Use the module for basic analysis
        analyzed_reviews = self.batch_analyze_reviews(reviews)
        analyzed_images = self.analyze_images(image_analyses) if image_analyses else []
        overall_sentiment = self.calculate_overall_sentiment(analyzed_reviews, analyzed_images)
        
        # Use LLM for deeper analysis
        deep_analysis = self.deep_analyze_review_content(reviews)
        image_analysis = self.analyze_image_content(image_analyses) if image_analyses else {
            "physical_environment": [],
            "overall_impression": "No images available for analysis"
        }
        
        risk_factors = self.identify_risk_factors(reviews, analyzed_reviews, overall_sentiment, analyzed_images)
        
        return {
            "analyzed_reviews": analyzed_reviews,
            "analyzed_images": analyzed_images,
            "overall_sentiment": overall_sentiment,
            "deep_analysis": deep_analysis,
            "image_analysis": image_analysis,
            "risk_factors": risk_factors
        }