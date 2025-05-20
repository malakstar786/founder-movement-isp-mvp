import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from datetime import datetime

from src.api.linkedin_profile import get_linkedin_profile_data
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
        self.insight_generator = InsightGenerator()
    
    async def add_profile(self, linkedin_url: str) -> Tuple[bool, str]:
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
            
            # Fetch profile data from LinkedIn
            profile_data = await get_linkedin_profile_data(linkedin_url)
            
            if not profile_data or "error" in profile_data:
                error_message = profile_data.get("message", "Unknown error from API") if profile_data else "Empty response from API"
                return False, f"Error fetching profile: {error_message}"
            
            # Extract relevant data
            processed_profile = await self.process_linkedin_profile(linkedin_url, profile_data)
            
            if not processed_profile:
                return False, "Failed to process profile data"
            
            # Add to session storage
            success = SessionStorage.add_profile(processed_profile)
            print(f"[DEBUG] Stored profile: {processed_profile}")
            
            if success:
                return True, f"Successfully added profile {linkedin_url} to tracking"
            else:
                return False, f"Error adding profile {linkedin_url} to storage"
        
        except Exception as e:
            logger.error(f"Error adding profile {linkedin_url}: {str(e)}")
            return False, f"Error adding profile: {str(e)}"
    
    async def refresh_profile(self, linkedin_url: str) -> Tuple[bool, str, Optional[Change]]:
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
                success, message = await self.add_profile(linkedin_url)
                return success, message, None
            
            # Fetch updated profile data from LinkedIn
            profile_data = await get_linkedin_profile_data(linkedin_url)
            
            if "error" in profile_data:
                return False, f"Error fetching profile: {profile_data['error']}", None
            
            # Extract relevant data
            processed_profile = await self.process_linkedin_profile(linkedin_url, profile_data)
            
            if not processed_profile:
                return False, "Failed to process profile data", None
            
            # Check for changes
            old_profile = Profile.from_dict(existing_profile)
            new_profile = Profile.from_dict(processed_profile)
            
            # Detect changes by comparing the *new* profile to the previous saved data
            if new_profile.has_changed_roles(existing_profile):
                # Create a change object
                is_founder = new_profile.is_founder()
                change = Change.from_profile_comparison(
                    linkedin_url=linkedin_url,
                    old_profile=existing_profile,
                    new_profile=processed_profile,
                    is_founder=is_founder
                )
                
                # Record the change
                SessionStorage.record_change(change.to_dict())
                
                # Update the profile
                SessionStorage.add_profile(processed_profile)
                
                # Generate AI insight for founder changes
                if is_founder:
                    try:
                        # Generate insight using OpenAI
                        insight = self.insight_generator.generate_founder_insight(change, processed_profile)
                        logger.info(f"Generated insight for founder change: {linkedin_url}")
                    except Exception as e:
                        logger.error(f"Error generating insight for {linkedin_url}: {str(e)}")
                
                return True, f"Detected role change for {linkedin_url}", change
            else:
                # No change detected, just update the last checked date
                SessionStorage.add_profile(processed_profile)
                
                return True, f"No changes detected for {linkedin_url}", None
        
        except Exception as e:
            logger.error(f"Error refreshing profile {linkedin_url}: {str(e)}")
            return False, f"Error refreshing profile: {str(e)}", None
    
    async def batch_add_profiles(self, linkedin_urls: List[str]) -> Dict[str, Any]:
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
        
        tasks = [self.add_profile(url) for url in linkedin_urls]
        task_results = await asyncio.gather(*tasks)
        
        for i, url in enumerate(linkedin_urls):
            success, message = task_results[i]
            
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
    
    async def batch_refresh_profiles(self, linkedin_urls: Optional[List[str]] = None) -> Dict[str, Any]:
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
        
        tasks = [self.refresh_profile(url) for url in linkedin_urls]
        task_results = await asyncio.gather(*tasks)

        for i, url in enumerate(linkedin_urls):
            success, message, change = task_results[i]
            
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

    async def process_linkedin_profile(self, linkedin_url: str, profile_data: dict) -> Optional[dict]:
        """
        Processes LinkedIn profile data and returns a processed profile dictionary.
        
        Parameters:
        - linkedin_url: LinkedIn profile URL
        - profile_data: Raw profile data from LinkedIn
        
        Returns:
        - Processed profile dictionary or None if processing fails
        """
        # Direct fields for current role
        first_name = profile_data.get("first_name", "")
        last_name = profile_data.get("last_name", "")
        current_title = profile_data.get("job_title", "") # Current job title from top level
        current_company = profile_data.get("company", "") # Current company from top level
        
        # For previous roles, iterate through experiences
        previous_title = ""
        previous_company = ""
        
        experiences = profile_data.get("experiences", [])
        if isinstance(experiences, list):
            # Sort experiences by end_year and end_month if available, or start_year/start_month
            # For simplicity, we'll just take the first non-current one if present.
            # A more robust solution would parse date_range or use end_year/start_year.
            past_experiences = [exp for exp in experiences if not exp.get("is_current")]
            
            # Simple approach: take the first past experience.
            # More complex: sort by end date. For now, let's assume the API returns them in a somewhat chronological order (latest first)
            # or that the first non-current one encountered is sufficient for a "previous" role display.
            if past_experiences:
                # To get the *most recent* previous job, you'd ideally sort by end date.
                # The 'date_range' field like "YYYY - YYYY" or "Month YYYY - Month YYYY" or "Month YYYY - Present"
                # would need careful parsing. Or, if 'end_year' and 'end_month' were reliably present for past jobs.
                # Given the example, 'is_current': false is the primary indicator.
                
                # Let's find the most chronologically recent past experience
                # This requires parsing 'date_range' or having structured end dates.
                # For now, taking the first one listed that is not current.
                # A better way would be to parse date_range or if end_year/end_month was consistently available.
                # The example for cjfollini has "date_range": "2014 - 2019"
                
                # Simplistic: take the first non-current role.
                # A more robust approach is needed if strict chronological order of past roles is critical.
                # The RapidAPI 'experiences' are often sorted with current ones first.
                if past_experiences:
                    # We need to sort past_experiences by their end date to find the most recent one.
                    # The 'date_range' (e.g., "Jan 2020 - Dec 2022") or individual date fields if available would be used.
                    # For simplicity, if 'end_year' and 'end_month' are available, use them.
                    # Otherwise, a placeholder or the first found past experience.

                    # Let's try to find the most recent one based on start_year if end_year is not available.
                    # This is a heuristic.
                    sorted_past_experiences = sorted(
                        past_experiences,
                        key=lambda x: (
                            int(x.get("end_year")) if x.get("end_year") else (int(x.get("start_year")) if x.get("start_year") else 0),
                            int(x.get("end_month")) if x.get("end_month") else (int(x.get("start_month")) if x.get("start_month") else 0)
                        ),
                        reverse=True
                    )
                    if sorted_past_experiences:
                        most_recent_past_exp = sorted_past_experiences[0]
                        previous_title = most_recent_past_exp.get("title", "")
                        previous_company = most_recent_past_exp.get("company", "")

        # This is where you would create your Profile object or dict
        processed_profile = {
            "linkedin_url": linkedin_url,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": profile_data.get("full_name", f"{first_name} {last_name}".strip()),
            "current_title": current_title,
            "current_company": current_company,
            "previous_title": previous_title,
            "previous_company": previous_company,
            "headline": profile_data.get("headline", ""),
            "summary": profile_data.get("about", ""), # 'about' seems to be the summary
            "location": profile_data.get("location", ""),
            "country": profile_data.get("country", ""),
            "skills": profile_data.get("skills", ""), # Assuming skills is a comma-separated string or list
            "profile_pic_url": profile_data.get("profile_image_url", ""),
            "follower_count": profile_data.get("connections_count") or profile_data.get("followers_count"), # API uses connections_count or followers_count
            "raw_data": profile_data, # Store the whole response for future use/debugging
            "last_checked_date": datetime.now().isoformat(),
            "tracking_status": "Active", # Default status
            "outreach_status": "Not contacted" # Default status
        }
        
        print(f"Processed data for {linkedin_url}: {processed_profile['full_name']}, {processed_profile['current_title']} at {processed_profile['current_company']}")

        return processed_profile

