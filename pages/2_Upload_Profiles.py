import streamlit as st
import pandas as pd
import os
import re
from dotenv import load_dotenv
from io import StringIO
import tempfile
import time

from config.settings import Settings
from src.services.profile_service import ProfileService
from src.utils.validators import validate_linkedin_url, validate_csv_with_linkedin_urls
from src.utils.helpers import csv_to_linkedin_urls
from src.api.session_storage import SessionStorage

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Upload Profiles | Founder Movement Tracker",
    page_icon="📤",
    layout="wide"
)

st.title("📤 Upload Profiles")
st.markdown("Upload a CSV file containing LinkedIn profile URLs to begin tracking career changes.")

# Initialize services
profile_service = ProfileService()

# Initialize session storage
SessionStorage.initialize_storage()

# Check if API keys are configured
def check_api_keys():
    """Check if required API keys are set"""
    missing_keys = Settings.get_missing_api_keys()
    return len(missing_keys) == 0, missing_keys

# Function to validate a single LinkedIn URL
def validate_and_add_profile(linkedin_url):
    """Validate and add a single LinkedIn profile URL"""
    if not validate_linkedin_url(linkedin_url):
        return False, f"Invalid LinkedIn URL format: {linkedin_url}"
    
    # Add profile to tracking
    success, message = profile_service.add_profile(linkedin_url)
    return success, message

# Function to add multiple profiles from a CSV file
def upload_profiles_from_csv(csv_content):
    """Process a CSV file and add profiles to tracking"""
    try:
        # Validate CSV content
        valid_urls, errors = validate_csv_with_linkedin_urls(csv_content)
        
        if errors:
            return False, f"CSV validation errors: {', '.join(errors)}", []
        
        if not valid_urls:
            return False, "No valid LinkedIn URLs found in the CSV.", []
        
        # Add profiles in batch
        results = profile_service.batch_add_profiles(valid_urls)
        
        # Return summary
        success = results["success"] > 0 or results["already_tracked"] > 0
        message = f"Added {results['success']} new profiles, {results['already_tracked']} already tracked, {results['failed']} failed."
        
        return success, message, results["details"]
    
    except Exception as e:
        return False, f"Error processing CSV: {str(e)}", []

# Initialize session state
if "upload_results" not in st.session_state:
    st.session_state["upload_results"] = None

if "manual_entry_results" not in st.session_state:
    st.session_state["manual_entry_results"] = []

# Check API keys
api_keys_set, missing_keys = check_api_keys()

if not api_keys_set:
    st.warning("⚠️ Please set up your API keys in the Settings page.")
    st.markdown(f"Missing API keys: {', '.join(missing_keys)}")
    st.stop()

# Create tabs for different ways to add profiles
tab1, tab2, tab3 = st.tabs(["Upload CSV", "Manual Entry", "URL List"])

with tab1:
    st.subheader("Upload CSV File")
    
    st.markdown("""
    Upload a CSV file containing LinkedIn profile URLs. The CSV should have a column named `linkedin_url`.
    
    Example CSV format:
    ```
    linkedin_url
    https://www.linkedin.com/in/johndoe
    https://www.linkedin.com/in/janedoe
    ```
    """)
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        csv_content = uploaded_file.getvalue().decode()
        
        if st.button("Process CSV", key="process_csv_button"):
            with st.spinner("Processing CSV file..."):
                success, message, details = upload_profiles_from_csv(csv_content)
                st.session_state["upload_results"] = {
                    "success": success,
                    "message": message,
                    "details": details
                }
    
    # Display upload results
    if "upload_results" in st.session_state and st.session_state["upload_results"]:
        result = st.session_state["upload_results"]
        
        if result["success"]:
            st.success(result["message"])
        else:
            st.error(result["message"])
        
        # Display detailed results
        if "details" in result and result["details"]:
            with st.expander("View detailed results"):
                for detail in result["details"]:
                    if detail.get("success"):
                        st.markdown(f"✅ {detail.get('url')}: {detail.get('message')}")
                    else:
                        st.markdown(f"❌ {detail.get('url')}: {detail.get('message')}")

