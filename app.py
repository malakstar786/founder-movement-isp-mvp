import streamlit as st
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from config.logging_config import setup_logging
from config.settings import Settings
from src.utils.validators import validate_api_keys

# Setup logging
logger = setup_logging()

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Founder Movement Tracker | ISV Capital",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .stButton button {
        background-color: #4CAF50;
        color: white;
    }
    .success-message {
        color: #4CAF50;
        font-weight: bold;
    }
    .error-message {
        color: #FF4500;
        font-weight: bold;
    }
    .warning-message {
        color: #FFA500;
        font-weight: bold;
    }
    .founder-change {
        background-color: #E6F7FF;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #1890FF;
        margin-bottom: 10px;
    }
    .title-change {
        background-color: #F6FFED;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #52C41A;
        margin-bottom: 10px;
    }
    .company-change {
        background-color: #FFF7E6;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #FA8C16;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Function to check API keys
def check_api_keys():
    """Check if required API keys are set"""
    missing_keys = Settings.get_missing_api_keys()
    return len(missing_keys) == 0, missing_keys

# Main app
def main():
    """Main app function"""
    st.title("Founder Movement Tracker")
    st.markdown("Track career changes among pre-seed founders and get AI-powered insights for outreach.")
    
    # Check API keys
    api_keys_set, missing_keys = check_api_keys()
    
    if not api_keys_set:
        st.warning("⚠️ Please set up your API keys in the Settings page.")
        st.markdown(f"Missing API keys: {', '.join(missing_keys)}")
        
        # Display setup instructions
        with st.expander("Setup Instructions", expanded=True):
            st.markdown("""
            ## Setup Instructions
            
            1. Go to the **Settings** page
            2. Enter your API keys:
               - Proxycurl API Key (for LinkedIn data)
               - SerpApi Key (for finding profiles)
               - OpenAI API Key (for generating insights)
               - Google Sheet ID (for storing data)
               - Upload Google Service Account JSON
            3. Save settings
            
            Once all keys are configured, you'll be able to:
            - Upload LinkedIn profiles to track
            - Discover new profiles to track
            - Monitor founder transitions
            - Get AI-powered outreach insights
            """)
    else:
        # Display app overview
        st.success("✅ API keys configured. The application is ready to use.")
        
        # App statistics
        with st.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(label="Profiles Tracked", value="0")
            
            with col2:
                st.metric(label="Founder Transitions", value="0")
            
            with col3:
                st.metric(label="Pending Outreach", value="0")
        
        # Quick actions
        st.subheader("Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.button("Upload Profiles", on_click=lambda: st.switch_page("pages/2_Upload_Profiles.py"))
        
        with col2:
            st.button("Discover Profiles", on_click=lambda: st.switch_page("pages/3_Discover.py"))
        
        with col3:
            st.button("Check for Changes", on_click=lambda: st.switch_page("pages/1_Dashboard.py"))
    
    # App information
    st.sidebar.title("About")
    st.sidebar.info(
        "This application helps track career changes among pre-seed founders. "
        "It automatically detects when someone has changed their role to 'Founder' "
        "or joined a stealth startup, and provides AI-powered insights for outreach."
    )
    
    # Show app version
    st.sidebar.markdown(f"**Version:** 0.1.0")
    st.sidebar.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main() 