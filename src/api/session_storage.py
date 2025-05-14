import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional

class SessionStorage:
    """
    Class to handle in-memory session storage as a replacement for Google Sheets
    """
    
    @staticmethod
    def initialize_storage():
        """Initialize session storage if it doesn't exist"""
        if 'profiles' not in st.session_state:
            st.session_state['profiles'] = []
        
        if 'changes' not in st.session_state:
            st.session_state['changes'] = []
        
        if 'outreach' not in st.session_state:
            st.session_state['outreach'] = []
    
    @staticmethod
    def add_profile(profile_data: Dict[str, Any]) -> bool:
        """
        Add a profile to session storage
        
        Parameters:
        - profile_data: Dictionary containing profile information
        
        Returns:
        - Boolean indicating success or failure
        """
        SessionStorage.initialize_storage()
        
        # Check if profile already exists
        linkedin_url = profile_data.get("linkedin_url", "")
        existing_profiles = [p for p in st.session_state['profiles'] if p.get("linkedin_url") == linkedin_url]
        
        if existing_profiles:
            # Update existing profile
            index = st.session_state['profiles'].index(existing_profiles[0])
            profile_data["last_checked_date"] = datetime.now().isoformat()
            st.session_state['profiles'][index] = profile_data
        else:
            # Add new profile
            profile_data["last_checked_date"] = datetime.now().isoformat()
            profile_data["tracking_status"] = "Active"
            profile_data["outreach_status"] = "Not contacted"
            st.session_state['profiles'].append(profile_data)
        
        return True
    
    @staticmethod
    def get_profile(linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific profile from session storage
        
        Parameters:
        - linkedin_url: LinkedIn URL to look up
        
        Returns:
        - Dictionary containing profile information or None if not found
        """
        SessionStorage.initialize_storage()
        
        for profile in st.session_state['profiles']:
            if profile.get("linkedin_url") == linkedin_url:
                return profile
        
        return None
    
    @staticmethod
    def get_all_profiles() -> List[Dict[str, Any]]:
        """
        Get all profiles from session storage
        
        Returns:
        - List of dictionaries containing profile information
        """
        SessionStorage.initialize_storage()
        return st.session_state['profiles']
    
    @staticmethod
    def record_change(change_data: Dict[str, Any]) -> bool:
        """
        Record a career change in session storage
        
        Parameters:
        - change_data: Dictionary containing change information
        
        Returns:
        - Boolean indicating success or failure
        """
        SessionStorage.initialize_storage()
        
        # Generate a unique change_id if not provided
        if "change_id" not in change_data:
            change_ids = [int(c.get("change_id", 0)) for c in st.session_state['changes']]
            next_change_id = max(change_ids, default=0) + 1
            change_data["change_id"] = next_change_id
        
        # Add detected_date if not provided
        if "detected_date" not in change_data:
            change_data["detected_date"] = datetime.now().isoformat()
        
        st.session_state['changes'].append(change_data)
        return True
    
    @staticmethod
    def get_all_changes(is_founder_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all changes from session storage
        
        Parameters:
        - is_founder_only: If True, return only founder-related changes
        
        Returns:
        - List of dictionaries containing change information
        """
        SessionStorage.initialize_storage()
        
        if not is_founder_only:
            return st.session_state['changes']
        
        # Filter for founder changes
        return [
            change for change in st.session_state['changes']
            if change.get("is_founder_change", "").lower() == "true"
        ]
    
    @staticmethod
    def get_recent_founder_changes(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent founder-related changes
        
        Parameters:
        - limit: Maximum number of changes to return
        
        Returns:
        - List of dictionaries containing change information
        """
        changes = SessionStorage.get_all_changes(is_founder_only=True)
        
        # Sort by detected_date (most recent first)
        changes.sort(key=lambda x: x.get("detected_date", ""), reverse=True)
        
        # Return up to the limit
        return changes[:limit]
    
    @staticmethod
    def clear_storage():
        """Clear all session storage data"""
        if 'profiles' in st.session_state:
            st.session_state['profiles'] = []
        
        if 'changes' in st.session_state:
            st.session_state['changes'] = []
        
        if 'outreach' in st.session_state:
            st.session_state['outreach'] = [] 