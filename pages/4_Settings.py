import streamlit as st
import os
import json
from dotenv import load_dotenv
import tempfile
from datetime import datetime

from config.settings import Settings
from src.api.session_storage import SessionStorage
from src.api.proxycurl import ProxycurlAPI
from src.api.serpapi import SerpAPI
from src.api.openai_api import OpenAIAPI

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
    # Store the API keys in session state
    st.session_state["api_keys"] = {
        "proxycurl_api_key": st.session_state.get("proxycurl_api_key", ""),
        "serpapi_api_key": st.session_state.get("serpapi_api_key", ""),
        "openai_api_key": st.session_state.get("openai_api_key", "")
    }
    
    # Set environment variables
    os.environ["PROXYCURL_API_KEY"] = st.session_state.get("proxycurl_api_key", "")
    os.environ["SERPAPI_API_KEY"] = st.session_state.get("serpapi_api_key", "")
    os.environ["OPENAI_API_KEY"] = st.session_state.get("openai_api_key", "")
    
    st.success("API keys saved successfully!")

# Function to test Proxycurl API
def test_proxycurl_api():
    api_key = st.session_state.get("proxycurl_api_key", "")
    
    if not api_key:
        st.error("Proxycurl API key is not set!")
        return
    
    # Test API
    proxycurl = ProxycurlAPI()
    result = proxycurl.get_credit_balance()
    
    if "error" in result:
        st.error(f"Error testing Proxycurl API: {result['error']}")
    else:
        st.success(f"Proxycurl API is working! Credits remaining: {result.get('credit_balance', 'unknown')}")

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
current_proxycurl_key = os.getenv("PROXYCURL_API_KEY", "")
current_serpapi_key = os.getenv("SERPAPI_API_KEY", "")
current_openai_key = os.getenv("OPENAI_API_KEY", "")

# Load API keys from session state if available
if "api_keys" in st.session_state:
    current_proxycurl_key = st.session_state["api_keys"].get("proxycurl_api_key", current_proxycurl_key)
    current_serpapi_key = st.session_state["api_keys"].get("serpapi_api_key", current_serpapi_key)
    current_openai_key = st.session_state["api_keys"].get("openai_api_key", current_openai_key)

# Display current API status
api_status_col1, api_status_col2, api_status_col3 = st.columns(3)

with api_status_col1:
    proxycurl_status = "✅ Configured" if current_proxycurl_key and current_proxycurl_key != "your_proxycurl_api_key_here" else "❌ Not Configured"
    st.metric(label="Proxycurl API", value=proxycurl_status)

with api_status_col2:
    serpapi_status = "✅ Configured" if current_serpapi_key and current_serpapi_key != "your_serpapi_key_here" else "❌ Not Configured"
    st.metric(label="SerpApi", value=serpapi_status)

with api_status_col3:
    openai_status = "✅ Configured" if current_openai_key and current_openai_key != "your_openai_api_key_here" else "❌ Not Configured"
    st.metric(label="OpenAI API", value=openai_status)

# API configuration form
with st.form("api_config_form"):
    st.markdown("### API Keys")
    
    # Hide API keys by default
    show_keys = st.checkbox("Show API Keys")
    
    # Proxycurl API
    st.markdown("#### Proxycurl API")
    st.markdown("Used to fetch LinkedIn profile data. [Get an API key here](https://nubela.co/proxycurl/)")
    proxycurl_api_key = st.text_input(
        "Proxycurl API Key",
        value=current_proxycurl_key if show_keys else "•" * 10 if current_proxycurl_key else "",
        type="default" if show_keys else "password",
        key="proxycurl_api_key"
    )
    
    # SerpApi
    st.markdown("#### SerpApi")
    st.markdown("Used to discover LinkedIn profiles. [Get an API key here](https://serpapi.com/)")
    serpapi_api_key = st.text_input(
        "SerpApi Key",
        value=current_serpapi_key if show_keys else "•" * 10 if current_serpapi_key else "",
        type="default" if show_keys else "password",
        key="serpapi_api_key"
    )
    
    # OpenAI API
    st.markdown("#### OpenAI API")
    st.markdown("Used to generate insights for outreach. [Get an API key here](https://openai.com/)")
    openai_api_key = st.text_input(
        "OpenAI API Key",
        value=current_openai_key if show_keys else "•" * 10 if current_openai_key else "",
        type="default" if show_keys else "password",
        key="openai_api_key"
    )
    
    # Submit button
    submitted = st.form_submit_button("Save API Keys")
    
    if submitted:
        save_api_keys()

# Test API connections
st.subheader("Test API Connections")

test_col1, test_col2, test_col3 = st.columns(3)

with test_col1:
    st.button("Test Proxycurl API", on_click=test_proxycurl_api)

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

# Storage management
st.subheader("Storage Management")

# Show current storage stats
profiles_count = len(SessionStorage.get_all_profiles())
changes_count = len(SessionStorage.get_all_changes())

stats_col1, stats_col2 = st.columns(2)

with stats_col1:
    st.metric(label="Tracked Profiles", value=profiles_count)

with stats_col2:
    st.metric(label="Detected Changes", value=changes_count)

# Clear storage option
if st.button("Clear All Data", type="primary"):
    SessionStorage.clear_storage()
    st.success("All data has been cleared from session storage.")
    st.experimental_rerun()

# Add app version info
st.sidebar.title("About")
st.sidebar.info(
    "Founder Movement Tracker helps you detect when people become founders "
    "and provides AI-powered insights for outreach."
)
st.sidebar.markdown(f"**Version:** 0.1.0")
st.sidebar.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}") 