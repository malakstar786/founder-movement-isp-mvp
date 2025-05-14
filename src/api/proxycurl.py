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
    
    def get_profile(self, linkedin_url, use_cache=True, fallback_to_cache=True):
        """
        Get LinkedIn profile data
        
        Parameters:
        - linkedin_url: URL of the LinkedIn profile
        - use_cache: Whether to use cached data (if available)
        - fallback_to_cache: Whether to fall back to cache if the profile is no longer available
        
        Returns:
        - Profile data in JSON format
        """
        # Apply rate limiting
        self.apply_rate_limit()
        
        url = f"{self.base_url}/linkedin"
        params = {
            "url": linkedin_url,
            "use_cache": "if-present" if use_cache else "if-recent",
            "fallback_to_cache": "on" if fallback_to_cache else "off"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API call failed with status code {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_profile_async(self, linkedin_url, use_cache=True, fallback_to_cache=True):
        """
        Get LinkedIn profile data asynchronously
        
        Parameters are the same as get_profile
        """
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
        if "error" in profile_data:
            return profile_data
        
        extracted = {
            "linkedin_url": profile_data.get("public_identifier", ""),
            "first_name": profile_data.get("first_name", ""),
            "last_name": profile_data.get("last_name", ""),
            "full_name": profile_data.get("full_name", ""),
            "headline": profile_data.get("headline", ""),
            "location": profile_data.get("city", ""),
            "country": profile_data.get("country", ""),
            "skills": profile_data.get("skills", []),
        }
        
        # Extract current and previous experiences
        experiences = profile_data.get("experiences", [])
        
        if experiences:
            # Sort by start date (most recent first)
            experiences.sort(
                key=lambda x: (
                    x.get("starts_at", {}).get("year", 0),
                    x.get("starts_at", {}).get("month", 0),
                ),
                reverse=True
            )
            
            # Current experience (most recent)
            current_exp = experiences[0]
            extracted["current_title"] = current_exp.get("title", "")
            extracted["current_company"] = current_exp.get("company", "")
            extracted["current_company_url"] = current_exp.get("company_linkedin_profile_url", "")
            
            # Previous experience (second most recent, if exists)
            if len(experiences) > 1:
                prev_exp = experiences[1]
                extracted["previous_title"] = prev_exp.get("title", "")
                extracted["previous_company"] = prev_exp.get("company", "")
                extracted["previous_company_url"] = prev_exp.get("company_linkedin_profile_url", "")
        
        # Extract education
        education = profile_data.get("education", [])
        extracted["education"] = [
            {
                "school": edu.get("school", ""),
                "degree": edu.get("degree_name", ""),
                "field": edu.get("field_of_study", ""),
                "start_year": edu.get("starts_at", {}).get("year", ""),
                "end_year": edu.get("ends_at", {}).get("year", "")
            }
            for edu in education
        ]
        
        return extracted
