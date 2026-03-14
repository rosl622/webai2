import json
import os
import requests
import toml

# 1. Load Secrets
secrets_path = ".streamlit/secrets.toml"
if not os.path.exists(secrets_path):
    print(f"❌ secrets.toml not found at {os.path.abspath(secrets_path)}")
    exit(1)

try:
    with open(secrets_path, "r", encoding="utf-8") as f:
        config = toml.load(f)
        
    if "secrets" in config:
        url = config["secrets"].get("SUPABASE_URL")
        key = config["secrets"].get("SUPABASE_KEY")
    else:
        url = config.get("SUPABASE_URL")
        key = config.get("SUPABASE_KEY")

    if not url or not key:
        print("❌ URL or KEY missing in secrets.toml")
        exit(1)
        
except Exception as e:
    print(f"❌ Failed to load secrets: {e}")
    exit(1)

# 2. Setup Supabase Client (Minimal)
class SimpleSupabaseClient:
    def __init__(self, url, key):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def insert(self, table, data):
        try:
            api_url = f"{self.url}/rest/v1/{table}"
            response = requests.post(api_url, headers=self.headers, json=data)
            if response.status_code == 201:
                return True
            elif response.status_code == 409:
                print(f"  Existing: {data['url']}")
                return True # Treat as success
            else:
                print(f"  Error {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"  Exception: {e}")
            return False

client = SimpleSupabaseClient(url, key)

# 3. Load Feeds
feeds_path = os.path.join("data", "feeds.json")
if not os.path.exists(feeds_path):
    print("❌ data/feeds.json not found")
    exit(1)

with open(feeds_path, "r", encoding="utf-8") as f:
    feeds_data = json.load(f)

print(f"📂 Loaded feeds.json with categories: {list(feeds_data.keys())}")

# 4. Migrate
total_success = 0
total_failed = 0

for category, urls in feeds_data.items():
    print(f"\nMigrating {category} ({len(urls)} urls)...")
    for feed_url in urls:
        print(f"  Uploading: {feed_url} ...", end=" ")
        
        payload = {
            "category": category,
            "url": feed_url
        }
        
        if client.insert("feeds", payload):
            print("✅")
            total_success += 1
        else:
            print("❌")
            total_failed += 1

print("\n------------------------------------------------")
print(f"🎉 Migration Complete!")
print(f"✅ Success: {total_success}")
print(f"❌ Failed: {total_failed}")
print("------------------------------------------------")
