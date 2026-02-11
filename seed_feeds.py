
import os
import toml
import requests

# 1. Load Secrets
secrets_path = ".streamlit/secrets.toml"
if not os.path.exists(secrets_path):
    print("❌ .streamlit/secrets.toml not found. Run this from the project root.")
    exit(1)

with open(secrets_path, "r", encoding="utf-8") as f:
    secrets = toml.load(f)

# Handle nesting
if "secrets" in secrets:
    secrets = secrets["secrets"]

SUPABASE_URL = secrets.get("SUPABASE_URL")
SUPABASE_KEY = secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL or SUPABASE_KEY missing in secrets.")
    exit(1)

# 2. Supabase Client (Minimal)
class SimpleSupabaseClient:
    def __init__(self, url, key):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def select(self, table, **kwargs):
        url = f"{self.url}/rest/v1/{table}"
        params = {"select": "*"}
        for k, v in kwargs.items():
            params[k] = f"eq.{v}"
        try:
            resp = requests.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Select Error: {e}")
            return []

    def insert(self, table, data):
        url = f"{self.url}/rest/v1/{table}"
        try:
            resp = requests.post(url, headers=self.headers, json=data)
            if resp.status_code == 409: return None # Conflict
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Insert Error: {e}")
            return None

db = SimpleSupabaseClient(SUPABASE_URL, SUPABASE_KEY)

# 3. Default Feeds
DEFAULT_FEEDS = {
    "IT": [
        "https://rss.etnews.com/Section902.xml", # ETNews SW/Startups
        "https://www.zdnet.co.kr/rss/all",       # ZDNet Korea All
        "https://www.bloter.net/rss/all",        # Bloter
        "https://it.donga.com/feeds/rss/news/",  # IT Donga
    ],
    "MVNO": [
        "https://www.yna.co.kr/rss/economy/it.xml", # Yonhap IT (General Telecom)
        "https://rss.etnews.com/Section903.xml",    # ETNews Communications/Broadcasting
        # Specific MVNO feeds are rare, using telecom sections
    ]
}

def seed_feeds():
    print("🌱 Seeding RSS Feeds...")
    
    for category, urls in DEFAULT_FEEDS.items():
        print(f"\nChecking {category} feeds...")
        current_feeds = db.select("feeds", category=category)
        existing_urls = {item['url'] for item in current_feeds}
        
        for url in urls:
            if url in existing_urls:
                print(f"  Existing: {url}")
            else:
                print(f"  ➕ Adding: {url}")
                db.insert("feeds", {"category": category, "url": url})
                
    print("\n✅ Seeding complete!")

if __name__ == "__main__":
    seed_feeds()
