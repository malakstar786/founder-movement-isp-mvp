from datetime import datetime
from typing import Dict, Any, Optional

class Outreach:
    """
    Model class to represent an outreach attempt to a founder
    """
    
    def __init__(
        self,
        linkedin_url: str,
        change_id: Optional[int] = None,
        outreach_date: Optional[str] = None,
        outreach_method: str = "Email",
        response_received: bool = False,
        notes: str = "",
        follow_up_date: Optional[str] = None,
        outreach_id: Optional[int] = None,
    ):
        self.outreach_id = outreach_id
        self.linkedin_url = linkedin_url
        self.change_id = change_id
        self.outreach_date = outreach_date or datetime.now().isoformat()
        self.outreach_method = outreach_method
        self.response_received = response_received
        self.notes = notes
        self.follow_up_date = follow_up_date
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Outreach':
        """
        Create an Outreach instance from a dictionary
        
        Parameters:
        - data: Dictionary containing outreach data
        
        Returns:
        - Outreach instance
        """
        # Convert outreach_id to integer if present
        outreach_id = None
        if 'outreach_id' in data and data['outreach_id']:
            try:
                outreach_id = int(data['outreach_id'])
            except (ValueError, TypeError):
                outreach_id = None
        
        # Convert change_id to integer if present
        change_id = None
        if 'change_id' in data and data['change_id']:
            try:
                change_id = int(data['change_id'])
            except (ValueError, TypeError):
                change_id = None
        
        # Convert response_received string to boolean
        response_received = False
        if 'response_received' in data:
            if isinstance(data['response_received'], bool):
                response_received = data['response_received']
            elif isinstance(data['response_received'], str):
                response_received = data['response_received'].lower() == 'true'
        
        return cls(
            linkedin_url=data.get('linkedin_url', ''),
            change_id=change_id,
            outreach_date=data.get('outreach_date', None),
            outreach_method=data.get('outreach_method', 'Email'),
            response_received=response_received,
            notes=data.get('notes', ''),
            follow_up_date=data.get('follow_up_date', None),
            outreach_id=outreach_id,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Outreach instance to a dictionary
        
        Returns:
        - Dictionary representation of the outreach
        """
        result = {
            'linkedin_url': self.linkedin_url,
            'outreach_date': self.outreach_date,
            'outreach_method': self.outreach_method,
            'response_received': str(self.response_received).lower(),
            'notes': self.notes,
        }
        
        # Only include optional fields if they're set
        if self.outreach_id is not None:
            result['outreach_id'] = str(self.outreach_id)
        
        if self.change_id is not None:
            result['change_id'] = str(self.change_id)
        
        if self.follow_up_date:
            result['follow_up_date'] = self.follow_up_date
        
        return result
    
    def is_successful(self) -> bool:
        """
        Check if the outreach was successful
        
        Returns:
        - Boolean indicating if a response was received
        """
        return self.response_received
    
    def needs_follow_up(self) -> bool:
        """
        Check if the outreach needs a follow-up
        
        Returns:
        - Boolean indicating if follow-up is needed
        """
        # If already received a response, no follow-up needed
        if self.response_received:
            return False
        
        # If no follow-up date is set, assume no follow-up needed
        if not self.follow_up_date:
            return False
        
        # Check if follow-up date is in the past
        try:
            follow_up = datetime.fromisoformat(self.follow_up_date)
            now = datetime.now()
            return follow_up <= now
        except (ValueError, TypeError):
            return False
    
    def mark_as_received(self, notes: Optional[str] = None) -> None:
        """
        Mark the outreach as having received a response
        
        Parameters:
        - notes: Optional notes about the response
        """
        self.response_received = True
        
        if notes:
            # Append the new notes to existing notes
            if self.notes:
                self.notes += f"\n\n{notes}"
            else:
                self.notes = notes
    
    def set_follow_up(self, follow_up_date: str, notes: Optional[str] = None) -> None:
        """
        Set a follow-up date for the outreach
        
        Parameters:
        - follow_up_date: Date for the follow-up in ISO format
        - notes: Optional notes about the follow-up
        """
        self.follow_up_date = follow_up_date
        
        if notes:
            # Append the new notes to existing notes
            if self.notes:
                self.notes += f"\n\nFollow-up notes: {notes}"
            else:
                self.notes = f"Follow-up notes: {notes}"