if __name__ == '__main__':
    # For testing this module directly
    async def test_run():
        # test_url = "https://www.linkedin.com/in/cjfollini/"
        # test_url = "https://www.linkedin.com/in/imranaly/"
        test_url = "https://www.linkedin.com/in/hus3ain/"

        profile_service = ProfileService()
        # To test batch add:
        # results = await profile_service.batch_add_profiles([test_url, "https://www.linkedin.com/in/anotherprofile/"])
        # print("\n--- Batch Add Results ---")
        # import json
        # print(json.dumps(results, indent=2))

        # Test single add profile
        success, message = await profile_service.add_profile(test_url)
        print(f"Add profile result: Success - {success}, Message - {message}")

        if success and "already being tracked" not in message:
            profile_details = profile_service.get_profile(test_url)
            if profile_details:
                print("\n--- Fetched Profile after add ---")
                import json
                print(json.dumps(profile_details.to_dict(), indent=2))
            else:
                print("Could not retrieve profile after adding.")
        
        # Test refresh profile
        # refresh_success, refresh_message, refresh_change = await profile_service.refresh_profile(test_url)
        # print(f"Refresh profile result: Success - {refresh_success}, Message - {refresh_message}, Change - {refresh_change}")
        # if refresh_change:
        #     print(json.dumps(refresh_change.to_dict(), indent=2))

    asyncio.run(test_run())

# --- TODO ---
# - Implement get_profile_from_sheet, detect_changes, generate_insight, add_change_to_sheet, update_profile_in_sheet
# - Ensure robust error handling and logging throughout
# - Refine the logic for determining the "most recent" previous company, possibly by parsing 'date_range'
#   or ensuring the API provides structured start/end dates for experiences.
# - Make sure the 'skills' field is processed correctly (e.g. if it's a list or string). The API response for cjfollini shows it as a string.
# - The 'follower_count' in RapidAPI can be 'connections_count' or 'followers_count'. Added a check. 