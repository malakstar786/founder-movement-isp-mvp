from datetime import datetime
from typing import List, Dict, Optional, Any

class Profile:
    """
    Model class to represent a LinkedIn profile
    """
    
    def __init__(
        self,
        linkedin_url: str,
        first_name: str = "",
        last_name: str = "",
        current_title: str = "",
        current_company: str = "",
        previous_title: str = "",
        previous_company: str = "",
        last_checked_date: Optional[str] = None,
        tracking_status: str = "Active",
        outreach_status: str = "Not contacted",
        skills: List[str] = None,
        education: List[Dict[str, Any]] = None,
    ):
        self.linkedin_url = linkedin_url
        self.first_name = first_name
        self.last_name = last_name
        self.current_title = current_title
        self.current_company = current_company
        self.previous_title = previous_title
        self.previous_company = previous_company
        self.last_checked_date = last_checked_date or datetime.now().isoformat()
        self.tracking_status = tracking_status
        self.outreach_status = outreach_status
        self.skills = skills or []
        self.education = education or []
    
    @property
    def full_name(self) -> str:
        """Get the full name of the profile"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """
        Create a Profile instance from a dictionary
        
        Parameters:
        - data: Dictionary containing profile data
        
        Returns:
        - Profile instance
        """
        if not data:
            # Return a default profile with empty values if data is None or empty
            return cls(linkedin_url="")
            
        return cls(
            linkedin_url=data.get('linkedin_url', ''),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            current_title=data.get('current_title', ''),
            current_company=data.get('current_company', ''),
            previous_title=data.get('previous_title', ''),
            previous_company=data.get('previous_company', ''),
            last_checked_date=data.get('last_checked_date', None),
            tracking_status=data.get('tracking_status', 'Active'),
            outreach_status=data.get('outreach_status', 'Not contacted'),
            skills=data.get('skills', []) or [],
            education=data.get('education', []) or [],
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Profile instance to a dictionary
        
        Returns:
        - Dictionary representation of the profile
        """
        return {
            'linkedin_url': self.linkedin_url,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'current_title': self.current_title,
            'current_company': self.current_company,
            'previous_title': self.previous_title,
            'previous_company': self.previous_company,
            'last_checked_date': self.last_checked_date,
            'tracking_status': self.tracking_status,
            'outreach_status': self.outreach_status,
            'skills': self.skills,
            'education': self.education,
        }
    
    def has_changed_roles(self, previous_data: Dict[str, Any]) -> bool:
        """
        Check if the profile has changed roles
        
        Parameters:
        - previous_data: Dictionary containing previous profile data
        
        Returns:
        - Boolean indicating if a role change was detected
        """
        if not previous_data:
            return False
        
        # Check for changes in title or company
        title_changed = (
            previous_data.get('current_title', '') != self.current_title and
            self.current_title
        )
        company_changed = (
            previous_data.get('current_company', '') != self.current_company and
            self.current_company
        )
        
        return title_changed or company_changed
    
    def is_founder(self) -> bool:
        """
        Check if the profile is likely a founder based on current title
        
        Returns:
        - Boolean indicating if the profile is likely a founder
        """
        if not self.current_title:
            return False
        
        # Convert to lowercase for case-insensitive matching
        title_lower = self.current_title.lower()
        
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
