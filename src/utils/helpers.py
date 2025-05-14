import re
import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

def parse_linkedin_id_from_url(url: str) -> Optional[str]:
    """
    Extract the LinkedIn ID from a profile URL
    
    Parameters:
    - url: LinkedIn profile URL
    
    Returns:
    - LinkedIn ID or None if not found
    """
    if not url:
        return None
    
    # Pattern to match the ID in a LinkedIn profile URL
    pattern = r'linkedin\.com/in/([\w\-_]+)'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    
    return None

def parse_company_id_from_url(url: str) -> Optional[str]:
    """
    Extract the company ID from a LinkedIn company URL
    
    Parameters:
    - url: LinkedIn company URL
    
    Returns:
    - Company ID or None if not found
    """
    if not url:
        return None
    
    # Pattern to match the ID in a LinkedIn company URL
    pattern = r'linkedin\.com/company/([\w\-_]+)'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    
    return None

def detect_founder_keywords(text: str, keywords: List[str]) -> bool:
    """
    Detect if any founder keywords are present in text
    
    Parameters:
    - text: Text to search in
    - keywords: List of keywords to search for
    
    Returns:
    - Boolean indicating if any keywords were found
    """
    if not text or not keywords:
        return False
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Check if any keywords are in the text
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True
    
    return False

def csv_to_linkedin_urls(csv_file_path: str) -> List[str]:
    """
    Extract LinkedIn URLs from a CSV file
    
    Parameters:
    - csv_file_path: Path to the CSV file
    
    Returns:
    - List of LinkedIn URLs
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        
        # Check if the CSV has a linkedin_url column
        if 'linkedin_url' not in df.columns:
            return []
        
        # Extract URLs
        urls = df['linkedin_url'].tolist()
        
        # Convert to strings and clean up
        urls = [str(url).strip() for url in urls if url]
        
        return urls
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        return []

def save_json(data: Any, file_path: str) -> bool:
    """
    Save data to a JSON file
    
    Parameters:
    - data: Data to save
    - file_path: Path to save the JSON file
    
    Returns:
    - Boolean indicating success
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save data to JSON file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving JSON: {str(e)}")
        return False

def load_json(file_path: str) -> Optional[Any]:
    """
    Load data from a JSON file
    
    Parameters:
    - file_path: Path to the JSON file
    
    Returns:
    - Loaded data or None if error
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return None
        
        # Load data from JSON file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return data
    except Exception as e:
        print(f"Error loading JSON: {str(e)}")
        return None

def format_iso_date(iso_date: str, format_str: str = "%Y-%m-%d") -> str:
    """
    Format an ISO date string
    
    Parameters:
    - iso_date: ISO format date string
    - format_str: Output format string
    
    Returns:
    - Formatted date string
    """
    try:
        # Parse ISO date
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        
        # Format date
        return dt.strftime(format_str)
    except (ValueError, TypeError, AttributeError):
        return iso_date
