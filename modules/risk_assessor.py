class RiskAssessor:
    def __init__(self):
        # Define risk factors based on underwriting guidelines
        self.risk_factors = {
            'sentiment': {
                'low_risk': {'positive_percentage': 70, 'negative_percentage': 15},
                'medium_risk': {'positive_percentage': 50, 'negative_percentage': 30},
                'high_risk': {'positive_percentage': 30, 'negative_percentage': 50}
            },
            'keywords': {
                'critical_negative': ['violation', 'hazard', 'unsafe', 'accident', 'injury', 'bugs']
            }
        }
        
        # Define class codes based on underwriting guidelines
        self.class_codes = {
            'restaurant': '16910',  # Full-service Restaurant
            'bar': '16911',         # Bar/Tavern
            'nightclub': '16912',   # Nightclub
            'fast_food': '16920'    # Fast Food Restaurant
        }
    
    def determine_class_code(self, business_details):
        """Determine the primary class code based on business details"""
        # Default to restaurant if no categories
        if 'categories' not in business_details or not business_details['categories']:
            return self.class_codes['restaurant']
            
        # Extract all category titles and convert to lowercase for easier matching
        categories = [cat['title'].lower() for cat in business_details['categories']]
        category_text = ' '.join(categories)
        
        print(f"Determining class code for business with categories: {categories}")
        
        # Check for alcohol-related phrases - if there are many, it's likely a bar
        alcohol_keywords = ['bar', 'pub', 'tavern', 'brewery', 'cocktail', 'beer', 'wine', 'liquor', 
                           'spirits', 'whiskey', 'vodka', 'tequila', 'drinks', 'alcohol']
        alcohol_count = sum(1 for keyword in alcohol_keywords if keyword in category_text)
        
        # Check for nightclub keywords first (highest risk category)
        nightclub_keywords = ['nightclub', 'night club', 'dance club', 'dancing', 'cabaret', 'disco', 
                             'lounge', 'nightlife', 'entertainment', 'dj', 'live music', 'club']
        nightclub_count = sum(1 for keyword in nightclub_keywords if keyword in category_text)
        
        # Check restaurant keywords
        restaurant_keywords = ['restaurant', 'bistro', 'café', 'cafe', 'eatery', 'dining', 'grill', 
                              'kitchen', 'chophouse', 'steakhouse', 'pizza', 'sushi', 'food']
        restaurant_count = sum(1 for keyword in restaurant_keywords if keyword in category_text)
        
        # Check for fast food keywords
        fast_food_keywords = ['fast food', 'quick service', 'fast casual', 'drive-thru', 'drive through', 
                             'takeout', 'take-out', 'take out', 'fast-food', 'quick-service', 
                             'fast', 'quick', 'express', 'counter service', 'self-service']
        fast_food_count = sum(1 for keyword in fast_food_keywords if keyword in category_text)
        
        # Check name for additional clues
        name_points = {'nightclub': 0, 'bar': 0, 'fast_food': 0, 'restaurant': 0}
        
        if 'name' in business_details:
            name_lower = business_details['name'].lower()
            
            # Check name for nightclub indicators
            club_name_keywords = ['club', 'lounge', 'disco', 'dance', 'dj', 'night']
            if any(keyword in name_lower for keyword in club_name_keywords):
                name_points['nightclub'] += 2
                
            # Check name for bar indicators
            bar_name_keywords = ['bar', 'pub', 'tavern', 'brewery', 'brew', 'beer', 'wine', 'spirits']
            if any(keyword in name_lower for keyword in bar_name_keywords):
                name_points['bar'] += 2
                    
            # Check name for fast food indicators
            fast_food_name_keywords = ['fast', 'quick', 'express', 'burger', 'pizza', "mcdonald's", 'wendy', 
                                      'kfc', 'taco bell', 'subway', 'chipotle', 'drive']
            if any(keyword in name_lower for keyword in fast_food_name_keywords):
                name_points['fast_food'] += 2
                
            # Check for restaurant indicators
            restaurant_name_keywords = ['restaurant', 'bistro', 'café', 'cafe', 'grill', 'kitchen', 
                                       'steakhouse', 'eatery', 'dining']
            if any(keyword in name_lower for keyword in restaurant_name_keywords):
                name_points['restaurant'] += 2
        
        # Check price level if available - typically $ is fast food, $$$$ is fine dining
        if 'price' in business_details:
            price = business_details.get('price', '')
            if price == '$':
                fast_food_count += 2
            elif price == '$$$$':
                restaurant_count += 2
                
        # Calculate scores for each category
        scores = {
            'nightclub': nightclub_count * 3 + name_points['nightclub'],  # Higher weight for nightclub
            'bar': alcohol_count * 2 + name_points['bar'] - restaurant_count,  # Bar minus restaurant indication
            'fast_food': fast_food_count * 2 + name_points['fast_food'],
            'restaurant': restaurant_count + name_points['restaurant']
        }
        
        print(f"Class code scores: {scores}")
        
        # Determine the highest score
        max_score = 0
        max_category = 'restaurant'  # Default
        
        for category, score in scores.items():
            if score > max_score:
                max_score = score
                max_category = category
                
        # Fast food and nightclub have minimum thresholds to ensure we don't misclassify
        if max_category == 'nightclub' and max_score < 3:
            max_category = 'bar' if scores['bar'] > scores['restaurant'] else 'restaurant'
            
        if max_category == 'fast_food' and max_score < 2:
            max_category = 'restaurant'
            
        # Final result
        if max_category == 'nightclub':
            print(f"Classified as nightclub with score {max_score}")
            return self.class_codes['nightclub']
        elif max_category == 'bar':
            print(f"Classified as bar with score {max_score}")
            return self.class_codes['bar']
        elif max_category == 'fast_food':
            print(f"Classified as fast food with score {max_score}")
            return self.class_codes['fast_food']
        else:
            print(f"Classified as restaurant with score {max_score}")
            return self.class_codes['restaurant']
    
    def assess_risk(self, sentiment_analysis, business_details):
        """Assess risk based on underwriting guidelines"""
        # Extract relevant metrics with defaults for missing data
        positive_percentage = sentiment_analysis.get('positive_percentage', 0)
        negative_percentage = sentiment_analysis.get('negative_percentage', 0)
        
        # Print for debugging
        print(f"Risk Assessment - Positive: {positive_percentage}%, Negative: {negative_percentage}%")
        
        # For safety, ensure we don't have unrealistic percentages (sometimes LLMs give 100% positive)
        if positive_percentage > 95 and sentiment_analysis.get('total_reviews', 0) > 10:
            print(f"Adjusting suspiciously high positive percentage: {positive_percentage}")
            positive_percentage = 85  # Cap at a more realistic max
            
        if negative_percentage < 5 and sentiment_analysis.get('total_reviews', 0) > 10:
            print(f"Adjusting suspiciously low negative percentage: {negative_percentage}")
            negative_percentage = 5  # Ensure some minimum negative percentage
        
        # Check for critical negative keywords with safe dictionary access
        critical_keywords_found = False
        critical_keywords = []
        if 'negative_keyword_frequency' in sentiment_analysis:
            negative_keywords = sentiment_analysis['negative_keyword_frequency']
            critical_keywords = [
                kw for kw in self.risk_factors['keywords']['critical_negative'] 
                if kw in negative_keywords
            ]
            critical_keywords_found = len(critical_keywords) > 0
            
        print(f"Critical keywords found: {critical_keywords_found}, Keywords: {critical_keywords}")
        
        # Determine risk level based on sentiment and keywords
        # Use a more nuanced approach that doesn't just rely on thresholds
        
        # Start with point-based system
        risk_score = 0
        
        # Base points from sentiment percentages
        if positive_percentage >= 80:
            risk_score -= 3  # Very positive reviews reduce risk
        elif positive_percentage >= 70:
            risk_score -= 2
        elif positive_percentage >= 50:
            risk_score -= 1
            
        if negative_percentage >= 40:
            risk_score += 3  # Very negative reviews increase risk
        elif negative_percentage >= 30:
            risk_score += 2
        elif negative_percentage >= 20:
            risk_score += 1
            
        # Points from critical keywords
        risk_score += len(critical_keywords) * 2
        
        # Determine risk level from score
        if risk_score <= -2 and not critical_keywords_found:
            risk_level = 'low'
            confidence = 0.85
        elif risk_score <= 1 and not critical_keywords_found:
            risk_level = 'medium'
            confidence = 0.75
        else:
            risk_level = 'high'
            confidence = 0.80
            
        print(f"Risk level determined as '{risk_level}' with score {risk_score} and confidence {confidence}")
        
        # Determine eligibility based on risk level
        class_code = self.determine_class_code(business_details)
        
        # Check for ineligible criteria from underwriting guidelines
        ineligible_criteria = []
        
        # Check if it's a fast food restaurant (ineligible per guidelines)
        if class_code == self.class_codes['fast_food']:
            ineligible_criteria.append("Fast Food Restaurants are ineligible per underwriting guidelines")
        
        # Check for critical safety concerns
        if critical_keywords_found:
            ineligible_criteria.append("Critical safety concerns identified in reviews")
        
        # Determine eligibility
        if ineligible_criteria:
            eligibility = "INELIGIBLE"
        elif risk_level == 'high':
            eligibility = "NEEDS_REVIEW"
        else:
            eligibility = "ELIGIBLE"
        
        return {
            'risk_level': risk_level,
            'class_code': class_code,
            'eligibility': eligibility,
            'confidence': confidence,
            'ineligible_criteria': ineligible_criteria,
            'positive_factors': self._get_positive_factors(sentiment_analysis),
            'negative_factors': self._get_negative_factors(sentiment_analysis)
        }
    
    def _get_positive_factors(self, sentiment_analysis):
        """Extract positive factors from sentiment analysis"""
        factors = []
        
        if sentiment_analysis['positive_percentage'] >= 70:
            factors.append("High percentage of positive reviews")
        
        for keyword, count in sentiment_analysis['positive_keyword_frequency'].items():
            if count >= 2:
                factors.append(f"Multiple mentions of '{keyword}'")
        
        return factors
    
    def _get_negative_factors(self, sentiment_analysis):
        """Extract negative factors from sentiment analysis"""
        factors = []
        
        if sentiment_analysis['negative_percentage'] >= 30:
            factors.append("High percentage of negative reviews")
        
        for keyword, count in sentiment_analysis['negative_keyword_frequency'].items():
            if count >= 1:
                factors.append(f"Mentions of '{keyword}'")
        
        return factors
