import streamlit as st
import datetime
import time
import pandas as pd
import json
from services import data_service, rss_service, gemini_service

# --- Utils ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def clean_text(text):
    if not text:
        return ""
    # 1. Convert to string and strip surrounding whitespace
    cleaned = str(text).strip()
    
    # 2. Remove potential list artifacts (start/end brackets and quotes if it looks like a python list representation)
    if cleaned.startswith("['") and cleaned.endswith("']"):
        cleaned = cleaned[2:-2]
    elif cleaned.startswith('["') and cleaned.endswith('"]'):
        cleaned = cleaned[2:-2]
        
    # 3. Handle escaped newlines (turn literal \n into legitimate newline characters)
    cleaned = cleaned.replace("\\n", "\n")
    
    # 4. Remove Markdown Bold artifacts (**) as requested
    cleaned = cleaned.replace("**", "")
    
    return cleaned

# --- Page Config ---
st.set_page_config(
    page_title="AI IT Newsroom",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
try:
    load_css("assets/style.css")
except FileNotFoundError:
    st.warning("CSS file not found. Styles might be missing.")

# --- Session State Init ---
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# --- Sidebar ---
st.sidebar.title("📰 AI IT Newsroom")
page = st.sidebar.radio("Go to", ["Newsroom", "Admin Dashboard"])

# Show stats in sidebar
stats = data_service.get_stats()
st.sidebar.divider()
st.sidebar.markdown(f"**Total Views:** {stats['total_views']}")
st.sidebar.markdown(f"**Today's Views:** {stats['daily_views'].get(datetime.datetime.now().strftime('%Y-%m-%d'), 0)}")

# --- Main Functions ---

def render_newsroom():
    st.title("IT Trends Daily Briefing")
    
    # Date Picker
    selected_date = st.date_input("Select Date", datetime.date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # Load Archive
    content = data_service.get_archive(date_str)
    
    if content:
        st.markdown("---")
        try:
            # Attempt to parse JSON
            data = json.loads(content)
            
            # 1. Headline Box
            st.markdown("<h3>🟦 오늘의 메인 헤드라인</h3>", unsafe_allow_html=True)
            head_html = f"""
            <div class="news-box box-headline">
                <div class="news-content">{clean_text(data.get('headline', ''))}</div>
            </div>
            """
            st.markdown(head_html, unsafe_allow_html=True)

            # 2. Trends Box
            st.markdown("<h3>💠 주요 트렌드 & 이슈</h3>", unsafe_allow_html=True)
            trend_html = f"""
            <div class="news-box box-trends">
                <div class="news-content">{clean_text(data.get('trends', ''))}</div>
            </div>
            """
            st.markdown(trend_html, unsafe_allow_html=True)

            # 3. Insight Box
            st.markdown("<h3>🏙️ 기술적 통찰과 전망</h3>", unsafe_allow_html=True)
            insight_html = f"""
            <div class="news-box box-insight">
                <div class="news-content">{clean_text(data.get('insight', ''))}</div>
            </div>
            """
            st.markdown(insight_html, unsafe_allow_html=True)

        except json.JSONDecodeError:
            # Fallback for old archive data (which is plain markdown)
            st.markdown(content)

    else:
        st.info(f"No briefing available for {date_str}.")
        if date_str == datetime.date.today().strftime("%Y-%m-%d"):
            st.info("Check back later or ask the admin to run the analysis!")

    # Increment Views (only if it's the main view and not a refresh spam - simple check)
    # in a real app create a more robust counter
    if 'view_counted' not in st.session_state:
        data_service.increment_views()
        st.session_state.view_counted = True

def render_admin():
    st.title("Admin Dashboard")
    
    # Auth
    # Check if password is in secrets
    secret_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    
    if not st.session_state.admin_logged_in:
        password = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if password == secret_password:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return

    # Tabs
    tab1, tab2, tab3 = st.tabs(["RSS Feeds", "Analysis Trigger", "Statistics"])
    
    with tab1:
        st.subheader("Manage RSS Feeds")
        feeds = data_service.get_feeds()
        
        # Add Feed
        new_feed = st.text_input("Add new RSS URL")
        if st.button("Add Feed"):
            if new_feed and new_feed.startswith("http"):
                if data_service.add_feed(new_feed):
                    st.success("Feed added!")
                    st.rerun()
                else:
                    st.warning("Feed already exists.")
            else:
                st.error("Invalid URL")
        
        # List Feeds
        st.markdown("### Current Feeds")
        for feed in feeds:
            col1, col2 = st.columns([4, 1])
            col1.text(feed)
            if col2.button("Remove", key=feed):
                data_service.remove_feed(feed)
                st.rerun()

    with tab2:
        st.subheader("Run Analysis")
        
        # Try to get key from secrets first
        default_key = st.secrets.get("GEMINI_API_KEY", "")
        
        gemini_key = st.text_input("Gemini API Key", value=default_key, type="password", help="Enter your Google Gemini API Key. If set in secrets.toml, it will appear here.")
        
        if st.button("Fetch & Analyze Now"):
            if not gemini_key:
                st.error("Please provide a Gemini API Key.")
            else:
                with st.spinner("Fetching RSS feeds..."):
                    feeds = data_service.get_feeds()
                    news_items = rss_service.fetch_all_feeds(feeds)
                    st.write(f"Fetched {len(news_items)} items.")
                
                with st.spinner("Analyzing with Gemini AI... (This may take a moment)"):
                    gemini_service.configure_gemini(gemini_key)
                    # Helper to display boxed content
                    def display_boxed_content(content_str):
                        try:
                            # Attempt to parse JSON
                            data = json.loads(content_str)
                            
                            # 1. Headline Box
                            st.markdown("<h3>🟦 오늘의 메인 헤드라인</h3>", unsafe_allow_html=True)
                            head_html = f"""
                            <div class="news-box box-headline">
                                <div class="news-content">{clean_text(data.get('headline', ''))}</div>
                            </div>
                            """
                            st.markdown(head_html, unsafe_allow_html=True)

                            # 2. Trends Box
                            st.markdown("<h3>💠 주요 트렌드 & 이슈</h3>", unsafe_allow_html=True)
                            trend_html = f"""
                            <div class="news-box box-trends">
                                <div class="news-content">{clean_text(data.get('trends', ''))}</div>
                            </div>
                            """
                            st.markdown(trend_html, unsafe_allow_html=True)

                            # 3. Insight Box
                            st.markdown("<h3>🏙️ 기술적 통찰과 전망</h3>", unsafe_allow_html=True)
                            insight_html = f"""
                            <div class="news-box box-insight">
                                <div class="news-content">{clean_text(data.get('insight', ''))}</div>
                            </div>
                            """
                            st.markdown(insight_html, unsafe_allow_html=True)
                            
                        except json.JSONDecodeError:
                            # Fallback to legacy markdown if JSON fails
                            st.error("Failed to parse structured data. Showing raw output:")
                            st.markdown(content_str)

                    summary = gemini_service.generate_news_summary(news_items)
                    
                    # Save for today
                    today_str = datetime.date.today().strftime("%Y-%m-%d")
                    data_service.save_archive(today_str, summary)
                    
                    st.success("Analysis Complete! Saved to daily archive.")
                    st.markdown("### Preview")
                    display_boxed_content(summary)

    with tab3:
        st.subheader("Traffic Stats")
        stats_data = data_service.get_stats()
        daily_views = stats_data.get("daily_views", {})
        
        if daily_views:
            df = pd.DataFrame(list(daily_views.items()), columns=['Date', 'Views'])
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            
            st.line_chart(df.set_index('Date'))
        else:
            st.info("No traffic data yet.")

# --- Routing ---
if page == "Newsroom":
    render_newsroom()
elif page == "Admin Dashboard":
    render_admin()

