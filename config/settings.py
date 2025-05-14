import os
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

class Settings:
    """
    Class to manage application settings
    """
    
    # API Keys
    PROXYCURL_API_KEY = os.getenv("PROXYCURL_API_KEY", "")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Application settings
    FOUNDER_KEYWORDS = os.getenv("FOUNDER_KEYWORDS", "Founder,Co-founder,CEO,Chief Executive Officer,Entrepreneur,Creator,Stealth,Building")
    CHECK_FREQUENCY = os.getenv("CHECK_FREQUENCY", "Daily")
    
    # API Limits
    PROXYCURL_RATE_LIMIT = 2  # Max 2 calls per minute on free tier
    SERPAPI_MONTHLY_LIMIT = 100  # Free tier limit
    
    # OpenAI Configuration
    OPENAI_MODEL = "gpt-4o-mini"
    OPENAI_TEMPERATURE = 0.7
    
    @classmethod
    def get_founder_keywords(cls) -> List[str]:
        """
        Get the list of founder keywords
        
        Returns:
        - List of keywords
        """
        return [k.strip() for k in cls.FOUNDER_KEYWORDS.split(",")]
    
    @classmethod
    def has_api_keys(cls) -> bool:
        """
        Check if the required API keys are set
        """
        return all([
            cls.PROXYCURL_API_KEY,
            cls.SERPAPI_API_KEY,
            cls.OPENAI_API_KEY,
        ])
    
    @classmethod
    def get_missing_api_keys(cls) -> List[str]:
        """
        Get a list of missing API keys
        
        Returns:
        - List of names of missing API keys
        """
        missing = []
        
        if not cls.PROXYCURL_API_KEY:
            missing.append("Proxycurl API Key")
        
        if not cls.SERPAPI_API_KEY:
            missing.append("SerpApi Key")
        
        if not cls.OPENAI_API_KEY:
            missing.append("OpenAI API Key")
        
        return missing
    
    @classmethod
    def update_setting(cls, key: str, value: Any) -> bool:
        """
        Update a setting value
        
        Parameters:
        - key: Setting name to update
        - value: New value for the setting
        
        Returns:
        - Boolean indicating success
        """
        # Make sure the setting exists
        if not hasattr(cls, key):
            return False
        
        # Update the setting
        setattr(cls, key, value)
        
        # Also update the environment variable if it matches
        env_var = key
        if hasattr(os.environ, env_var):
            os.environ[env_var] = str(value)
        
        return True
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Convert settings to a dictionary
        
        Returns:
        - Dictionary of settings
        """
        return {
            "proxycurl_api_key": cls.PROXYCURL_API_KEY,
            "serpapi_api_key": cls.SERPAPI_API_KEY,
            "openai_api_key": cls.OPENAI_API_KEY,
            "founder_keywords": cls.FOUNDER_KEYWORDS,
            "check_frequency": cls.CHECK_FREQUENCY,
            "proxycurl_rate_limit": cls.PROXYCURL_RATE_LIMIT,
            "serpapi_monthly_limit": cls.SERPAPI_MONTHLY_LIMIT,
            "openai_model": cls.OPENAI_MODEL,
            "openai_temperature": cls.OPENAI_TEMPERATURE
        }
