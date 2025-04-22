import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re

# Download NLTK resources
nltk.download('vader_lexicon', quiet=True)

class SentimentAnalyzer:
    def __init__(self):
        self.sid = SentimentIntensityAnalyzer()
        
        # Expanded keywords to look for in reviews
        self.positive_indicators = [
            'professional', 'clean', 'safety', 'maintained', 'trained',
            'spotless', 'excellent', 'organized', 'well-managed', 'delicious', 
            'attentive', 'friendly', 'efficient', 'prompt', 'fresh', 'quality',
            'consistent', 'hygienic', 'well-trained', 'thorough', 'immaculate',
            'compliant', 'reliable', 'careful', 'diligent', 'secure'
        ]
        self.negative_indicators = [
            'hazard', 'dirty', 'violation', 'unsafe', 'equipment failure',
            'bugs', 'unclean', 'untrained', 'messy', 'accident', 'unsanitary',
            'dangerous', 'negligent', 'broken', 'contaminated', 'slow', 'rude',
            'spoiled', 'expired', 'rats', 'mice', 'insects', 'mold', 'illness',
            'sick', 'food poisoning', 'health code', 'complaint', 'health department',
            'careless', 'unhygienic', 'uncooked', 'undercooked', 'fire', 'damaged'
        ]
        
        # Image-specific risk indicators
        self.image_risk_indicators = [
            'disorganized', 'cluttered', 'dirty', 'messy', 'unclean', 
            'poor maintenance', 'hazard', 'unsafe', 'damaged', 'broken',
            'crowded', 'violation', 'exposed food', 'pest', 'mold',
            'inadequate', 'improper', 'outdated', 'risk', 'issue'
        ]
        
        # Image-specific positive indicators
        self.image_positive_indicators = [
            'clean', 'organized', 'modern', 'maintained', 'sanitary',
            'spacious', 'proper', 'safety', 'following protocol', 'equipment',
            'ventilation', 'storage', 'professional', 'hygiene', 'compliance'
        ]
    
    def analyze_reviews(self, reviews):
        """Analyze sentiment and extract key information from reviews"""
        results = []
        
        total_reviews = len(reviews)
        print(f"Analyzing {total_reviews} reviews for sentiment")
        
        # For large review sets, show progress
        progress_step = max(1, total_reviews // 10)
        progress_thresholds = [i * progress_step for i in range(1, 11)]
        
        # Process in batches for large sets
        processed_count = 0
        batch_size = 50
        
        # Process all reviews
        for i, review in enumerate(reviews):
            try:
                # Make sure we have text to analyze
                if 'text' not in review or not review['text']:
                    print(f"Review {i} missing text field, skipping")
                    continue
                
                # Extract the rating - convert to a number if it's a string
                rating = review.get('rating', 3)  # Default to neutral
                if isinstance(rating, str):
                    try:
                        rating = float(rating)
                    except ValueError:
                        rating = 3  # Default if can't convert
                
                # Calculate sentiment scores
                sentiment = self.sid.polarity_scores(review['text'])
                
                # Extract keywords - more efficient with longer lists
                pos_keywords = []
                neg_keywords = []
                
                # Convert to lowercase once for efficiency
                review_text_lower = review['text'].lower()
                
                # For very large review sets, optimize keyword extraction
                if total_reviews > 100:
                    # Use a more efficient algorithm for keyword extraction
                    for word in self.positive_indicators:
                        if word.lower() in review_text_lower:
                            pos_keywords.append(word)
                    
                    for word in self.negative_indicators:
                        if word.lower() in review_text_lower:
                            neg_keywords.append(word)
                else:
                    # Original approach for smaller sets
                    pos_keywords = [word for word in self.positive_indicators 
                                  if word.lower() in review_text_lower]
                    neg_keywords = [word for word in self.negative_indicators 
                                  if word.lower() in review_text_lower]
                
                # Determine sentiment category - consider rating as well as text sentiment
                # This gives more balanced results between positive, neutral and negative
                if sentiment['compound'] >= 0.2 or rating >= 4:
                    sentiment_category = 'positive'
                elif sentiment['compound'] <= -0.1 or rating <= 2:
                    sentiment_category = 'negative'
                else:
                    sentiment_category = 'neutral'
                
                # Use review ID if available, otherwise generate a sequential ID
                review_id = review.get('id', f"review_{i}")
                
                # Add the analyzed review
                results.append({
                    'review_id': review_id,
                    'rating': rating,
                    'text': review['text'],
                    'sentiment_scores': sentiment,
                    'sentiment_category': sentiment_category,
                    'positive_keywords': pos_keywords,
                    'negative_keywords': neg_keywords
                })
                
                # Update processed count
                processed_count += 1
                
                # Show progress for large review sets
                if total_reviews > 10 and processed_count in progress_thresholds:
                    print(f"Progress: {processed_count}/{total_reviews} reviews analyzed ({int(processed_count/total_reviews*100)}%)")
                
            except Exception as e:
                print(f"Error analyzing review {i}: {str(e)}")
                continue
                
        print(f"Completed sentiment analysis on {len(results)} reviews")
        return results
    
    def analyze_image_results(self, image_analyses):
        """Analyze the results from image analysis to extract sentiment and keywords"""
        if not image_analyses:
            return []
            
        print(f"Analyzing sentiment from {len(image_analyses)} image analyses")
        results = []
        
        for i, analysis in enumerate(image_analyses):
            try:
                # Combine all observations into a single text for sentiment analysis
                observations_text = ' '.join(analysis.get('observations', []))
                
                # Calculate sentiment scores
                sentiment = self.sid.polarity_scores(observations_text)
                
                # Extract risk and positive factors
                risk_factors = analysis.get('risk_factors', [])
                positive_factors = analysis.get('positive_factors', [])
                
                # Determine overall sentiment based on the observations
                if sentiment['compound'] >= 0.05 and len(risk_factors) == 0:
                    sentiment_category = 'positive'
                elif sentiment['compound'] <= -0.05 or len(risk_factors) > 0:
                    sentiment_category = 'negative'
                else:
                    sentiment_category = 'neutral'
                
                # Add the analyzed image
                results.append({
                    'image_url': analysis.get('image_url', ''),
                    'observations': analysis.get('observations', []),
                    'sentiment_scores': sentiment,
                    'sentiment_category': sentiment_category,
                    'risk_factors': risk_factors,
                    'positive_factors': positive_factors
                })
                
            except Exception as e:
                print(f"Error analyzing image {i}: {str(e)}")
                continue
        
        print(f"Completed sentiment analysis on {len(results)} images")
        return results
        
    def get_overall_sentiment(self, analyzed_reviews, analyzed_images=None):
        """Calculate overall sentiment metrics from analyzed reviews and images"""
        total_reviews = len(analyzed_reviews)
        if total_reviews == 0:
            return {
                'total_reviews': 0,
                'positive_percentage': 0,
                'negative_percentage': 0,
                'neutral_percentage': 0,
                'average_compound_score': 0
            }
            
        positive_count = sum(1 for r in analyzed_reviews if r['sentiment_category'] == 'positive')
        negative_count = sum(1 for r in analyzed_reviews if r['sentiment_category'] == 'negative')
        neutral_count = sum(1 for r in analyzed_reviews if r['sentiment_category'] == 'neutral')
        
        # Calculate average sentiment score
        avg_compound = sum(r['sentiment_scores']['compound'] for r in analyzed_reviews) / total_reviews
        
        # Extract all keywords
        all_positive_keywords = [kw for r in analyzed_reviews for kw in r['positive_keywords']]
        all_negative_keywords = [kw for r in analyzed_reviews for kw in r['negative_keywords']]
        
        # Count keyword frequencies
        positive_keyword_freq = {kw: all_positive_keywords.count(kw) for kw in set(all_positive_keywords)}
        negative_keyword_freq = {kw: all_negative_keywords.count(kw) for kw in set(all_negative_keywords)}
        
        # Process image sentiment if available
        image_sentiment = {}
        if analyzed_images and len(analyzed_images) > 0:
            # Calculate image sentiment statistics
            total_images = len(analyzed_images)
            img_positive_count = sum(1 for img in analyzed_images if img['sentiment_category'] == 'positive')
            img_negative_count = sum(1 for img in analyzed_images if img['sentiment_category'] == 'negative')
            img_neutral_count = sum(1 for img in analyzed_images if img['sentiment_category'] == 'neutral')
            
            # Extract all risk and positive factors
            all_risk_factors = [factor for img in analyzed_images for factor in img['risk_factors']]
            all_positive_factors = [factor for img in analyzed_images for factor in img['positive_factors']]
            
            # Count frequencies
            risk_factor_freq = {factor: all_risk_factors.count(factor) for factor in set(all_risk_factors)}
            positive_factor_freq = {factor: all_positive_factors.count(factor) for factor in set(all_positive_factors)}
            
            # Calculate average sentiment score
            img_avg_compound = sum(img['sentiment_scores']['compound'] for img in analyzed_images) / total_images if total_images else 0
            
            image_sentiment = {
                'total_images': total_images,
                'positive_count': img_positive_count,
                'negative_count': img_negative_count,
                'neutral_count': img_neutral_count,
                'positive_percentage': (img_positive_count / total_images) * 100 if total_images else 0,
                'negative_percentage': (img_negative_count / total_images) * 100 if total_images else 0,
                'neutral_percentage': (img_neutral_count / total_images) * 100 if total_images else 0,
                'average_compound_score': img_avg_compound,
                'risk_factor_frequency': risk_factor_freq,
                'positive_factor_frequency': positive_factor_freq
            }
        
        # Return combined sentiment data
        sentiment_data = {
            'total_reviews': total_reviews,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_percentage': (positive_count / total_reviews) * 100,
            'negative_percentage': (negative_count / total_reviews) * 100,
            'neutral_percentage': (neutral_count / total_reviews) * 100,
            'average_compound_score': avg_compound,
            'positive_keyword_frequency': positive_keyword_freq,
            'negative_keyword_frequency': negative_keyword_freq
        }
        
        # Add image sentiment if available
        if image_sentiment:
            sentiment_data['image_sentiment'] = image_sentiment
            
            # Calculate combined sentiment
            sentiment_data['combined_sentiment'] = {
                'total_items': total_reviews + image_sentiment['total_images'],
                'overall_positive_percentage': (positive_count + image_sentiment['positive_count']) / 
                                             (total_reviews + image_sentiment['total_images']) * 100,
                'overall_negative_percentage': (negative_count + image_sentiment['negative_count']) / 
                                             (total_reviews + image_sentiment['total_images']) * 100,
                'overall_neutral_percentage': (neutral_count + image_sentiment['neutral_count']) / 
                                            (total_reviews + image_sentiment['total_images']) * 100
            }
        
        return sentiment_data