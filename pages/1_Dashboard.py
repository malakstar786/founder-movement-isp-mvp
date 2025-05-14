import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import plotly.express as px
import datetime
import random
from datetime import datetime, timedelta

from config.settings import Settings
from src.api.session_storage import SessionStorage
from src.services.profile_service import ProfileService
from src.models.profile import Profile
from src.models.change import Change
from src.utils.helpers import format_iso_date

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Dashboard | Founder Movement Tracker",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard")
st.markdown("Monitor founder transitions and career changes in your tracking list.")

# Initialize services
profile_service = ProfileService()

# Check if API keys are configured
def check_api_keys():
    """Check if required API keys are set"""
    missing_keys = Settings.get_missing_api_keys()
    return len(missing_keys) == 0, missing_keys

# Function to refresh all profiles
def refresh_all_profiles():
    with st.spinner("Refreshing all profiles... This may take a minute due to API rate limits."):
        result = profile_service.batch_refresh_profiles()
        
        st.session_state["refresh_result"] = result
        st.session_state["last_refresh"] = datetime.now().isoformat()

# Function to get founder changes with profile details
def get_founder_changes(limit=10):
    try:
        # Get recent founder changes
        changes = profile_service.get_recent_founder_changes(limit)
        return changes
    except Exception as e:
        st.error(f"Error getting founder changes: {str(e)}")
        return []

# Function to render a change card
def render_change_card(change):
    detected_date = format_iso_date(change.get("detected_date", ""), format_str="%B %d, %Y")
    full_name = change.get("full_name", "Unknown")
    old_title = change.get("old_title", "")
    new_title = change.get("new_title", "")
    old_company = change.get("old_company", "")
    new_company = change.get("new_company", "")
    linkedin_url = change.get("linkedin_url", "")
    ai_insight = change.get("ai_insight", "")
    
    with st.container():
        st.markdown(f"""
        <div class="founder-change">
            <h3>{full_name}</h3>
            <p><strong>Changed on:</strong> {detected_date}</p>
            <p><strong>From:</strong> {old_title} at {old_company}</p>
            <p><strong>To:</strong> {new_title} at {new_company}</p>
            <p><strong>Insight:</strong> {ai_insight}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.button(f"View Profile", key=f"view_{linkedin_url}", on_click=lambda: st.markdown(f"[View on LinkedIn]({linkedin_url})"))
        with col2:
            st.button(f"Contact", key=f"contact_{linkedin_url}")
        with col3:
            st.button(f"Archive", key=f"archive_{linkedin_url}")

# Get all profiles
def get_all_profiles():
    try:
        profiles = profile_service.get_all_profiles()
        return profiles
    except Exception as e:
        st.error(f"Error getting profiles: {str(e)}")
        return []

# Initialize session storage
SessionStorage.initialize_storage()

# Main dashboard content
api_keys_set, missing_keys = check_api_keys()

if not api_keys_set:
    st.warning("⚠️ Please set up your API keys in the Settings page.")
    st.markdown(f"Missing API keys: {', '.join(missing_keys)}")
    st.stop()

# Initialize session state
if "refresh_result" not in st.session_state:
    st.session_state["refresh_result"] = None

if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = None

# Tabs for dashboard sections
tab1, tab2, tab3 = st.tabs(["Overview", "Recent Changes", "All Profiles"])

with tab1:
    st.subheader("Dashboard Overview")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        st.button("Refresh All Profiles", on_click=refresh_all_profiles)
    with col2:
        if st.session_state["last_refresh"]:
            last_refresh_time = datetime.fromisoformat(st.session_state["last_refresh"])
            st.info(f"Last refreshed: {last_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Display metrics
    profiles = get_all_profiles()
    founder_changes = get_founder_changes()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Profiles Tracked", value=len(profiles))
    with col2:
        st.metric(label="Founder Transitions", value=len(founder_changes))
    with col3:
        tracked_days = 30  # Placeholder
        st.metric(label="Days Tracking", value=tracked_days)
    
    # Display refresh results if available
    if st.session_state["refresh_result"]:
        result = st.session_state["refresh_result"]
        
        st.subheader("Last Refresh Results")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Profiles Checked", value=result.get("success", 0))
        with col2:
            st.metric(label="Changes Detected", value=result.get("changes_detected", 0))
        with col3:
            st.metric(label="Founder Changes", value=result.get("founder_changes", 0))
        with col4:
            st.metric(label="Failed Updates", value=result.get("failed", 0))
    
    # Display recent activity chart
    st.subheader("Recent Activity")
    
    # Generate sample data for demonstration
    if not founder_changes:
        # Use mock data if no real data available
        dates = [(datetime.now() - timedelta(days=x)).strftime("%Y-%m-%d") for x in range(30)]
        activity = [random.randint(0, 3) for _ in range(30)]
        df = pd.DataFrame({"date": dates, "changes": activity})
    else:
        # Use real data
        change_dates = [
            datetime.fromisoformat(change.get("detected_date", "")).strftime("%Y-%m-%d")
            for change in founder_changes
            if "detected_date" in change
        ]
        
        # Count changes by date
        date_counts = {}
        for date in change_dates:
            if date in date_counts:
                date_counts[date] += 1
            else:
                date_counts[date] = 1
        
        # Create dataframe
        df = pd.DataFrame({
            "date": list(date_counts.keys()),
            "changes": list(date_counts.values())
        })
    
    # Sort by date
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    # Create chart
    fig = px.bar(
        df,
        x="date",
        y="changes",
        title="Profile Changes by Date",
        labels={"date": "Date", "changes": "Number of Changes"},
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Changes",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Recent Founder Transitions")
    
    founder_changes = get_founder_changes(limit=10)
    
    if not founder_changes:
        st.info("No founder transitions detected yet. Add profiles and refresh to start tracking changes.")
    else:
        for change in founder_changes:
            render_change_card(change)

with tab3:
    st.subheader("All Tracked Profiles")
    
    profiles = get_all_profiles()
    
    if not profiles:
        st.info("No profiles being tracked yet. Add profiles on the Upload Profiles page.")
    else:
        # Create dataframe for display
        profiles_data = []
        for profile in profiles:
            profiles_data.append({
                "Name": profile.full_name,
                "Current Title": profile.current_title,
                "Current Company": profile.current_company,
                "Previous Title": profile.previous_title,
                "Previous Company": profile.previous_company,
                "Last Checked": format_iso_date(profile.last_checked_date),
                "LinkedIn URL": profile.linkedin_url
            })
        
        df = pd.DataFrame(profiles_data)
        
        # Add search and filters
        search = st.text_input("Search profiles", "")
        
        if search:
            df = df[
                df["Name"].str.contains(search, case=False) |
                df["Current Title"].str.contains(search, case=False) |
                df["Current Company"].str.contains(search, case=False)
            ]
        
        # Display table
        st.dataframe(df, use_container_width=True) 