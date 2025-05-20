import os
from pathlib import Path

def update_env_file():
    """Update the .env file with consistent environment variable names."""
    env_path = Path(".env")
    
    # Read existing .env content if it exists
    env_vars = {}
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    
    # Ensure consistent naming
    # If SERPAPI_KEY exists and SERPAPI_API_KEY doesn't, copy the value
    if "SERPAPI_KEY" in env_vars and "SERPAPI_API_KEY" not in env_vars:
        env_vars["SERPAPI_API_KEY"] = env_vars["SERPAPI_KEY"]
    
    # Write back to .env
    with open(env_path, "w") as f:
        f.write("# API Keys\n")
        for key, value in env_vars.items():
            if key != "SERPAPI_KEY":  # Skip the old key
                f.write(f"{key}={value}\n")
    
    print("Environment variables updated successfully!")

if __name__ == "__main__":
    update_env_file() 