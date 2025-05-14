import logging
from typing import List, Dict, Any, Optional, Tuple

from config.settings import Settings
from src.models.profile import Profile
from src.models.change import Change
from src.utils.helpers import detect_founder_keywords

# Get logger
logger = logging.getLogger(__name__)

class ChangeDetector:
    """
    Service for detecting career changes, particularly founder transitions
    """
    
    def __init__(self):
        """Initialize the change detector"""
        self.founder_keywords = Settings.get_founder_keywords()
    
    def detect_change(
        self,
        old_profile: Dict[str, Any],
        new_profile: Dict[str, Any]
    ) -> Optional[Change]:
        """
        Detect changes between two profile versions
        
        Parameters:
        - old_profile: Previous profile data
        - new_profile: Current profile data
        
        Returns:
        - Change object if change detected, None otherwise
        """
        if not old_profile or not new_profile:
            return None
        
        # Get LinkedIn URL
        linkedin_url = new_profile.get("linkedin_url", "")
        
        # Check if title or company has changed
        title_changed = (
            old_profile.get("current_title", "") != new_profile.get("current_title", "") and
            new_profile.get("current_title", "")
        )
        
        company_changed = (
            old_profile.get("current_company", "") != new_profile.get("current_company", "") and
            new_profile.get("current_company", "")
        )
        
        # If no changes, return None
        if not (title_changed or company_changed):
            return None
        
        # Check if this is a founder-related change
        is_founder_change = self.is_founder_change(new_profile)
        
        # Create change object
        change = Change(
            linkedin_url=linkedin_url,
            old_title=old_profile.get("current_title", ""),
            new_title=new_profile.get("current_title", ""),
            old_company=old_profile.get("current_company", ""),
            new_company=new_profile.get("current_company", ""),
            is_founder_change=is_founder_change
        )
        
        return change
    
    def is_founder_change(self, profile_data: Dict[str, Any]) -> bool:
        """
        Check if a profile change indicates a founder role
        
        Parameters:
        - profile_data: Profile data to check
        
        Returns:
        - Boolean indicating if this is a founder-related change
        """
        # Get current title and company
        current_title = profile_data.get("current_title", "")
        current_company = profile_data.get("current_company", "")
        
        # Check title for founder keywords
        if detect_founder_keywords(current_title, self.founder_keywords):
            return True
        
        # Look for stealth mode signals
        stealth_keywords = ["stealth", "building", "launching", "starting", "startup"]
        if detect_founder_keywords(current_title, stealth_keywords) or detect_founder_keywords(current_company, stealth_keywords):
            return True
        
        return False
    
    def analyze_change_significance(self, change: Change) -> Dict[str, Any]:
        """
        Analyze the significance of a career change
        
        Parameters:
        - change: Change object to analyze
        
        Returns:
        - Dictionary with analysis results
        """
        analysis = {
            "is_significant": False,
            "reasons": [],
            "score": 0  # 0-100 scale of significance
        }
        
        # Check if it's a founder change
        if change.is_founder_change:
            analysis["is_significant"] = True
            analysis["reasons"].append("Change to founder role detected")
            analysis["score"] += 80
        
        # Check if both title and company changed
        if change.is_title_change() and change.is_company_change():
            analysis["reasons"].append("Both role and company changed")
            analysis["score"] += 50
        elif change.is_title_change():
            analysis["reasons"].append("Role changed within same company")
            analysis["score"] += 30
        elif change.is_company_change():
            analysis["reasons"].append("Company changed with similar role")
            analysis["score"] += 40
        
        # Cap score at 100
        analysis["score"] = min(analysis["score"], 100)
        
        # If score is high enough, mark as significant
        if analysis["score"] >= 50:
            analysis["is_significant"] = True
        
        return analysis
    
    def detect_batch_changes(
        self,
        profiles_data: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], Change]]:
        """
        Detect changes in a batch of profiles
        
        Parameters:
        - profiles_data: List of tuples with (old_profile, new_profile)
        
        Returns:
        - List of tuples with (profile_data, detected_change)
        """
        results = []
        
        for old_profile, new_profile in profiles_data:
            change = self.detect_change(old_profile, new_profile)
            
            if change:
                # Add to results if change detected
                results.append((new_profile, change))
        
        return results
    
    def filter_founder_changes(self, changes: List[Change]) -> List[Change]:
        """
        Filter a list of changes to get only founder-related changes
        
        Parameters:
        - changes: List of Change objects
        
        Returns:
        - List of founder-related Change objects
        """
        return [c for c in changes if c.is_founder_change]
    
    def categorize_changes(self, changes: List[Change]) -> Dict[str, List[Change]]:
        """
        Categorize changes by type
        
        Parameters:
        - changes: List of Change objects
        
        Returns:
        - Dictionary of categorized changes
        """
        categories = {
            "founder": [],
            "company": [],
            "title": [],
            "other": []
        }
        
        for change in changes:
            if change.is_founder_change:
                categories["founder"].append(change)
            elif change.is_company_change() and change.is_title_change():
                # Both company and title changed
                categories["company"].append(change)
            elif change.is_title_change():
                # Only title changed
                categories["title"].append(change)
            else:
                # Other changes
                categories["other"].append(change)
        
        return categories