with tab2:
    st.subheader("Manual Entry")
    
    st.markdown("""
    Enter a single LinkedIn profile URL manually.
    
    Example: `https://www.linkedin.com/in/johndoe`
    """)
    
    # Form for manual entry
    with st.form("manual_entry_form"):
        linkedin_url = st.text_input("LinkedIn Profile URL")
        submitted = st.form_submit_button("Add Profile")
        
        if submitted and linkedin_url:
            with st.spinner("Adding profile..."):
                success, message = validate_and_add_profile(linkedin_url)
                
                st.session_state["manual_entry_results"].append({
                    "url": linkedin_url,
                    "success": success,
                    "message": message,
                    "timestamp": time.time()
                })
    
    # Display manual entry results
    if "manual_entry_results" in st.session_state and st.session_state["manual_entry_results"]:
        # Sort results by timestamp (newest first)
        sorted_results = sorted(
            st.session_state["manual_entry_results"],
            key=lambda x: x.get("timestamp", 0),
            reverse=True
        )
        
        # Display only the most recent 10 results
        for result in sorted_results[:10]:
            if result.get("success"):
                st.success(f"{result.get('url')}: {result.get('message')}")
            else:
                st.error(f"{result.get('url')}: {result.get('message')}")
        
        # Add a clear button
        if st.button("Clear Results"):
            st.session_state["manual_entry_results"] = []
            st.experimental_rerun()

with tab3:
    st.subheader("Text List of URLs")
    
    st.markdown("""
    Enter a list of LinkedIn profile URLs, one per line.
    
    Example:
    ```
    https://www.linkedin.com/in/johndoe
    https://www.linkedin.com/in/janedoe
    ```
    """)
    
    # Form for text entry
    with st.form("url_list_form"):
        url_list = st.text_area("LinkedIn Profile URLs (one per line)")
        submitted = st.form_submit_button("Add Profiles")
        
        if submitted and url_list:
            with st.spinner("Processing URLs..."):
                # Split by newline and clean up
                urls = [url.strip() for url in url_list.split("\n") if url.strip()]
                
                # Validate URLs
                valid_urls = []
                invalid_urls = []
                
                for url in urls:
                    if validate_linkedin_url(url):
                        valid_urls.append(url)
                    else:
                        invalid_urls.append(url)
                
                if invalid_urls:
                    st.error(f"Found {len(invalid_urls)} invalid URLs: {', '.join(invalid_urls)}")
                
                if valid_urls:
                    # Add valid URLs in batch
                    results = profile_service.batch_add_profiles(valid_urls)
                    
                    # Display summary
                    st.success(f"Added {results['success']} new profiles, {results['already_tracked']} already tracked, {results['failed']} failed.")
                    
                    # Store results in session state for detailed view
                    st.session_state["url_list_results"] = results

# Display tracked profiles
st.markdown("---")
st.subheader("Currently Tracked Profiles")

profiles = SessionStorage.get_all_profiles()
if profiles:
    # Create a dataframe for display
    df = pd.DataFrame([
        {
            "Name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
            "Current Title": p.get('current_title', ''),
            "Current Company": p.get('current_company', ''),
            "LinkedIn URL": p.get('linkedin_url', '')
        }
        for p in profiles
    ])
    
    # Display the table
    st.dataframe(df, use_container_width=True)
    
    # Add a button to clear all profiles
    if st.button("Clear All Profiles"):
        SessionStorage.clear_storage()
        st.success("All profiles cleared.")
        st.experimental_rerun()
else:
    st.info("No profiles currently being tracked. Use the forms above to add profiles.")

# Instructions section
st.markdown("---")
st.subheader("How to Get LinkedIn Profile URLs")

st.markdown("""
To get a LinkedIn profile URL:

1. Visit a person's LinkedIn profile
2. Copy the URL from your browser's address bar
3. The URL should look like: `https://www.linkedin.com/in/username`

You can also export connections from LinkedIn:

1. Go to your LinkedIn connections page
2. Click on "Manage synced and imported contacts"
3. Click on "Export contacts"
4. Select "Connections" and download as CSV
5. Use the downloaded CSV file for upload
""")

# Add a link to check tracked profiles
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("View Dashboard", key="view_dashboard_button"):
        st.switch_page("pages/1_Dashboard.py")

with col2:
    if st.button("Discover Profiles", key="discover_profiles_button"):
        st.switch_page("pages/3_Discover.py") 