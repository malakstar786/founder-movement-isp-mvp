from datetime import datetime
from typing import Dict, Any, Optional

class Change:
    """
    Model class to represent a career change
    """
    
    def __init__(
        self,
        linkedin_url: str,
        old_title: str = "",
        new_title: str = "",
        old_company: str = "",
        new_company: str = "",
        detected_date: Optional[str] = None,
        is_founder_change: bool = False,
        ai_insight: str = "",
        notification_sent: bool = False,
        change_id: Optional[int] = None,
    ):
        self.change_id = change_id
        self.linkedin_url = linkedin_url
        self.old_title = old_title
        self.new_title = new_title
        self.old_company = old_company
        self.new_company = new_company
        self.detected_date = detected_date or datetime.now().isoformat()
        self.is_founder_change = is_founder_change
        self.ai_insight = ai_insight
        self.notification_sent = notification_sent
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Change':
        """
        Create a Change instance from a dictionary
        
        Parameters:
        - data: Dictionary containing change data
        
        Returns:
        - Change instance
        """
        # Convert change_id to integer if present
        change_id = None
        if 'change_id' in data and data['change_id']:
            try:
                change_id = int(data['change_id'])
            except (ValueError, TypeError):
                change_id = None
        
        # Convert is_founder_change string to boolean
        is_founder_change = False
        if 'is_founder_change' in data:
            if isinstance(data['is_founder_change'], bool):
                is_founder_change = data['is_founder_change']
            elif isinstance(data['is_founder_change'], str):
                is_founder_change = data['is_founder_change'].lower() == 'true'
        
        # Convert notification_sent string to boolean
        notification_sent = False
        if 'notification_sent' in data:
            if isinstance(data['notification_sent'], bool):
                notification_sent = data['notification_sent']
            elif isinstance(data['notification_sent'], str):
                notification_sent = data['notification_sent'].lower() == 'true'
        
        return cls(
            linkedin_url=data.get('linkedin_url', ''),
            old_title=data.get('old_title', ''),
            new_title=data.get('new_title', ''),
            old_company=data.get('old_company', ''),
            new_company=data.get('new_company', ''),
            detected_date=data.get('detected_date', None),
            is_founder_change=is_founder_change,
            ai_insight=data.get('ai_insight', ''),
            notification_sent=notification_sent,
            change_id=change_id,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Change instance to a dictionary
        
        Returns:
        - Dictionary representation of the change
        """
        result = {
            'linkedin_url': self.linkedin_url,
            'old_title': self.old_title,
            'new_title': self.new_title,
            'old_company': self.old_company,
            'new_company': self.new_company,
            'detected_date': self.detected_date,
            'is_founder_change': str(self.is_founder_change).lower(),
            'ai_insight': self.ai_insight,
            'notification_sent': str(self.notification_sent).lower(),
        }
        
        # Only include change_id if it's set
        if self.change_id is not None:
            result['change_id'] = str(self.change_id)
        
        return result
    
    @classmethod
    def from_profile_comparison(
        cls, 
        linkedin_url: str,
        old_profile: Dict[str, Any],
        new_profile: Dict[str, Any],
        is_founder: bool = False,
        ai_insight: str = ""
    ) -> 'Change':
        """
        Create a Change instance from comparing old and new profile data
        
        Parameters:
        - linkedin_url: LinkedIn URL of the profile
        - old_profile: Dictionary containing previous profile data
        - new_profile: Dictionary containing current profile data
        - is_founder: Boolean indicating if this is a founder-related change
        - ai_insight: AI-generated insight about the change
        
        Returns:
        - Change instance
        """
        return cls(
            linkedin_url=linkedin_url,
            old_title=old_profile.get('current_title', ''),
            new_title=new_profile.get('current_title', ''),
            old_company=old_profile.get('current_company', ''),
            new_company=new_profile.get('current_company', ''),
            is_founder_change=is_founder,
            ai_insight=ai_insight,
        )
    
    def is_title_change(self) -> bool:
        """
        Check if this change involves a title change
        
        Returns:
        - Boolean indicating if there was a title change
        """
        return (
            self.old_title != self.new_title and
            self.old_title and self.new_title
        )
    
    def is_company_change(self) -> bool:
        """
        Check if this change involves a company change
        
        Returns:
        - Boolean indicating if there was a company change
        """
        return (
            self.old_company != self.new_company and
            self.old_company and self.new_company
        )
    
    def get_change_description(self) -> str:
        """
        Get a human-readable description of the change
        
        Returns:
        - String describing the change
        """
        if self.is_title_change() and self.is_company_change():
            return f"Changed from {self.old_title} at {self.old_company} to {self.new_title} at {self.new_company}"
        elif self.is_title_change():
            return f"Changed role from {self.old_title} to {self.new_title} at {self.new_company}"
        elif self.is_company_change():
            return f"Moved from {self.old_company} to {self.new_company} as {self.new_title}"
        else:
            return "No significant change detected"
