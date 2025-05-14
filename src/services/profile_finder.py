import logging
from typing import List, Dict, Any, Optional, Tuple

from src.api.serpapi import SerpAPI
from src.utils.validators import validate_linkedin_url
from config.settings import Settings

# Get logger
logger = logging.getLogger(__name__)

class ProfileFinder:
    """
    Service for finding new LinkedIn profiles to track
    """
    
    def __init__(self):
        """Initialize the profile finder"""
        self.serp_api = SerpAPI()
        self.founder_keywords = Settings.get_founder_keywords()
    
    def search_founder_profiles(
        self,
        keywords: str,
        location: Optional[str] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Search for founder profiles using SerpApi
        
        Parameters:
        - keywords: Search terms (comma-separated)
        - location: Geographic location (optional)
        - page: Page number for pagination
        
        Returns:
        - Dictionary with search results
        """
        try:
            # Parse keywords
            keyword_list = [k.strip() for k in keywords.split(',')]
            
            # Always include some founder-related keywords
            founder_terms = ["founder", "co-founder", "entrepreneur", "startup"]
            has_founder_term = any(term in keyword_list for term in founder_terms)
            
            if not has_founder_term:
                # Add a founder term if none present
                search_terms = f"{keywords}, founder"
            else:
                search_terms = keywords
            
            # Perform search
            search_results = self.serp_api.search_linkedin_profiles(search_terms, location, page)
            
            if "error" in search_results:
                return {
                    "success": False,
                    "error": search_results["error"],
                    "profiles": []
                }
            
            # Extract profile information
            profiles = self.serp_api.extract_profiles(search_results)
            
            # Filter for founder profiles
            founder_profiles = self.filter_founder_profiles(profiles)
            
            # Get API usage info
            usage_info = self.serp_api.get_usage_info()
            
            return {
                "success": True,
                "total_results": len(profiles),
                "founder_results": len(founder_profiles),
                "profiles": founder_profiles,
                "usage_info": usage_info
            }
        except Exception as e:
            logger.error(f"Error searching profiles: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "profiles": []
            }
    
    def filter_founder_profiles(
        self,
        profiles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter profiles to find likely founders
        
        Parameters:
        - profiles: List of profile dictionaries
        
        Returns:
        - List of filtered profile dictionaries
        """
        founder_profiles = []
        
        for profile in profiles:
            job_title = profile.get('job_title', '').lower()
            
            # Check if this looks like a founder
            is_founder = self.serp_api.detect_founder_in_title(job_title)
            
            if is_founder:
                # Add to results
                profile['is_founder'] = True
                
                # Try to extract company name
                company = self.serp_api.parse_company_from_job_title(job_title)
                if company:
                    profile['company_name'] = company
                
                founder_profiles.append(profile)
        
        return founder_profiles
    
    def search_by_company(
        self,
        company_name: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for founder profiles at a specific company
        
        Parameters:
        - company_name: Name of the company to search for
        - location: Geographic location (optional)
        
        Returns:
        - Dictionary with search results
        """
        try:
            # Create search terms with company and founder keywords
            search_terms = f"{company_name}, founder"
            
            # Perform search
            search_results = self.serp_api.search_linkedin_profiles(search_terms, location)
            
            if "error" in search_results:
                return {
                    "success": False,
                    "error": search_results["error"],
                    "profiles": []
                }
            
            # Extract profile information
            profiles = self.serp_api.extract_profiles(search_results)
            
            # Filter for company mentions
            company_profiles = []
            for profile in profiles:
                job_title = profile.get('job_title', '').lower()
                description = profile.get('description', '').lower()
                
                # Check if company name is mentioned
                if (company_name.lower() in job_title or
                    company_name.lower() in description):
                    company_profiles.append(profile)
            
            return {
                "success": True,
                "total_results": len(profiles),
                "company_results": len(company_profiles),
                "profiles": company_profiles
            }
        except Exception as e:
            logger.error(f"Error searching by company: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "profiles": []
            }
    
    def generate_search_suggestions(
        self,
        industry: Optional[str] = None
    ) -> List[str]:
        """
        Generate search suggestions for finding founders
        
        Parameters:
        - industry: Optional industry focus
        
        Returns:
        - List of search suggestions
        """
        suggestions = [
            "founder, pre-seed",
            "entrepreneur, startup",
            "co-founder, new venture",
            "CEO, stealth startup",
            "founder, seed round"
        ]
        
        # Add industry-specific suggestions if provided
        if industry:
            industry_suggestions = [
                f"founder, {industry}",
                f"startup, {industry}",
                f"{industry} entrepreneur",
                f"building, {industry}"
            ]
            suggestions.extend(industry_suggestions)
        
        return suggestions
    
    def validate_and_format_profiles(
        self,
        profiles: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Validate and format profiles for tracking
        
        Parameters:
        - profiles: List of profile dictionaries
        
        Returns:
        - Tuple of (valid_profiles, error_messages)
        """
        valid_profiles = []
        errors = []
        
        for profile in profiles:
            # Extract LinkedIn URL
            linkedin_url = profile.get('link', '')
            
            # Validate URL
            if not validate_linkedin_url(linkedin_url):
                errors.append(f"Invalid LinkedIn URL format: {linkedin_url}")
                continue
            
            # Format profile for tracking
            formatted_profile = {
                "linkedin_url": linkedin_url,
                "first_name": "",  # Will be filled by API
                "last_name": "",   # Will be filled by API
                "current_title": profile.get('job_title', ''),
                "current_company": profile.get('company_name', ''),
                "tracking_status": "Active"
            }
            
            # Try to extract name
            full_name = profile.get('name', '')
            if full_name:
                # Split name into first and last
                name_parts = full_name.split(' ', 1)
                if len(name_parts) >= 2:
                    formatted_profile["first_name"] = name_parts[0]
                    formatted_profile["last_name"] = name_parts[1]
                else:
                    formatted_profile["first_name"] = name_parts[0]
            
            valid_profiles.append(formatted_profile)
        
        return valid_profiles, errors 