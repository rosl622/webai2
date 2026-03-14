import toml
import os
from supabase import create_client, Client

# Manually load secrets
secrets_path = os.path.join(".streamlit", "secrets.toml")
if not os.path.exists(secrets_path):
    print("❌ secrets.toml not found")
    exit(1)

with open(secrets_path, "r") as f:
    secrets = toml.load(f)

url = secrets.get("SUPABASE_URL")
key = secrets.get("SUPABASE_KEY")

if not url or not key:
    print("❌ URL or KEY missing in secrets.toml")
    print(f"URL: {url}")
    print(f"KEY: {key}")
    exit(1)

print(f"✅ Found Credentials.")
print(f"URL: {url}")
# print(f"KEY: {key}") # Don't print key

try:
    print("Attempting to connect...")
    supabase: Client = create_client(url, key)
    
    # Try simple query
    response = supabase.table("feeds").select("count", count="exact").execute()
    
    print("✅ Connection Successful!")
    print(f"Response: {response}")
    
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    exit(1)
