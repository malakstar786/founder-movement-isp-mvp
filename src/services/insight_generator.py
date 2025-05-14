import logging
from typing import Dict, Any, Optional, List

from src.api.openai_api import OpenAIAPI
from src.models.change import Change
from src.models.profile import Profile
from src.api.session_storage import SessionStorage

# Get logger
logger = logging.getLogger(__name__)

class InsightGenerator:
    """
    Service for generating AI-powered insights about founder transitions
    """
    
    def __init__(self):
        """Initialize the insight generator"""
        self.openai_api = OpenAIAPI()
    
    def generate_founder_insight(
        self,
        change: Change,
        profile_data: Dict[str, Any]
    ) -> str:
        """
        Generate insight for a founder transition
        
        Parameters:
        - change: Change object representing the career change
        - profile_data: Dictionary containing profile information
        
        Returns:
        - String containing the generated insight
        """
        try:
            # Generate insight using OpenAI
            insight = self.openai_api.generate_founder_insight(profile_data, change.to_dict())
            
            # Update the change with the insight
            change.ai_insight = insight
            
            # Update the change in session storage
            change_dict = change.to_dict()
            SessionStorage.record_change(change_dict)
            
            return insight
        except Exception as e:
            logger.error(f"Error generating insight: {str(e)}")
            return f"Unable to generate insight: {str(e)}"
    
    def generate_insights_for_changes(
        self,
        changes: List[Change],
        profiles: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generate insights for a list of changes
        
        Parameters:
        - changes: List of Change objects
        - profiles: Dictionary mapping LinkedIn URLs to profile data
        
        Returns:
        - Dictionary mapping LinkedIn URLs to insights
        """
        insights = {}
        
        for change in changes:
            # Skip if not a founder change
            if not change.is_founder_change:
                continue
            
            # Get profile data
            profile_data = profiles.get(change.linkedin_url)
            
            if not profile_data:
                # Try to fetch profile data from session storage
                profile_data = SessionStorage.get_profile(change.linkedin_url)
            
            if not profile_data:
                # Skip if no profile data available
                logger.warning(f"No profile data available for {change.linkedin_url}")
                continue
            
            # Generate insight
            insight = self.generate_founder_insight(change, profile_data)
            
            # Add to results
            insights[change.linkedin_url] = insight
        
        return insights
    
    def analyze_founder_potential(
        self,
        profile: Profile,
        change: Optional[Change] = None
    ) -> Dict[str, Any]:
        """
        Analyze the potential of a founder based on their background
        
        Parameters:
        - profile: Profile of the founder
        - change: Optional Change object representing a recent career change
        
        Returns:
        - Dictionary with analysis results
        """
        company_name = profile.current_company
        
        # Create a background dictionary
        founder_background = {
            "previous_title": profile.previous_title,
            "previous_company": profile.previous_company,
            "education": profile.education,
            "skills": profile.skills
        }
        
        try:
            # Generate analysis using OpenAI
            analysis = self.openai_api.analyze_company_potential(company_name, founder_background)
            
            return {
                "founder_name": profile.full_name,
                "company_name": company_name,
                "analysis": analysis,
                "previous_experience": f"{profile.previous_title} at {profile.previous_company}" if profile.previous_title else "",
                "education": profile.education,
                "skills": profile.skills
            }
        except Exception as e:
            logger.error(f"Error analyzing founder potential: {str(e)}")
            return {
                "founder_name": profile.full_name,
                "company_name": company_name,
                "analysis": f"Unable to analyze potential: {str(e)}",
                "previous_experience": f"{profile.previous_title} at {profile.previous_company}" if profile.previous_title else "",
                "education": profile.education,
                "skills": profile.skills
            }
    
    def generate_outreach_suggestions(
        self,
        profile: Profile,
        analysis: Dict[str, Any]
    ) -> List[str]:
        """
        Generate outreach suggestions based on founder's background
        
        Parameters:
        - profile: Profile of the founder
        - analysis: Analysis of the founder's potential
        
        Returns:
        - List of outreach suggestions
        """
        try:
            # Create suggestion based on background
            suggestions = []
            
            # Add suggestion based on previous experience
            if profile.previous_title and profile.previous_company:
                suggestions.append(
                    f"Mention their previous experience as {profile.previous_title} at {profile.previous_company}"
                )
            
            # Add suggestion based on education
            if profile.education:
                school = profile.education[0].get("school", "")
                if school:
                    suggestions.append(f"Reference their education at {school}")
            
            # Add suggestion based on company type
            if "analysis" in analysis and isinstance(analysis["analysis"], str):
                if "fintech" in analysis["analysis"].lower():
                    suggestions.append("Mention your expertise in fintech investments")
                elif "health" in analysis["analysis"].lower():
                    suggestions.append("Highlight your portfolio companies in the health sector")
                elif "AI" in analysis["analysis"] or "artificial intelligence" in analysis["analysis"].lower():
                    suggestions.append("Discuss your interest in AI/ML startups")
            
            # Add a general suggestion
            suggestions.append(
                f"Congratulate {profile.first_name} on their new role as {profile.current_title} at {profile.current_company}"
            )
            
            return suggestions
        except Exception as e:
            logger.error(f"Error generating outreach suggestions: {str(e)}")
            return ["Unable to generate outreach suggestions"] 