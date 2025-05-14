import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SerpAPI:
    """
    Class to handle interactions with the SerpApi for LinkedIn profile discovery
    """
    
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.base_url = "https://serpapi.com/search"
    
    def search_linkedin_profiles(self, keywords, location=None, page=1):
        """
        Search for LinkedIn profiles based on keywords and location
        
        Parameters:
        - keywords: Search terms (required)
        - location: Geographic location (optional)
        - page: Page number for pagination (default: 1)
        
        Returns:
        - JSON response with search results
        """
        params = {
            "engine": "linkedin_profiles",
            "keywords": keywords,
            "page": page,
            "api_key": self.api_key
        }
        
        # Add location if provided
        if location:
            params["location"] = location
        
        try:
            response = requests.get(self.base_url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API call failed with status code {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def extract_profiles(self, search_results):
        """
        Extract profile information from search results
        
        Parameters:
        - search_results: Full search results from the API
        
        Returns:
        - List of dictionaries with profile information
        """
        if "error" in search_results:
            return []
        
        profiles = search_results.get("profiles", [])
        extracted = []
        
        for profile in profiles:
            # Extract relevant profile information
            extracted.append({
                "name": profile.get("name", ""),
                "link": profile.get("link", ""),
                "job_title": profile.get("job_title", ""),
                "location": profile.get("location", ""),
                "description": profile.get("description", ""),
                "image": profile.get("image", "")
            })
        
        return extracted
    
    def get_usage_info(self):
        """
        Get SerpApi usage information
        
        Returns:
        - JSON response with account information
        """
        params = {
            "api_key": self.api_key
        }
        
        try:
            response = requests.get("https://serpapi.com/account", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API call failed with status code {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def parse_company_from_job_title(self, job_title):
        """
        Attempt to extract company name from job title
        
        Parameters:
        - job_title: Job title string (e.g., "Founder at TechCorp")
        
        Returns:
        - Company name or empty string if not found
        """
        if not job_title:
            return ""
        
        # Common patterns: "Title at Company" or "Title @ Company"
        if " at " in job_title:
            return job_title.split(" at ")[1].strip()
        elif " @ " in job_title:
            return job_title.split(" @ ")[1].strip()
        
        return ""
    
    def detect_founder_in_title(self, job_title):
        """
        Detect if a job title indicates a founder role
        
        Parameters:
        - job_title: Job title string
        
        Returns:
        - Boolean indicating if this is likely a founder
        """
        if not job_title:
            return False
        
        # Convert to lowercase for case-insensitive matching
        title_lower = job_title.lower()
        
        # Keywords that indicate founder roles
        founder_keywords = [
            "founder", 
            "co-founder", 
            "cofounder", 
            "ceo", 
            "chief executive", 
            "owner",
            "entrepreneur",
            "creator"
        ]
        
        # Keywords that indicate stealth or new startups
        stealth_keywords = [
            "stealth",
            "building",
            "launching",
            "starting"
        ]
        
        # Check if any founder keywords are in the title
        for keyword in founder_keywords:
            if keyword in title_lower:
                return True
        
        # Check if any stealth keywords are in the title
        for keyword in stealth_keywords:
            if keyword in title_lower:
                return True
        
        return False
