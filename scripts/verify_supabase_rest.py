import streamlit as st
import requests
import os
import toml

# Load secrets manually
secrets_path = ".streamlit/secrets.toml"
if not os.path.exists(secrets_path):
    print(f"❌ secrets.toml not found at {os.path.abspath(secrets_path)}")
    exit(1)

try:
    with open(secrets_path, "r", encoding="utf-8") as f:
        config = toml.load(f)
        
    # Check if inside [secrets] block
    if "secrets" in config:
        url = config["secrets"].get("SUPABASE_URL")
        key = config["secrets"].get("SUPABASE_KEY")
    else:
        url = config.get("SUPABASE_URL")
        key = config.get("SUPABASE_KEY")

    if not url or not key:
        print("❌ URL or KEY missing in secrets.toml")
        print(f"Keys found: {list(config.keys())}")
        exit(1)
        
except Exception as e:
    print(f"❌ Failed to load secrets: {e}")
    exit(1)

print(f"Testing Connection to: {url}")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

try:
    # Test SELECT from feeds
    print("Attempting SELECT from 'feeds'...")
    api_url = f"{url}/rest/v1/feeds?select=count"
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Connection Successful!")
        print(f"Response: {response.text}")
    else:
        print(f"❌ Connection Failed: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error: {e}")
