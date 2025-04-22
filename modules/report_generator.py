class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_report(self, business_details, sentiment_analysis, risk_assessment):
        """Generate a comprehensive underwriting report"""
        
        # Format the report data
        report = {
            "business_info": {
                "name": business_details["name"],
                "address": f"{business_details['location']['address1']}, {business_details['location']['city']}, {business_details['location']['state']} {business_details['location']['zip_code']}",
                "rating": business_details["rating"],
                "review_count": business_details["review_count"],
                "price_level": business_details["price"],
                "categories": [cat["title"] for cat in business_details["categories"]]
            },
            "sentiment_analysis": {
                "total_reviews": sentiment_analysis["total_reviews"],
                "positive_percentage": round(sentiment_analysis["positive_percentage"], 2),
                "negative_percentage": round(sentiment_analysis["negative_percentage"], 2),
                "neutral_percentage": round(sentiment_analysis["neutral_percentage"], 2),
                "average_sentiment_score": round(sentiment_analysis["average_compound_score"], 2),
                "positive_keywords": sentiment_analysis["positive_keyword_frequency"],
                "negative_keywords": sentiment_analysis["negative_keyword_frequency"]
            },
            "risk_assessment": {
                "risk_level": risk_assessment["risk_level"],
                "primary_class_code": risk_assessment["class_code"],
                "eligibility": risk_assessment["eligibility"],
                "confidence": round(risk_assessment["confidence"] * 100, 2),
                "ineligible_criteria": risk_assessment["ineligible_criteria"],
                "positive_factors": risk_assessment["positive_factors"],
                "negative_factors": risk_assessment["negative_factors"]
            },
            "recommendation": self._generate_recommendation(risk_assessment)
        }
        
        return report
    
    def _generate_recommendation(self, risk_assessment):
        """Generate a recommendation based on risk assessment"""
        
        if risk_assessment["eligibility"] == "INELIGIBLE":
            return "Decline coverage due to ineligible criteria."
        elif risk_assessment["eligibility"] == "NEEDS_REVIEW":
            return "Refer to senior underwriter for manual review. Consider additional information gathering."
        else:
            if risk_assessment["risk_level"] == "low":
                return "Approve coverage with standard terms and pricing."
            else:  # medium risk
                return "Approve coverage with enhanced monitoring and potential premium adjustment."
