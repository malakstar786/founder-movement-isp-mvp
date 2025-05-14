import logging
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from src.api.session_storage import SessionStorage
from src.models.outreach import Outreach
from src.models.profile import Profile
from src.models.change import Change
from src.services.insight_generator import InsightGenerator

# Get logger
logger = logging.getLogger(__name__)

class OutreachService:
    """
    Service for managing outreach to founders
    """
    
    def __init__(self):
        """Initialize the outreach service"""
        self.insight_generator = InsightGenerator()
    
    def create_outreach(
        self,
        linkedin_url: str,
        change_id: Optional[int] = None,
        outreach_method: str = "Email",
        notes: str = ""
    ) -> Tuple[bool, str, Optional[Outreach]]:
        """
        Create a new outreach record
        
        Parameters:
        - linkedin_url: LinkedIn URL of the profile
        - change_id: Optional ID of the change that triggered the outreach
        - outreach_method: Method of outreach (Email, LinkedIn, etc.)
        - notes: Optional notes about the outreach
        
        Returns:
        - Tuple of (success, message, outreach)
        """
        try:
            # Initialize storage
            SessionStorage.initialize_storage()
            
            # Create outreach object
            outreach = Outreach(
                linkedin_url=linkedin_url,
                change_id=change_id,
                outreach_method=outreach_method,
                notes=notes
            )
            
            # Add to session state
            if 'outreach' not in st.session_state:
                st.session_state['outreach'] = []
            
            # Generate a unique outreach_id if not provided
            outreach_ids = [int(o.get("outreach_id", 0)) for o in st.session_state['outreach']]
            next_outreach_id = max(outreach_ids, default=0) + 1
            outreach.outreach_id = next_outreach_id
            
            # Save to session storage
            st.session_state['outreach'].append(outreach.to_dict())
            
            return True, "Outreach record created successfully", outreach
        
        except Exception as e:
            logger.error(f"Error creating outreach: {str(e)}")
            return False, f"Error creating outreach: {str(e)}", None
    
    def get_founder_outreach_suggestions(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get suggestions for founder outreach based on recent changes
        
        Parameters:
        - limit: Maximum number of suggestions to return
        
        Returns:
        - List of outreach suggestions
        """
        try:
            # Get recent founder changes
            changes = SessionStorage.get_recent_founder_changes(limit)
            
            # Get profile details for changes
            suggestions = []
            
            for change in changes:
                # Get LinkedIn URL
                linkedin_url = change.get("linkedin_url", "")
                
                # Get profile details
                profile_data = SessionStorage.get_profile(linkedin_url)
                
                if profile_data:
                    # Convert to Profile object
                    profile = Profile.from_dict(profile_data)
                    
                    # Convert change to Change object
                    change_obj = Change.from_dict(change)
                    
                    # Generate analysis
                    analysis = self.insight_generator.analyze_founder_potential(profile, change_obj)
                    
                    # Generate outreach suggestions
                    outreach_suggestions = self.insight_generator.generate_outreach_suggestions(profile, analysis)
                    
                    # Add to results
                    suggestion = {
                        "profile": profile.to_dict(),
                        "change": change,
                        "analysis": analysis,
                        "outreach_suggestions": outreach_suggestions
                    }
                    
                    suggestions.append(suggestion)
            
            return suggestions
        
        except Exception as e:
            logger.error(f"Error getting outreach suggestions: {str(e)}")
            return [] 