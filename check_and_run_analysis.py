import toml
import os
import datetime
from services import data_service, rss_service, gemini_service
import streamlit as st

# Mock st.secrets for services that might use it (data_service uses st.secrets)
# We need to manually load secrets and patch st.secrets or just ensure data_service can handle it.
# data_service uses st.secrets in init_supabase.

secrets_path = ".streamlit/secrets.toml"
if os.path.exists(secrets_path):
    with open(secrets_path, "r", encoding="utf-8") as f:
        secrets = toml.load(f)
    # Flatten if needed or just assign. Streamlit secrets are dict-like.
    # The app uses st.secrets["SUPABASE_URL"] etc.
    # We can monkeypatch st.secrets
    if "secrets" in secrets:
        st.secrets = secrets["secrets"]
    else:
        st.secrets = secrets
else:
    print("❌ secrets.toml not found")
    exit(1)

# Re-init db with loaded secrets
data_service.db = data_service.init_supabase()

def run_analysis_for_category(category):
    print(f"\nChecking {category} archive for today...")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    archive = data_service.get_archive(today_str, category=category)
    if archive:
        print(f"✅ {category} archive for {today_str} already exists.")
        return
    
    print(f"⚠️ {category} archive missing. Running analysis...")
    
    # 1. Fetch Feeds
    urls = data_service.get_feeds(category=category)
    if not urls:
        print(f"❌ No feeds found for {category}")
        return

    print(f"  Fetching {len(urls)} feeds...")
    news_items = rss_service.fetch_all_feeds(urls)
    print(f"  Fetched {len(news_items)} items.")
    
    if not news_items:
        print("  No news items to analyze.")
        return

    # 2. Analyze
    print("  Analyzing with Gemini...")
    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ GEMINI_API_KEY not found in secrets")
        return

    gemini_service.configure_gemini(gemini_key)
    summary = gemini_service.generate_news_summary(news_items, category=category)
    
    # 3. Save
    if summary:
        data_service.save_archive(today_str, summary, category=category)
        print(f"✅ Saved {category} analysis for {today_str}")
    else:
        print("❌ Failed to generate summary")

if __name__ == "__main__":
    run_analysis_for_category("IT")
    run_analysis_for_category("MVNO")
