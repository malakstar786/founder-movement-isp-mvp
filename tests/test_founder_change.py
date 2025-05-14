from src.api.session_storage import SessionStorage
from src.services.profile_service import ProfileService

# Initialize session state (simulate Streamlit session)
SessionStorage.initialize_storage()
profile_service = ProfileService()

test_url = "https://www.linkedin.com/in/test-founder"

# 1. Add the profile (should be non-founder)
success, msg = profile_service.add_profile(test_url)
print("Add profile:", success, msg)

# 2. Refresh the profile (should now simulate a founder change)
success, msg, change = profile_service.refresh_profile(test_url)
print("Refresh profile:", success, msg)
if change:
    print("Change detected:", change.to_dict())
    print("AI Insight:", change.ai_insight)  # The insight should already be generated

# 3. Print all changes
print("All changes:", SessionStorage.get_all_changes()) 