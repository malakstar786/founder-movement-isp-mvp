import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

class GoogleSheetsAPI:
    """
    Class to handle interactions with Google Sheets API for data storage
    """
    
    def __init__(self):
        # Get configuration from environment variables
        self.service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        
        # Sheet names for organization
        self.profiles_sheet_name = "Profiles"
        self.changes_sheet_name = "Changes"
        self.outreach_sheet_name = "Outreach"
        
        # Initialize connection
        self.client = None
        self.spreadsheet = None
        self.initialize_connection()
    
    def initialize_connection(self):
        """Initialize connection to Google Sheets"""
        if not self.service_account_file or not os.path.exists(self.service_account_file):
            print(f"Service account file not found: {self.service_account_file}")
            return False
        
        if not self.sheet_id:
            print("Google Sheet ID not provided")
            return False
        
        try:
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            
            # Authenticate
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.service_account_file, scope)
            self.client = gspread.authorize(creds)
            
            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            
            # Initialize sheets if they don't exist
            self._initialize_sheets()
            
            return True
        except Exception as e:
            print(f"Error initializing Google Sheets connection: {str(e)}")
            return False
    
    def _initialize_sheets(self):
        """Initialize necessary worksheets if they don't exist"""
        if not self.spreadsheet:
            return False
        
        try:
            # Get all worksheet titles
            worksheet_list = self.spreadsheet.worksheets()
            worksheet_titles = [ws.title for ws in worksheet_list]
            
            # Create Profiles sheet if it doesn't exist
            if self.profiles_sheet_name not in worksheet_titles:
                profiles_sheet = self.spreadsheet.add_worksheet(
                    title=self.profiles_sheet_name, rows=1000, cols=10
                )
                # Add headers
                profiles_sheet.append_row([
                    "linkedin_url", "first_name", "last_name", "current_title",
                    "current_company", "previous_title", "previous_company",
                    "last_checked_date", "tracking_status", "outreach_status"
                ])
            
            # Create Changes sheet if it doesn't exist
            if self.changes_sheet_name not in worksheet_titles:
                changes_sheet = self.spreadsheet.add_worksheet(
                    title=self.changes_sheet_name, rows=1000, cols=10
                )
                # Add headers
                changes_sheet.append_row([
                    "change_id", "linkedin_url", "detected_date", "old_title",
                    "new_title", "old_company", "new_company", "is_founder_change",
                    "ai_insight", "notification_sent"
                ])
            
            # Create Outreach sheet if it doesn't exist
            if self.outreach_sheet_name not in worksheet_titles:
                outreach_sheet = self.spreadsheet.add_worksheet(
                    title=self.outreach_sheet_name, rows=1000, cols=8
                )
                # Add headers
                outreach_sheet.append_row([
                    "outreach_id", "linkedin_url", "change_id", "outreach_date",
                    "outreach_method", "response_received", "notes", "follow_up_date"
                ])
            
            return True
        except Exception as e:
            print(f"Error initializing sheets: {str(e)}")
            return False
    
    def add_profile(self, profile_data):
        """
        Add a new profile to the Profiles sheet
        
        Parameters:
        - profile_data: Dictionary containing profile information
        
        Returns:
        - Boolean indicating success or failure
        """
        if not self.spreadsheet:
            return False
        
        try:
            # Get the Profiles sheet
            profiles_sheet = self.spreadsheet.worksheet(self.profiles_sheet_name)
            
            # Check if profile already exists
            existing_profiles = profiles_sheet.col_values(1)  # Get all values in the first column (linkedin_url)
            
            if profile_data.get("linkedin_url") in existing_profiles:
                # Update existing profile
                return self.update_profile(profile_data)
            
            # Prepare row data
            row_data = [
                profile_data.get("linkedin_url", ""),
                profile_data.get("first_name", ""),
                profile_data.get("last_name", ""),
                profile_data.get("current_title", ""),
                profile_data.get("current_company", ""),
                profile_data.get("previous_title", ""),
                profile_data.get("previous_company", ""),
                datetime.now().isoformat(),  # last_checked_date
                "Active",  # tracking_status
                "Not contacted"  # outreach_status
            ]
            
            # Add row to sheet
            profiles_sheet.append_row(row_data)
            return True
        except Exception as e:
            print(f"Error adding profile: {str(e)}")
            return False
    
    def update_profile(self, profile_data):
        """
        Update an existing profile in the Profiles sheet
        
        Parameters:
        - profile_data: Dictionary containing profile information
        
        Returns:
        - Boolean indicating success or failure
        """
        if not self.spreadsheet:
            return False
        
        try:
            # Get the Profiles sheet
            profiles_sheet = self.spreadsheet.worksheet(self.profiles_sheet_name)
            
            # Find the row for this profile
            linkedin_url = profile_data.get("linkedin_url", "")
            cell = profiles_sheet.find(linkedin_url, in_column=1)
            
            if not cell:
                # Profile not found, add it instead
                return self.add_profile(profile_data)
            
            # Update cells in the row
            row_index = cell.row
            profiles_sheet.update_cell(row_index, 3, profile_data.get("first_name", ""))
            profiles_sheet.update_cell(row_index, 4, profile_data.get("last_name", ""))
            profiles_sheet.update_cell(row_index, 5, profile_data.get("current_title", ""))
            profiles_sheet.update_cell(row_index, 6, profile_data.get("current_company", ""))
            profiles_sheet.update_cell(row_index, 7, profile_data.get("previous_title", ""))
            profiles_sheet.update_cell(row_index, 8, profile_data.get("previous_company", ""))
            profiles_sheet.update_cell(row_index, 9, datetime.now().isoformat())  # last_checked_date
            
            return True
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            return False
    
    def record_change(self, change_data):
        """
        Record a career change in the Changes sheet
        
        Parameters:
        - change_data: Dictionary containing change information
        
        Returns:
        - Boolean indicating success or failure
        """
        if not self.spreadsheet:
            return False
        
        try:
            # Get the Changes sheet
            changes_sheet = self.spreadsheet.worksheet(self.changes_sheet_name)
            
            # Get the next change_id
            change_ids = changes_sheet.col_values(1)[1:]  # Skip header
            next_change_id = 1
            if change_ids:
                try:
                    next_change_id = max([int(cid) for cid in change_ids if cid.isdigit()]) + 1
                except ValueError:
                    next_change_id = len(change_ids) + 1
            
            # Prepare row data
            row_data = [
                str(next_change_id),
                change_data.get("linkedin_url", ""),
                change_data.get("detected_date", datetime.now().isoformat()),
                change_data.get("old_title", ""),
                change_data.get("new_title", ""),
                change_data.get("old_company", ""),
                change_data.get("new_company", ""),
                str(change_data.get("is_founder_change", False)).lower(),
                change_data.get("ai_insight", ""),
                str(change_data.get("notification_sent", False)).lower()
            ]
            
            # Add row to sheet
            changes_sheet.append_row(row_data)
            return True
        except Exception as e:
            print(f"Error recording change: {str(e)}")
            return False
    
    def record_outreach(self, outreach_data):
        """
        Record an outreach attempt in the Outreach sheet
        
        Parameters:
        - outreach_data: Dictionary containing outreach information
        
        Returns:
        - Boolean indicating success or failure
        """
        if not self.spreadsheet:
            return False
        
        try:
            # Get the Outreach sheet
            outreach_sheet = self.spreadsheet.worksheet(self.outreach_sheet_name)
            
            # Get the next outreach_id
            outreach_ids = outreach_sheet.col_values(1)[1:]  # Skip header
            next_outreach_id = 1
            if outreach_ids:
                try:
                    next_outreach_id = max([int(oid) for oid in outreach_ids if oid.isdigit()]) + 1
                except ValueError:
                    next_outreach_id = len(outreach_ids) + 1
            
            # Prepare row data
            row_data = [
                str(next_outreach_id),
                outreach_data.get("linkedin_url", ""),
                outreach_data.get("change_id", ""),
                outreach_data.get("outreach_date", datetime.now().isoformat()),
                outreach_data.get("outreach_method", ""),
                str(outreach_data.get("response_received", False)).lower(),
                outreach_data.get("notes", ""),
                outreach_data.get("follow_up_date", "")
            ]
            
            # Add row to sheet
            outreach_sheet.append_row(row_data)
            return True
        except Exception as e:
            print(f"Error recording outreach: {str(e)}")
            return False
    
    def get_all_profiles(self):
        """
        Get all profiles from the Profiles sheet
        
        Returns:
        - List of dictionaries containing profile information
        """
        if not self.spreadsheet:
            return []
        
        try:
            # Get the Profiles sheet
            profiles_sheet = self.spreadsheet.worksheet(self.profiles_sheet_name)
            
            # Get all values as list of lists
            all_values = profiles_sheet.get_all_values()
            
            if len(all_values) <= 1:  # Only header or empty sheet
                return []
            
            # Extract header and data
            headers = all_values[0]
            data_rows = all_values[1:]
            
            # Convert to list of dictionaries
            profiles = []
            for row in data_rows:
                profile = {headers[i]: row[i] for i in range(len(headers))}
                profiles.append(profile)
            
            return profiles
        except Exception as e:
            print(f"Error retrieving profiles: {str(e)}")
            return []
    
    def get_profile(self, linkedin_url):
        """
        Get a specific profile from the Profiles sheet
        
        Parameters:
        - linkedin_url: LinkedIn URL to look up
        
        Returns:
        - Dictionary containing profile information, or None if not found
        """
        if not self.spreadsheet:
            return None
        
        try:
            # Get the Profiles sheet
            profiles_sheet = self.spreadsheet.worksheet(self.profiles_sheet_name)
            
            # Find the row for this profile
            cell = profiles_sheet.find(linkedin_url, in_column=1)
            
            if not cell:
                return None
            
            # Get headers and row data
            headers = profiles_sheet.row_values(1)
            row_data = profiles_sheet.row_values(cell.row)
            
            # Create dictionary
            profile = {headers[i]: row_data[i] for i in range(len(headers)) if i < len(row_data)}
            
            return profile
        except Exception as e:
            print(f"Error retrieving profile: {str(e)}")
            return None
    
    def get_all_changes(self, is_founder_only=False):
        """
        Get all changes from the Changes sheet
        
        Parameters:
        - is_founder_only: If True, return only founder-related changes
        
        Returns:
        - List of dictionaries containing change information
        """
        if not self.spreadsheet:
            return []
        
        try:
            # Get the Changes sheet
            changes_sheet = self.spreadsheet.worksheet(self.changes_sheet_name)
            
            # Get all values as list of lists
            all_values = changes_sheet.get_all_values()
            
            if len(all_values) <= 1:  # Only header or empty sheet
                return []
            
            # Extract header and data
            headers = all_values[0]
            data_rows = all_values[1:]
            
            # Convert to list of dictionaries
            changes = []
            for row in data_rows:
                change = {headers[i]: row[i] for i in range(len(headers)) if i < len(row)}
                
                # Filter by founder changes if requested
                if is_founder_only and change.get("is_founder_change", "").lower() != "true":
                    continue
                
                changes.append(change)
            
            return changes
        except Exception as e:
            print(f"Error retrieving changes: {str(e)}")
            return []
    
    def get_recent_founder_changes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent founder-related changes
        
        Parameters:
        - limit: Maximum number of changes to return
        
        Returns:
        - List of dictionaries containing change information
        """
        founder_changes = self.get_all_changes(is_founder_only=True)
        
        # Sort by detected_date (most recent first)
        founder_changes.sort(key=lambda x: x.get("detected_date", ""), reverse=True)
        
        # Return up to the limit
        return founder_changes[:limit]
    
    def update_outreach(self, outreach_data: Dict[str, Any]) -> bool:
        """
        Update an existing outreach record in the Outreach sheet
        
        Parameters:
        - outreach_data: Dictionary containing outreach information
        
        Returns:
        - Boolean indicating success or failure
        """
        if not self.spreadsheet:
            return False
        
        try:
            # Get the Outreach sheet
            outreach_sheet = self.spreadsheet.worksheet(self.outreach_sheet_name)
            
            # Find the row for this outreach
            outreach_id = outreach_data.get("outreach_id", "")
            
            if not outreach_id:
                return False
                
            cell = outreach_sheet.find(str(outreach_id), in_column=1)
            
            if not cell:
                # Outreach not found, add it instead
                return self.record_outreach(outreach_data)
            
            # Update cells in the row
            row_index = cell.row
            
            # Update each field
            outreach_sheet.update_cell(row_index, 2, outreach_data.get("linkedin_url", ""))
            
            # Update change_id if present
            if "change_id" in outreach_data:
                outreach_sheet.update_cell(row_index, 3, outreach_data.get("change_id", ""))
            
            # Update outreach_date
            outreach_sheet.update_cell(row_index, 4, outreach_data.get("outreach_date", ""))
            
            # Update outreach_method
            outreach_sheet.update_cell(row_index, 5, outreach_data.get("outreach_method", ""))
            
            # Update response_received
            outreach_sheet.update_cell(row_index, 6, str(outreach_data.get("response_received", "false")).lower())
            
            # Update notes
            outreach_sheet.update_cell(row_index, 7, outreach_data.get("notes", ""))
            
            # Update follow_up_date if present
            if "follow_up_date" in outreach_data:
                outreach_sheet.update_cell(row_index, 8, outreach_data.get("follow_up_date", ""))
            
            return True
        except Exception as e:
            print(f"Error updating outreach: {str(e)}")
            return False
    
    def get_all_outreach(self) -> List[Dict[str, Any]]:
        """
        Get all outreach records from the Outreach sheet
        
        Returns:
        - List of dictionaries containing outreach information
        """
        if not self.spreadsheet:
            return []
        
        try:
            # Get the Outreach sheet
            outreach_sheet = self.spreadsheet.worksheet(self.outreach_sheet_name)
            
            # Get all values as list of lists
            all_values = outreach_sheet.get_all_values()
            
            if len(all_values) <= 1:  # Only header or empty sheet
                return []
            
            # Extract header and data
            headers = all_values[0]
            data_rows = all_values[1:]
            
            # Convert to list of dictionaries
            outreach_records = []
            for row in data_rows:
                record = {headers[i]: row[i] for i in range(len(headers)) if i < len(row)}
                outreach_records.append(record)
            
            return outreach_records
        except Exception as e:
            print(f"Error retrieving outreach records: {str(e)}")
            return []
    
    def get_outreach_for_url(self, linkedin_url: str) -> List[Dict[str, Any]]:
        """
        Get outreach records for a specific LinkedIn URL
        
        Parameters:
        - linkedin_url: LinkedIn URL to look up
        
        Returns:
        - List of dictionaries containing outreach information
        """
        if not self.spreadsheet:
            return []
        
        try:
            # Get all outreach records
            all_records = self.get_all_outreach()
            
            # Filter by LinkedIn URL
            return [rec for rec in all_records if rec.get("linkedin_url") == linkedin_url]
        except Exception as e:
            print(f"Error retrieving outreach for URL: {str(e)}")
            return []
