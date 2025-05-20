import sys
import os
# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import json
from dotenv import load_dotenv
import tempfile
from datetime import datetime
import asyncio

from config.settings import Settings
from src.api.session_storage import SessionStorage
from src.api.serpapi import SerpAPI
from src.api.openai_api import OpenAIAPI
from src.api.change import Change
from src.api.linkedin_profile import get_linkedin_profile_data

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Settings | Founder Movement Tracker",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Settings")
st.markdown("Configure API keys and application settings.")

# Initialize storage
SessionStorage.initialize_storage()

# Function to save API keys to session state
def save_api_keys():
    """Persist API keys to environment, session state and Settings singleton."""
    rapidapi_key_val = st.session_state.get("rapidapi_key", "")
    serp_key = st.session_state.get("serpapi_api_key", "")
    openai_key = st.session_state.get("openai_api_key", "")

    # Store in session
    st.session_state["api_keys"] = {
        "rapidapi_key": rapidapi_key_val,
        "serpapi_api_key": serp_key,
        "openai_api_key": openai_key,
    }

    # Update environment variables for current session
    os.environ["RAPIDAPI_KEY"] = rapidapi_key_val
    os.environ["SERPAPI_KEY"] = serp_key
    os.environ["OPENAI_API_KEY"] = openai_key

    # Update Settings so other modules pick up the changes immediately
    Settings.save_api_keys(
        rapidapi_key=rapidapi_key_val,
        serpapi_key=serp_key,
        openai_api_key=openai_key
    )
    st.success("API keys updated in session and environment (if changed in form)!")

# Function to test SerpAPI
def test_serpapi():
    api_key = st.session_state.get("serpapi_api_key", "")
    
    if not api_key:
        st.error("SerpApi key is not set!")
        return
    
    # Test API
    serpapi = SerpAPI()
    result = serpapi.get_usage_info()
    
    if "error" in result:
        st.error(f"Error testing SerpApi: {result['error']}")
    else:
        remaining = result.get("plan_searches_left", "unknown")
        st.success(f"SerpApi is working! Searches remaining: {remaining}")

# Function to test OpenAI API
def test_openai_api():
    api_key = st.session_state.get("openai_api_key", "")
    
    if not api_key:
        st.error("OpenAI API key is not set!")
        return
    
    # Test API
    openai_api = OpenAIAPI()
    company_name = "New Startup"
    founder_background = {
        "previous_title": "Product Manager",
        "previous_company": "Google",
        "education": [{"school": "Stanford University", "degree": "MBA"}],
        "skills": ["AI", "Machine Learning", "Product Management"]
    }
    
    try:
        analysis = openai_api.analyze_company_potential(company_name, founder_background)
        st.success(f"OpenAI API is working! Sample analysis: {analysis}")
    except Exception as e:
        st.error(f"Error testing OpenAI API: {str(e)}")

# Create API configuration section
st.subheader("API Configuration")

# Get current API keys from environment
current_rapidapi_key = os.getenv("RAPIDAPI_KEY", "")
current_serpapi_key = os.getenv("SERPAPI_KEY", "")
current_openai_key = os.getenv("OPENAI_API_KEY", "")

# Load API keys from session state if available (e.g., after a failed save and rerun)
if "api_keys" in st.session_state: 
    current_rapidapi_key = st.session_state["api_keys"].get("rapidapi_key", current_rapidapi_key)
    current_serpapi_key = st.session_state["api_keys"].get("serpapi_api_key", current_serpapi_key)
    current_openai_key = st.session_state["api_keys"].get("openai_api_key", current_openai_key)

# Display current API status
api_status_col1, api_status_col2, api_status_col3 = st.columns(3)

with api_status_col1:
    rapidapi_status_val = "✅ Configured" if current_rapidapi_key else "❌ Not Configured"
    st.metric(label="RapidAPI", value=rapidapi_status_val)

with api_status_col2:
    serpapi_status = "✅ Configured" if current_serpapi_key else "❌ Not Configured"
    st.metric(label="SerpApi", value=serpapi_status)

with api_status_col3:
    openai_status = "✅ Configured" if current_openai_key else "❌ Not Configured"
    st.metric(label="OpenAI API", value=openai_status)

# API configuration form
with st.form("api_config_form"):
    st.markdown("### API Keys")
    
    # Hide API keys by default
    show_keys = st.checkbox("Show API Keys")
    
    # Helper to render API key fields with dynamic visibility
    def api_key_input(label: str, key_name: str, current_value: str):
        """Render an API key input field that can toggle between hidden and visible."""
        input_type = "default" if show_keys else "password"
        return st.text_input(
            label,
            value=current_value,
            type=input_type,
            key=key_name,
        )
    
    # RapidAPI Key (replaces Proxycurl)
    st.markdown("#### RapidAPI - Fresh LinkedIn Profile Data")
    st.markdown("Used to fetch LinkedIn profile data. Get an API key from RapidAPI by subscribing to the 'Fresh LinkedIn Profile Data' API.")
    rapidapi_key_val = api_key_input("RapidAPI Key", "rapidapi_key", current_rapidapi_key)
    
    # SerpApi
    st.markdown("#### SerpApi")
    st.markdown("Used to discover LinkedIn profiles. [Get an API key here](https://serpapi.com/)")
    serpapi_api_key = api_key_input("SerpApi Key", "serpapi_api_key", current_serpapi_key)
    
    # OpenAI API
    st.markdown("#### OpenAI API")
    st.markdown("Used to generate insights for outreach. [Get an API key here](https://openai.com/)")
    openai_api_key = api_key_input("OpenAI API Key", "openai_api_key", current_openai_key)
    
    # Submit button
    submitted = st.form_submit_button("Save API Keys")
    
    if submitted:
        # Update os.environ before saving, so Settings can pick it up if it re-initializes
        if rapidapi_key_val:
            os.environ["RAPIDAPI_KEY"] = rapidapi_key_val
        if serpapi_api_key:
            os.environ["SERPAPI_KEY"] = serpapi_api_key
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        Settings.save_api_keys(
            rapidapi_key=rapidapi_key_val,
            serpapi_key=serpapi_api_key,
            openai_api_key=openai_api_key
        )
        st.success("API keys saved successfully!")
        st.rerun()

