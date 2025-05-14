import re
import pandas as pd
from typing import Tuple, List, Dict, Any

def validate_linkedin_url(url: str) -> bool:
    """
    Validate a LinkedIn profile URL
    
    Parameters:
    - url: LinkedIn URL to validate
    
    Returns:
    - Boolean indicating if the URL is valid
    """
    # Check if URL is None or empty
    if not url:
        return False
    
    # Regular expression pattern for LinkedIn profile URLs
    pattern = r'^https?://(www\.)?linkedin\.com/in/[\w\-_]+/?$'
    
    # Check if the URL matches the pattern
    return bool(re.match(pattern, url))

def validate_linkedin_company_url(url: str) -> bool:
    """
    Validate a LinkedIn company URL
    
    Parameters:
    - url: LinkedIn company URL to validate
    
    Returns:
    - Boolean indicating if the URL is valid
    """
    # Check if URL is None or empty
    if not url:
        return False
    
    # Regular expression pattern for LinkedIn company URLs
    pattern = r'^https?://(www\.)?linkedin\.com/company/[\w\-_]+/?$'
    
    # Check if the URL matches the pattern
    return bool(re.match(pattern, url))

def validate_csv_with_linkedin_urls(csv_data: str) -> Tuple[List[str], List[str]]:
    """
    Validate a CSV containing LinkedIn URLs
    
    Parameters:
    - csv_data: String containing CSV data
    
    Returns:
    - Tuple of (valid_urls, error_messages)
    """
    try:
        # Read CSV data
        df = pd.read_csv(pd.StringIO(csv_data))
        
        # Check if the CSV has a linkedin_url column
        if 'linkedin_url' not in df.columns:
            return [], ["CSV must contain a 'linkedin_url' column"]
        
        valid_urls = []
        errors = []
        
        # Validate each URL
        for i, row in df.iterrows():
            url = row['linkedin_url']
            
            # Convert to string if not already
            if not isinstance(url, str):
                url = str(url).strip()
            
            # Validate the URL
            if validate_linkedin_url(url):
                valid_urls.append(url)
            else:
                errors.append(f"Row {i+2}: Invalid LinkedIn URL format: {url}")
        
        return valid_urls, errors
    
    except Exception as e:
        return [], [f"Error processing CSV: {str(e)}"]

def validate_api_keys(keys: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate that API keys are present
    
    Parameters:
    - keys: Dictionary of API keys
    
    Returns:
    - Tuple of (all_valid, missing_keys)
    """
    required_keys = [
        "proxycurl_api_key",
        "serpapi_api_key",
        "openai_api_key",
        "google_sheet_id",
        "google_service_account_file"
    ]
    
    missing = []
    
    for key in required_keys:
        if key not in keys or not keys[key]:
            missing.append(key)
    
    return len(missing) == 0, missing

def validate_founder_keywords(keywords: str) -> Tuple[bool, List[str]]:
    """
    Validate and parse founder keywords
    
    Parameters:
    - keywords: Comma-separated list of keywords
    
    Returns:
    - Tuple of (is_valid, parsed_keywords)
    """
    if not keywords:
        return False, []
    
    # Split by comma and trim whitespace
    parsed = [k.strip() for k in keywords.split(',')]
    
    # Filter out empty strings
    parsed = [k for k in parsed if k]
    
    # Check if we have at least one valid keyword
    is_valid = len(parsed) > 0
    
    return is_valid, parsed
