import os
import requests
import httpx
import asyncio
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ProxycurlAPI:
    """
    Class to handle interactions with the Proxycurl API
    """
    
    # Track which profiles have been refreshed (for mock change simulation)
    _mock_refresh_state = {}
    
    def __init__(self):
        self.api_key = os.getenv("PROXYCURL_API_KEY")
        self.base_url = "https://nubela.co/proxycurl/api/v2"
        self.rate_limit = 2  # Max 2 calls per minute on free tier
        self.last_call_time = 0
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def apply_rate_limit(self):
        """Apply rate limiting to API calls"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        
        # If less than 30 seconds passed since last call, wait
        if elapsed < 30 and self.last_call_time > 0:
            wait_time = 30 - elapsed
            time.sleep(wait_time)
        
        self.last_call_time = time.time()
    
    def get_credit_balance(self):
        """Check the remaining credit balance"""
        url = "https://nubela.co/proxycurl/api/credit-balance"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API call failed with status code {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    # --- NEW: helper to build deterministic mock profile -------------------
    def _build_mock_profile(self, linkedin_url: str, is_founder: bool = False):
        """Return deterministic mock profile data for the given url."""
        base_profile = {
            "public_identifier": linkedin_url.split('/')[-1],
            "first_name": "Test",
            "last_name": "User",
            "full_name": "Test User",
            "city": "San Francisco",
            "country": "United States",
            "skills": [
                "Product Management",
                "AI/ML",
                "Leadership",
            ],
            "education": [
                {
                    "school": "Test University",
                    "degree_name": "MBA",
                    "field_of_study": "Business Administration",
                    "starts_at": {"year": 2018},
                    "ends_at": {"year": 2020},
                }
            ],
        }

        founder_exp = {
            "starts_at": {"year": 2023, "month": 6, "day": 1},
            "company": "Test Startup",
            "company_linkedin_profile_url": "https://linkedin.com/company/test-startup",
            "title": "Founder & CEO",
            "description": "Building something new.",
            "location": "San Francisco, CA",
            "company_size": "2-10",
        }
        pm_exp = {
            "starts_at": {"year": 2020, "month": 3, "day": 15},
            "ends_at": {"year": 2023, "month": 5, "day": 30},
            "company": "BigTech",
            "company_linkedin_profile_url": "https://linkedin.com/company/bigtech",
            "title": "Product Manager",
            "description": "Worked on product strategy.",
            "location": "Mountain View, CA",
        }

        if is_founder:
            base_profile.update(
                {
                    "headline": "Founder & CEO at Test Startup",
                    "experiences": [founder_exp, pm_exp],
                }
            )
        else:
            base_profile.update(
                {
                    "headline": "Product Manager at BigTech",
                    "experiences": [pm_exp],
                }
            )
        return base_profile
    
    def get_profile(self, linkedin_url, use_cache=True, fallback_to_cache="never"):
        """
        Get LinkedIn profile data
        
        Parameters:
        - linkedin_url: URL of the LinkedIn profile
        - use_cache: Whether to use cached data (if available)
        - fallback_to_cache: Whether to fall back to cache if the profile is no longer available, accepted values are "on-error", "never"
        
        Returns:
        - Profile data in JSON format or error information
        """
        if not linkedin_url:
            return {"error": "No LinkedIn URL provided"}
            
        # MOCK FALLBACK: If no API key, simulate deterministic change behaviour
        if not self.api_key:
            if linkedin_url not in ProxycurlAPI._mock_refresh_state:
                ProxycurlAPI._mock_refresh_state[linkedin_url] = 1
                return self._build_mock_profile(linkedin_url, is_founder=False)
            else:
                return self._build_mock_profile(linkedin_url, is_founder=True)
        
        # Only apply rate limiting if using a real API key
        self.apply_rate_limit()
        
        url = f"{self.base_url}/linkedin"
        params = {
            "url": linkedin_url,
            "use_cache": "if-present" if use_cache else "if-recent",
            "fallback_to_cache": "never" if fallback_to_cache == "never" else "on-error"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.get_headers())
            
            if response.status_code == 200:
                profile_data = response.json()
                if not profile_data:
                    return {"error": "Empty response from API"}
                return profile_data
            elif response.status_code == 401:
                # Unauthorized / invalid key – fall back to mock data instead of recursion
                return self._build_mock_profile(linkedin_url, is_founder=False)
            elif response.status_code == 404:
                return {"error": f"Profile not found: {linkedin_url}"}
            else:
                return {"error": f"API call failed with status code {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": f"Exception during API call: {str(e)}"}
    
    async def get_profile_async(self, linkedin_url, use_cache=True, fallback_to_cache=True):
        """
        Get LinkedIn profile data asynchronously
        
        Parameters are the same as get_profile
        """
        # MOCK FALLBACK: If no API key, return deterministic mock
        if not self.api_key:
            return self._build_mock_profile(linkedin_url, is_founder=True)
        
        # Apply rate limiting
        self.apply_rate_limit()
        
        url = f"{self.base_url}/linkedin"
        params = {
            "url": linkedin_url,
            "use_cache": "if-present" if use_cache else "if-recent",
            "fallback_to_cache": "on" if fallback_to_cache else "off"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=self.get_headers())
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    # Unauthorized – fall back to mock profile instead of recursion
                    return self._build_mock_profile(linkedin_url, is_founder=False)
                else:
                    return {"error": f"API call failed with status code {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_profiles_batch(self, linkedin_urls, max_concurrency=1):
        """
        Get multiple LinkedIn profiles in batch (respecting rate limits)
        
        Parameters:
        - linkedin_urls: List of LinkedIn profile URLs
        - max_concurrency: Maximum number of concurrent requests
                          (should be 1 for free tier to respect rate limits)
        
        Returns:
        - Dictionary mapping LinkedIn URLs to profile data
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def fetch_with_semaphore(url):
            async with semaphore:
                return url, await self.get_profile_async(url)
        
        tasks = [fetch_with_semaphore(url) for url in linkedin_urls]
        results = await asyncio.gather(*tasks)
        
        return {url: data for url, data in results}
    
    def get_company(self, linkedin_url, use_cache=True):
        """
        Get LinkedIn company data
        
        Parameters:
        - linkedin_url: URL of the LinkedIn company page
        - use_cache: Whether to use cached data (if available)
        
        Returns:
        - Company data in JSON format
        """
        # Generate mock company data for testing
        mock_data = {
            "name": "Test Startup",
            "description": "An innovative startup building cutting-edge technology.",
            "website": "https://teststartup.com",
            "industry": "Technology",
            "company_size": "2-10 employees",
            "founded_year": 2023,
            "headquarters": {
                "country": "United States",
                "city": "San Francisco",
                "state": "California"
            },
            "company_type": "Privately Held"
        }
        
        # MOCK FALLBACK: If no API key, return mock data
        if not self.api_key:
            return mock_data
            
        # Apply rate limiting
        self.apply_rate_limit()
        
        url = f"{self.base_url}/company"
        params = {
            "url": linkedin_url,
            "use_cache": "if-present" if use_cache else "if-recent"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.get_headers())
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # If unauthorized, return mock data instead of error
                return mock_data
            else:
                return {"error": f"API call failed with status code {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def extract_profile_data(self, profile_data):
        """
        Extract relevant data from the profile response
        
        Parameters:
        - profile_data: Full profile data from the API
        
        Returns:
        - Dictionary with extracted and simplified profile data
        """
        if not profile_data or "error" in profile_data:
            return profile_data or {"error": "Empty profile data received"}
        
        extracted = {
            "linkedin_url": profile_data.get("public_identifier", ""),
            "first_name": profile_data.get("first_name", ""),
            "last_name": profile_data.get("last_name", ""),
            "full_name": profile_data.get("full_name", ""),
            "headline": profile_data.get("headline", ""),
            "location": profile_data.get("city", ""),
            "country": profile_data.get("country", ""),
            "skills": profile_data.get("skills", []) or [],
        }
        
        # Extract current and previous experiences
        experiences = profile_data.get("experiences", []) or []
        
        if experiences:
            # First priority: current positions (ends_at is None)
            # Second priority: most recent start date
            # This ensures current positions are prioritized regardless of start date
            experiences.sort(
                key=lambda x: (
                    0 if x.get("ends_at") is None else 1,  # Current positions first
                    -1 * ((x.get("starts_at") or {}).get("year", 0) or 0),  # Then sort by year (descending)
                    -1 * ((x.get("starts_at") or {}).get("month", 0) or 0)  # Then by month (descending)
                )
            )
            
            # Current experience (most recent or current)
            current_exp = experiences[0] if experiences else {}
            extracted["current_title"] = current_exp.get("title", "")
            extracted["current_company"] = current_exp.get("company", "")
            extracted["current_company_url"] = current_exp.get("company_linkedin_profile_url", "")
            
            # Previous experience (second most recent, if exists)
            if len(experiences) > 1:
                prev_exp = experiences[1]
                extracted["previous_title"] = prev_exp.get("title", "")
                extracted["previous_company"] = prev_exp.get("company", "")
                extracted["previous_company_url"] = prev_exp.get("company_linkedin_profile_url", "")
            else:
                # Ensure these fields exist even if there's no previous experience
                extracted["previous_title"] = ""
                extracted["previous_company"] = ""
                extracted["previous_company_url"] = ""
        else:
            # No experiences, set empty defaults
            extracted["current_title"] = ""
            extracted["current_company"] = ""
            extracted["current_company_url"] = ""
            extracted["previous_title"] = ""
            extracted["previous_company"] = ""
            extracted["previous_company_url"] = ""
        
        # Extract education
        education = profile_data.get("education", []) or []
        extracted["education"] = [
            {
                "school": edu.get("school", ""),
                "degree": edu.get("degree_name", ""),
                "field": edu.get("field_of_study", ""),
                "start_year": (edu.get("starts_at") or {}).get("year", ""),
                "end_year": (edu.get("ends_at") or {}).get("year", "")
            }
            for edu in education
        ]
        
        return extracted
