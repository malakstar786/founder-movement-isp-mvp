import streamlit as st
import pandas as pd
import os
import json
import requests
from dotenv import load_dotenv
import random
import asyncio

from src.api.session_storage import SessionStorage
from src.services.profile_service import ProfileService
from src.api.serpapi import SerpAPI

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Discover Profiles | Founder Movement Tracker",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Discover Profiles")
st.markdown("Find new LinkedIn profiles to track based on keywords, industries, or locations.")

# Initialize services
profile_service = ProfileService()
serp_api = SerpAPI()

# Initialize session storage
SessionStorage.initialize_storage()

# Function to search for profiles (using SerpAPI if key available)
def search_profiles(keywords, industry=None, location=None, company=None):
    """
    Search for LinkedIn profiles using SerpApi
    """
    # Check if we have an API key
    api_key = os.getenv("SERPAPI_API_KEY")
    
    if not api_key or api_key == "your_serpapi_key_here":
        st.warning("⚠️ SerpApi key not configured. Using mock data.")
        return get_mock_results(keywords, industry, location, company)
    
    try:
        # Prepare search query
        search_terms = keywords
        if industry:
            search_terms += f", {industry}"
        
        # Add founder keywords if not present
        founder_keywords = ["founder", "co-founder", "ceo", "entrepreneur"]
        has_founder_term = any(term.lower() in search_terms.lower() for term in founder_keywords)
        if not has_founder_term:
            search_terms += ", founder"
        
        # Make API call
        st.info(f"Searching for: {search_terms}")
        search_results = serp_api.search_linkedin_profiles(search_terms, location)
        
        if "error" in search_results:
            st.error(f"Error from SerpAPI: {search_results['error']}")
            return get_mock_results(keywords, industry, location, company)
        
        # Extract and filter profiles
        profiles = serp_api.extract_profiles(search_results)
        
        # Filter for company if specified
        if company:
            profiles = [
                profile for profile in profiles
                if company.lower() in profile.get("job_title", "").lower()
                or company.lower() in profile.get("description", "").lower()
            ]
        
        # Add relevance scores
        for profile in profiles:
            # Check if title contains founder keywords
            job_title = profile.get("job_title", "").lower()
            is_founder = serp_api.detect_founder_in_title(job_title)
            profile["is_founder"] = is_founder
            profile["relevance_score"] = 0.9 if is_founder else 0.7

            # Ensure we have a company field for display
            if "company" not in profile or not profile["company"]:
                inferred_company = serp_api.parse_company_from_job_title(profile.get("job_title", ""))
                profile["company"] = inferred_company
        
        # Sort by relevance
        profiles.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return profiles
    except Exception as e:
        st.error(f"Error searching profiles: {str(e)}")
        return get_mock_results(keywords, industry, location, company)

def get_mock_results(keywords, industry=None, location=None, company=None):
    """Generate mock search results for UI demonstration"""
    # Create some mock profiles based on the search criteria
    mock_results = []
    
    # Parse keywords
    keyword_list = [k.strip() for k in keywords.split(',')]
    
    for i in range(1, 6):  # Generate 5 mock results
        first_name = random.choice(["John", "Jane", "Alex", "Sarah", "Michael", "Emma"])
        last_name = random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller"])
        
        # Use the keywords to generate job titles
        job_keywords = random.sample(keyword_list, min(len(keyword_list), 2))
        job_title = " ".join(job_keywords).title()
        
        if random.random() < 0.7:  # 70% chance to be founder-related
            founder_prefix = random.choice(["Founder", "Co-founder", "CEO", "Founder &", "Co-founder &"])
            job_title = f"{founder_prefix} {job_title}"
        
        # Use industry if provided
        company_name = "Startup"
        if industry:
            company_name = f"{industry.split(',')[0].strip()} {company_name}"
        
        # Include location if provided
        profile_location = location if location else "San Francisco Bay Area"
        
        # Create a unique LinkedIn URL
        linkedin_url = f"https://www.linkedin.com/in/{first_name.lower()}-{last_name.lower()}-{random.randint(10000, 99999)}"
        
        # Create description with keywords
        description = f"Experienced {job_title} with background in {', '.join(keyword_list)}. " + \
                      f"Building innovative solutions for {industry if industry else 'technology'} sector."
        
        # Create mock result
        mock_results.append({
            "name": f"{first_name} {last_name}",
            "link": linkedin_url,
            "job_title": job_title,
            "company": company_name,
            "location": profile_location,
            "description": description,
            "relevance_score": round(random.uniform(0.7, 0.99), 2),  # Random relevance score between 0.7 and 0.99
            "is_founder": "founder" in job_title.lower() or "ceo" in job_title.lower()
        })
    
    # Sort by relevance score
    mock_results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return mock_results

