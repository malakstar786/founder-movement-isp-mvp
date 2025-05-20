import httpx
import os
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "fresh-linkedin-profile-data.p.rapidapi.com"

async def get_linkedin_profile_data(linkedin_url: str) -> dict:
    """
    Fetches LinkedIn profile data using the Fresh LinkedIn Profile Data API on RapidAPI.
    """
    if not RAPIDAPI_KEY:
        raise ValueError("RAPIDAPI_KEY not found in environment variables.")

    url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile"
    
    # Set desired parameters, can be adjusted as needed
    # For now, keeping it similar to the example provided by the user
    # but enabling skills as it's useful for founder analysis.
    params = {
        "linkedin_url": linkedin_url,
        "include_skills": "true",
        "include_certifications": "false",
        "include_publications": "false",
        "include_honors": "false",
        "include_volunteers": "false",
        "include_projects": "false",
        "include_patents": "false",
        "include_courses": "false",
        "include_organizations": "false",
        "include_profile_status": "true", # Useful for verification status
        "include_company_public_url": "false" 
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            return response.json()
        except httpx.HTTPStatusError as e:
            # Log or handle specific HTTP errors
            print(f"HTTP error occurred: {e}")
            # You might want to return a specific error structure or re-raise
            return {"error": True, "status_code": e.response.status_code, "message": str(e)}
        except httpx.RequestError as e:
            # Log or handle other request errors (e.g., network issues)
            print(f"Request error occurred: {e}")
            return {"error": True, "message": f"Request failed: {str(e)}"}
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return {"error": True, "message": f"An unexpected error: {str(e)}"}

if __name__ == '__main__':
    # Example usage (for testing this module directly)
    import asyncio

    async def main():
        # Test with a sample LinkedIn URL
        # test_url = "https://www.linkedin.com/in/cjfollini/" 
        test_url = "https://www.linkedin.com/in/imranaly/" # Using a profile we've tested
        print(f"Fetching profile for: {test_url}")
        data = await get_linkedin_profile_data(test_url)
        
        if data and not data.get("error"):
            print("Successfully fetched data:")
            # print(data.get("data", {}).get("full_name"))
            # print(data.get("data", {}).get("headline"))
            # print(f"Current Company: {data.get('data', {}).get('company')}")
            # print(f"Current Title: {data.get('data', {}).get('job_title')}")
            import json
            print(json.dumps(data, indent=2))
        else:
            print("Failed to fetch data.")
            if data and data.get("error"):
                print(f"Error details: {data.get('message')}")

    asyncio.run(main()) 