import streamlit as st
import os
from pathlib import Path

def show_welcome():
    st.title("Welcome to Founder Movement Tracker")
    
    # Check if first time setup is needed
    if not (Path(".env").exists() and Path("credentials/isv-service-account.json").exists()):
        st.markdown("### First-time Setup Required")
        
        # Create credentials directory if it doesn't exist
        credentials_dir = Path("credentials")
        credentials_dir.mkdir(exist_ok=True)
        
        # API Keys Setup
        st.subheader("1. API Keys")
        proxycurl_key = st.text_input("Proxycurl API Key", type="password")
        serpapi_key = st.text_input("SerpApi Key", type="password")
        openai_key = st.text_input("OpenAI API Key", type="password")
        
        # Google Sheets Setup
        st.subheader("2. Google Sheets Setup")
        st.markdown("""
        To set up Google Sheets integration:
        1. Go to [Google Cloud Console](https://console.cloud.google.com)
        2. Create a new project or select existing one
        3. Enable Google Sheets API
        4. Create a service account and download JSON credentials
        """)
        
        uploaded_file = st.file_uploader("Upload Google Service Account JSON", type=['json'])
        
        if st.button("Complete Setup"):
            if all([proxycurl_key, serpapi_key, openai_key, uploaded_file]):
                # Save API keys to .env
                env_content = f"""
                PROXYCURL_API_KEY={proxycurl_key}
                SERPAPI_KEY={serpapi_key}
                OPENAI_API_KEY={openai_key}
                """
                with open(".env", "w") as f:
                    f.write(env_content)
                
                # Save Google credentials
                with open("credentials/isv-service-account.json", "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                st.success("Setup completed successfully!")
                st.balloons()
                st.experimental_rerun()
            else:
                st.error("Please fill in all required credentials")
    else:
        st.success("✅ Setup completed! You can now use the application.")
        st.markdown("""
        ## Quick Start Guide
        
        1. **Upload Profiles**
           - Go to the Upload page
           - Upload a CSV file with LinkedIn URLs
        
        2. **Discover New Profiles**
           - Use the Discover page to find new profiles
           - Add them to your tracking list
        
        3. **Monitor Changes**
           - Check the Dashboard for recent changes
           - Get AI-powered insights for outreach
        
        [Get Started →](?page=1_Dashboard)
        """)
    
        # Add testimonials or use cases
        st.markdown("""
        ## Why Use Founder Movement Tracker?
        
        - 🚀 Automate founder discovery
        - 📊 Track career changes in real-time
        - 🤖 Get AI-powered insights
        - 📈 Improve deal flow
        """)

if __name__ == "__main__":
    show_welcome() 