# Function to add profiles to tracking
async def add_to_tracking_async(profiles):
    """Add selected profiles to tracking"""
    if isinstance(profiles, list) and all(isinstance(item, str) for item in profiles):
        # URLs only
        results = await profile_service.batch_add_profiles(profiles)
    else:
        # Full profile objects
        linkedin_urls = [p['link'] for p in profiles]
        results = await profile_service.batch_add_profiles(linkedin_urls)
    
    return results

# Display search form
st.subheader("Search for LinkedIn Profiles")

with st.form("profile_search_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        keywords = st.text_input(
            "Search Keywords (comma separated)",
            placeholder="founder, startup, AI, fintech, etc.",
            help="Enter keywords related to the profiles you want to find."
        )
        
        industry = st.text_input(
            "Industry (optional)",
            placeholder="Fintech, AI, Health Tech, etc.",
            help="Specify industry sectors to filter results."
        )
    
    with col2:
        location = st.text_input(
            "Location (optional)",
            placeholder="San Francisco, New York, etc.",
            help="Enter locations to filter results by geography."
        )
        
        company = st.text_input(
            "Company (optional)",
            placeholder="Google, Meta, etc.",
            help="Specify companies to filter for alumni."
        )
    
    submitted = st.form_submit_button("Search Profiles")

# --- Helper function to render search results --------------------------------

def _render_results(display_results):
    """Render a list of discovered profiles with tracking actions."""
    if not display_results:
        st.info("No profiles found matching your criteria. Try different keywords.")
        return

    st.success(f"Found {len(display_results)} profiles matching your criteria.")

    # Display summary table
    results_df = pd.DataFrame([
        {
            'Name': r['name'],
            'Job Title': r['job_title'],
            'Company': r['company'],
            'Location': r['location'],
            'Description': r['description'],
            'LinkedIn URL': r['link']
        }
        for r in display_results
    ])
    st.dataframe(
        results_df[[
            'Name',
            'Job Title',
            'Company',
            'Location',
            'Description',
            'LinkedIn URL',
        ]],
        use_container_width=True,
    )

    # Detailed card per profile
    for idx, result in enumerate(display_results):
        with st.expander(f"{result['name']} - {result['job_title']} at {result['company']}"):
            st.write(f"**Location:** {result['location']}")
            st.write(f"**Description:** {result['description']}")
            st.write(f"**LinkedIn URL:** [{result['link']}]({result['link']})")
            if st.button("Add to Tracking", key=f"add_single_{idx}"):
                asyncio.run(add_to_tracking_async([result['link']]))
                st.success(f"Added {result['name']} to tracking list.")

    # Bulk add button (outside loop so it appears once)
    if st.button("Add All to Tracking"):
        asyncio.run(add_to_tracking_async([r['link'] for r in display_results]))
        st.success("All displayed profiles have been added to your tracking list.")

# --------------------------------------------------------------
# Process search request and manage result persistence

if submitted:
    if not keywords:
        st.error("Please enter at least one search keyword.")
    else:
        with st.spinner("Searching for LinkedIn profiles..."):
            search_outcome = search_profiles(keywords, industry, location, company)

        # Persist and display
        st.session_state['search_results'] = search_outcome
        _render_results(search_outcome)
else:
    # If the user has not just submitted but we have previous results, show them
    previous_results = st.session_state.get('search_results', [])
    if previous_results:
        st.markdown("### Previous Search Results")
        _render_results(previous_results)

# Display API usage
st.subheader("SerpApi Usage")
api_key = os.getenv("SERPAPI_API_KEY")
if api_key and api_key != "your_serpapi_key_here":
    try:
        usage_info = serp_api.get_usage_info()
        if "error" not in usage_info:
            remaining = usage_info.get("plan_searches_left", "unknown")
            st.info(f"SerpApi free tier allows 100 searches per month. You have {remaining} searches remaining.")
        else:
            st.warning(f"Error getting SerpApi usage: {usage_info['error']}")
    except Exception as e:
        st.warning(f"Error getting SerpApi usage: {str(e)}")
else:
    st.info("SerpApi free tier allows 100 searches per month. Configure your API key in Settings to track usage.")

# Tips for effective searching
st.subheader("Tips for Effective Profile Discovery")
st.markdown("""
* Use specific industry keywords like "fintech", "healthtech", or "AI startup"
* Search for common founder title variations: "founder", "co-founder", "CEO", etc.
* Use location keywords to find founders in specific regions
* Combine previous company names with founder keywords to find alumni who have started companies
* Try different combinations of keywords to maximize your search coverage
""")

# Display currently tracked profiles
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
else:
    st.info("No profiles currently being tracked. Use the search above to find profiles.") 