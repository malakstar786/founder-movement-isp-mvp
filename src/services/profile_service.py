import os
import logging
from typing import List, Dict, Any, Optional, Tuple

from src.api.proxycurl import ProxycurlAPI
from src.api.session_storage import SessionStorage
from src.models.profile import Profile
from src.models.change import Change
from src.utils.validators import validate_linkedin_url
from src.services.insight_generator import InsightGenerator

# Get logger
logger = logging.getLogger(__name__)

class ProfileService:
    """
    Service for managing LinkedIn profiles
    """
    
    def __init__(self):
        """Initialize the profile service"""
        self.proxycurl_api = ProxycurlAPI()
        self.insight_generator = InsightGenerator()
    
    def add_profile(self, linkedin_url: str) -> Tuple[bool, str]:
        """
        Add a LinkedIn profile to tracking
        
        Parameters:
        - linkedin_url: LinkedIn profile URL to track
        
        Returns:
        - Tuple of (success, message)
        """
        # Validate the URL
        if not validate_linkedin_url(linkedin_url):
            return False, f"Invalid LinkedIn URL: {linkedin_url}"
        
        try:
            # Check if the profile already exists
            existing_profile = SessionStorage.get_profile(linkedin_url)
            
            if existing_profile:
                return True, f"Profile {linkedin_url} is already being tracked"
            
            # Fetch profile data from Proxycurl
            profile_data = self.proxycurl_api.get_profile(linkedin_url)
            
            # Check if profile_data is None or has an error
            if not profile_data:
                return False, f"Error fetching profile: Received empty response"
                
            if "error" in profile_data:
                return False, f"Error fetching profile: {profile_data['error']}"
            
            # Extract relevant data
            extracted_data = self.proxycurl_api.extract_profile_data(profile_data)
            
            # Check if extraction was successful
            if not extracted_data or "error" in extracted_data:
                error_message = extracted_data.get("error", "Failed to extract profile data") if extracted_data else "Failed to extract profile data"
                return False, f"Error processing profile: {error_message}"
            
            # Ensure we keep the full original LinkedIn URL, not just the public identifier
            extracted_data["linkedin_url"] = linkedin_url.strip()
            
            # Add to session storage
            success = SessionStorage.add_profile(extracted_data)
            
            if success:
                return True, f"Successfully added profile {linkedin_url} to tracking"
            else:
                return False, f"Error adding profile {linkedin_url} to storage"
        
        except Exception as e:
            logger.error(f"Error adding profile {linkedin_url}: {str(e)}")
            return False, f"Error adding profile: {str(e)}"
    
    def refresh_profile(self, linkedin_url: str) -> Tuple[bool, str, Optional[Change]]:
        """
        Refresh a LinkedIn profile and detect changes
        
        Parameters:
        - linkedin_url: LinkedIn profile URL to refresh
        
        Returns:
        - Tuple of (success, message, detected_change)
        """
        # Validate the URL
        if not validate_linkedin_url(linkedin_url):
            return False, f"Invalid LinkedIn URL: {linkedin_url}", None
        
        try:
            # Get the existing profile
            existing_profile = SessionStorage.get_profile(linkedin_url)
            
            if not existing_profile:
                # Profile not found, add it
                success, message = self.add_profile(linkedin_url)
                return success, message, None
            
            # Fetch updated profile data from Proxycurl
            profile_data = self.proxycurl_api.get_profile(linkedin_url)
            
            if "error" in profile_data:
                return False, f"Error fetching profile: {profile_data['error']}", None
            
            # Extract relevant data
            extracted_data = self.proxycurl_api.extract_profile_data(profile_data)
            
            # Ensure we keep the full original LinkedIn URL, not just the public identifier
            extracted_data["linkedin_url"] = linkedin_url.strip()
            
            # Check for changes
            old_profile = Profile.from_dict(existing_profile)
            new_profile = Profile.from_dict(extracted_data)
            
            # Detect changes by comparing the *new* profile to the previous saved data
            if new_profile.has_changed_roles(existing_profile):
                # Create a change object
                is_founder = new_profile.is_founder()
                change = Change.from_profile_comparison(
                    linkedin_url=linkedin_url,
                    old_profile=existing_profile,
                    new_profile=extracted_data,
                    is_founder=is_founder
                )
                
                # Record the change
                SessionStorage.record_change(change.to_dict())
                
                # Update the profile
                SessionStorage.add_profile(extracted_data)
                
                # Generate AI insight for founder changes
                if is_founder:
                    try:
                        # Generate insight using OpenAI
                        insight = self.insight_generator.generate_founder_insight(change, extracted_data)
                        logger.info(f"Generated insight for founder change: {linkedin_url}")
                    except Exception as e:
                        logger.error(f"Error generating insight for {linkedin_url}: {str(e)}")
                
                return True, f"Detected role change for {linkedin_url}", change
            else:
                # No change detected, just update the last checked date
                SessionStorage.add_profile(extracted_data)
                
                return True, f"No changes detected for {linkedin_url}", None
        
        except Exception as e:
            logger.error(f"Error refreshing profile {linkedin_url}: {str(e)}")
            return False, f"Error refreshing profile: {str(e)}", None
    
    def batch_add_profiles(self, linkedin_urls: List[str]) -> Dict[str, Any]:
        """
        Add multiple LinkedIn profiles to tracking
        
        Parameters:
        - linkedin_urls: List of LinkedIn profile URLs to track
        
        Returns:
        - Dictionary with results
        """
        results = {
            "success": 0,
            "failed": 0,
            "already_tracked": 0,
            "details": []
        }
        
        for url in linkedin_urls:
            success, message = self.add_profile(url)
            
            # Record result
            results["details"].append({
                "url": url,
                "success": success,
                "message": message
            })
            
            # Update counters
            if success:
                if "already being tracked" in message:
                    results["already_tracked"] += 1
                else:
                    results["success"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def batch_refresh_profiles(self, linkedin_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Refresh multiple LinkedIn profiles
        
        Parameters:
        - linkedin_urls: Optional list of LinkedIn profile URLs to refresh
                         If None, refresh all tracked profiles
        
        Returns:
        - Dictionary with results
        """
        results = {
            "success": 0,
            "failed": 0,
            "changes_detected": 0,
            "founder_changes": 0,
            "details": []
        }
        
        # If no URLs provided, get all tracked profiles
        if not linkedin_urls:
            profiles = SessionStorage.get_all_profiles()
            linkedin_urls = [p.get("linkedin_url") for p in profiles if p.get("linkedin_url")]
        
        for url in linkedin_urls:
            success, message, change = self.refresh_profile(url)
            
            # Record result
            result = {
                "url": url,
                "success": success,
                "message": message,
                "change_detected": change is not None
            }
            
            # Add change details if detected
            if change:
                result["change"] = {
                    "old_title": change.old_title,
                    "new_title": change.new_title,
                    "old_company": change.old_company,
                    "new_company": change.new_company,
                    "is_founder_change": change.is_founder_change
                }
            
            results["details"].append(result)
            
            # Update counters
            if success:
                results["success"] += 1
                
                if change:
                    results["changes_detected"] += 1
                    
                    if change.is_founder_change:
                        results["founder_changes"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def get_all_profiles(self) -> List[Profile]:
        """
        Get all tracked profiles
        
        Returns:
        - List of Profile objects
        """
        profile_dicts = SessionStorage.get_all_profiles()
        return [Profile.from_dict(p) for p in profile_dicts]
    
    def get_profile(self, linkedin_url: str) -> Optional[Profile]:
        """
        Get a specific profile
        
        Parameters:
        - linkedin_url: LinkedIn profile URL
        
        Returns:
        - Profile object or None if not found
        """
        profile_dict = SessionStorage.get_profile(linkedin_url)
        
        if profile_dict:
            return Profile.from_dict(profile_dict)
        
        return None
    
    def get_recent_founder_changes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent founder changes with profile details
        
        Parameters:
        - limit: Maximum number of changes to return
        
        Returns:
        - List of changes with profile details
        """
        # Get recent founder changes
        changes = SessionStorage.get_recent_founder_changes(limit)
        
        # Enhance with profile details
        enhanced_changes = []
        
        for change in changes:
            # Get profile details
            profile = SessionStorage.get_profile(change.get("linkedin_url", ""))
            
            if profile:
                # Combine change and profile details
                enhanced_change = {
                    **change,
                    "first_name": profile.get("first_name", ""),
                    "last_name": profile.get("last_name", ""),
                    "full_name": f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
                }
                
                enhanced_changes.append(enhanced_change)
            else:
                # Just add the change
                enhanced_changes.append(change)
        
        return enhanced_changes 