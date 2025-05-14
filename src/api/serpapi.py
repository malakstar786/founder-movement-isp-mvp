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
        # Generate mock data for testing
        mock_data = {
            "search_metadata": {
                "id": "mock_search_id",
                "status": "Success",
                "created_at": "2023-12-26 12:05:31 UTC",
                "processed_at": "2023-12-26 12:05:31 UTC",
                "total_time_taken": 1.5
            },
            "search_parameters": {
                "engine": "linkedin_profiles",
                "keywords": keywords,
                "location": location or "United States"
            },
            "profiles": [
                {
                    "name": "Test Founder",
                    "link": "https://www.linkedin.com/in/test-founder",
                    "job_title": "Founder & CEO at Tech Startup",
                    "description": "Building innovative solutions | Ex-Google | YC Alumni",
                    "location": location or "San Francisco Bay Area",
                    "image": "https://media.licdn.com/dms/image/mock_image_1"
                },
                {
                    "name": "Jane Innovator",
                    "link": "https://www.linkedin.com/in/jane-innovator",
                    "job_title": "Co-founder at Stealth Startup",
                    "description": "Working on the future of AI | Previously Director at Microsoft",
                    "location": location or "New York, NY",
                    "image": "https://media.licdn.com/dms/image/mock_image_2"
                },
                {
                    "name": "Alex Tech",
                    "link": "https://www.linkedin.com/in/alex-tech",
                    "job_title": "Founder, Building something new",
                    "description": "Serial entrepreneur | AI & ML enthusiast | Stanford MBA",
                    "location": location or "Austin, Texas",
                    "image": "https://media.licdn.com/dms/image/mock_image_3"
                }
            ],
            "pagination": {
                "current": page,
                "next": page + 1,
                "other_pages": {
                    "2": "page 2 link",
                    "3": "page 3 link"
                }
            }
        }
        
        # If no API key or called with test keywords, return mock data
        if not self.api_key or keywords.lower() == "test":
            return mock_data
        
        params = {
            "engine": "google",
            "q": f'site:linkedin.com/in/ {keywords}',
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
            elif response.status_code == 401:
                # If unauthorized, return mock data
                return mock_data
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
        
        # Handle mock data (our own structure)
        if "profiles" in search_results:
            profiles = search_results.get("profiles", [])
            extracted = []
            for profile in profiles:
                extracted.append({
                    "name": profile.get("name", ""),
                    "job_title": profile.get("job_title", ""),
                    "company": self.parse_company_from_job_title(profile.get("job_title", "")),
                    "location": profile.get("location", ""),
                    "description": profile.get("description", ""),
                    "link": profile.get("link", ""),
                    "image": profile.get("image", "")
                })
            return extracted
        
        # Handle real SerpApi response (organic_results)
        extracted = []
        for result in search_results.get("organic_results", []):
            title = result.get("title", "")
            # Try to split title into name and job/company
            name = title.split(" - ")[0] if " - " in title else title
            job_and_company = " - ".join(title.split(" - ")[1:]) if " - " in title else ""
            job_title = job_and_company
            company = ""
            location = ""
            # Try to extract company and location from rich_snippet
            rich = result.get("rich_snippet", {})
            if rich and "top" in rich and "extensions" in rich["top"]:
                extensions = rich["top"]["extensions"]
                # Heuristically assign location and company
                for ext in extensions:
                    if any(city in ext.lower() for city in ["san ", "new york", "bay area", "united states", "california", "london", "area", "denver", "berkeley", "austin", "united kingdom"]):
                        location = ext
                    elif any(role in ext.lower() for role in ["founder", "ceo", "co-founder", "stealth", "startup"]):
                        job_title = ext
                    else:
                        company = ext
            # Fallback: try to parse company from job_title
            if not company:
                company = self.parse_company_from_job_title(job_title)
            extracted.append({
                "name": name,
                "job_title": job_title,
                "company": company,
                "location": location,
                "description": result.get("snippet", ""),
                "link": result.get("link", ""),
                "image": ""  # SerpApi does not provide image in organic_results
            })
        return extracted
    
    def get_usage_info(self):
        """
        Get SerpApi usage information
        
        Returns:
        - JSON response with account information
        """
        # Mock usage data
        mock_usage = {
            "plan_searches_left": 100,
            "plan_name": "Test Plan",
            "account_email": "test@example.com",
            "total_searches_used": 0
        }
        
        # If no API key, return mock usage data
        if not self.api_key:
            return mock_usage
            
        params = {
            "api_key": self.api_key
        }
        
        try:
            response = requests.get("https://serpapi.com/account", params=params)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # If unauthorized, return mock usage data
                return mock_usage
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