# Test API connections
st.subheader("Test API Connections")

# Functions to test API connections (moved before usage for clarity)
def test_linkedin_api():
    """Test the RapidAPI LinkedIn connection."""
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        st.error("RapidAPI Key is not set.")
        return
    
    test_url = "https://www.linkedin.com/in/satyanadella/" 
    with st.spinner(f"Testing RapidAPI with {test_url}..."):
        try:
            data = asyncio.run(get_linkedin_profile_data(test_url))
            if data and not data.get("error") and data.get("data"):
                st.success(f"Successfully fetched data for {data.get('data',{}).get('full_name', 'profile')}")
            elif data and data.get("error"):
                st.error(f"RapidAPI Error: {data.get('message')}")
            else:
                st.error("RapidAPI test failed. No data or unexpected response.")
        except Exception as e:
            st.error(f"RapidAPI test failed: {str(e)}")

def test_serpapi():
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        st.error("SerpApi key is not set!")
        return
    
    serpapi = SerpAPI()
    result = serpapi.get_usage_info()
    if "error" in result:
        st.error(f"Error testing SerpApi: {result['error']}")
    else:
        remaining = result.get("plan_searches_left", "unknown")
        st.success(f"SerpApi is working! Searches remaining: {remaining}")

def test_openai_api():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key is not set!")
        return
    
    openai_api = OpenAIAPI()
    # Dummy data for testing OpenAI API call structure
    sample_profile_data = {
        "full_name": "Test Founder",
        "current_title": "Founder",
        "current_company": "TestCo",
        "summary": "Building innovative solutions.",
        "skills": "AI, SaaS, Product Management",
        "experiences": [{
            "title": "Senior PM", "company": "BigTech", 
            "starts_at": {"year": 2018}, "ends_at": {"year": 2022}
        }],
        "education": [{ "school": "Top University", "degree_name": "CS Degree"}]
    }
    sample_change_details = {
        "old_title": "Senior PM", "new_title": "Founder",
        "old_company": "BigTech", "new_company": "TestCo",
        "is_founder_change": True
    }
    sample_change_obj = Change.from_profile_comparison(
        linkedin_url="http://linkedin.com/in/testfounder",
        old_profile=sample_profile_data, # Simplified for test
        new_profile=sample_profile_data, # Simplified for test
        is_founder=True
    )
    sample_change_obj.old_title = sample_change_details["old_title"]
    sample_change_obj.new_title = sample_change_details["new_title"]

    with st.spinner("Testing OpenAI API..."):
        try:
            analysis = openai_api.generate_founder_insight(sample_change_obj, sample_profile_data)
            st.success(f"OpenAI API is working! Sample analysis: {analysis}")
        except Exception as e:
            st.error(f"Error testing OpenAI API: {str(e)}")

test_col1, test_col2, test_col3 = st.columns(3)

with test_col1:
    if st.button("Test LinkedIn Data API (RapidAPI)"):
        test_linkedin_api()

with test_col2:
    st.button("Test SerpApi", on_click=test_serpapi)

with test_col3:
    st.button("Test OpenAI API", on_click=test_openai_api)

# Application settings
st.subheader("Application Settings")

# Get founder keywords
founder_keywords = Settings.FOUNDER_KEYWORDS

# Display and update founder keywords
with st.expander("Founder Detection Keywords"):
    st.markdown("Keywords used to detect founder roles in job titles.")
    
    new_keywords = st.text_area(
        "Founder Keywords (comma separated)",
        value=founder_keywords,
        height=100
    )
    
    if st.button("Update Keywords"):
        # Update settings
        os.environ["FOUNDER_KEYWORDS"] = new_keywords
        Settings.FOUNDER_KEYWORDS = new_keywords
        st.success("Keywords updated successfully!")

# Storage management (in-memory only)
st.subheader("Storage Management")

profiles_count = len(SessionStorage.get_all_profiles())
changes_count = len(SessionStorage.get_all_changes())

st.markdown("All data is stored in-memory and will be lost when the app is restarted. The app tracks changes within the browser session.")

col_p, col_c = st.columns(2)

with col_p:
    st.metric(label="Tracked Profiles", value=profiles_count)

with col_c:
    st.metric(label="Detected Changes", value=changes_count)

if st.button("Clear All Data", type="primary"):
    SessionStorage.clear_storage()
    st.success("All in-memory data has been cleared.")
    st.rerun()

# Add app version info
st.sidebar.title("About")
st.sidebar.info(
    "Founder Movement Tracker helps you detect when people become founders "
    "and provides AI-powered insights for outreach."
)
st.sidebar.markdown(f"**Version:** 0.1.0")
st.sidebar.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}") 