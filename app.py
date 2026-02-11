import streamlit as st
import datetime
import time
import pandas as pd
import json
from services import data_service, rss_service, gemini_service

# --- Utils ---
def load_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

import re  # Added for regex operations

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
    
    # 4. Convert Markdown Bold (**text**) to HTML Strong (<strong>text</strong>)
    # This is critical because st.markdown(html) does not parse markdown inside HTML tags.
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', cleaned)
    
    return cleaned

# --- Page Config ---
# --- Page Config ---
st.set_page_config(
    page_title="Eric's AI Newsroom",
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
# --- Sidebar ---
st.logo("assets/logo.svg") # Logo without link, size handling via CSS or SVG adjustment if needed

# Sidebar Header Placeholder
sidebar_header = st.sidebar.empty()

# Navigation
page = st.sidebar.radio("Navigation", ["IT Newsroom", "MVNO Newsroom", "Admin Dashboard"], label_visibility="collapsed")

# Update Header based on selection
if page == "IT Newsroom":
    sidebar_header.title("📰 IT Newsroom")
elif page == "MVNO Newsroom":
    sidebar_header.title("📱 MVNO Newsroom")
else:
    sidebar_header.title("⚙️ Admin Dashboard")

# Show stats in sidebar
stats = data_service.get_stats()
st.sidebar.divider()
st.sidebar.markdown(f"**Total Views:** {stats['total_views']}")
st.sidebar.markdown(f"**Today's Views:** {stats['daily_views'].get(datetime.datetime.now().strftime('%Y-%m-%d'), 0)}")

# Sidebar Footer
st.sidebar.markdown("""
    <div class="sidebar-footer">
        <a href="mailto:sanghoon.e.kim@gmail.com" class="footer-link">
            <svg class="footer-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                <polyline points="22,6 12,13 2,6"></polyline>
            </svg>
            sanghoon.e.kim@gmail.com
        </a>
        <a href="https://linkedin.com/in/erickiiim" target="_blank" class="footer-link">
            <svg class="footer-icon" viewBox="0 0 24 24" fill="#0077B5" xmlns="http://www.w3.org/2000/svg">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
            </svg>
            Eric Kim
        </a>
    </div>
    """, unsafe_allow_html=True)

# --- Main Functions ---

def render_newsroom(category):
    title_prefix = "IT" if category == "IT" else "MVNO"
    st.title(f"{title_prefix} Trends Daily Briefing")
    
    # Date Picker
    selected_date = st.date_input("Select Date", datetime.date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # Load Archive
    content = data_service.get_archive(date_str, category=category)
    
    if content:
        st.markdown("---")
        try:
            # Attempt to Parse JSON
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
        st.info(f"No {category} briefing available for {date_str}.")
        if date_str == datetime.date.today().strftime("%Y-%m-%d"):
            st.info("Check back later or ask the admin to run the analysis!")

    # Increment Views
    if 'view_counted' not in st.session_state:
        data_service.increment_views()
        st.session_state.view_counted = True

def render_admin():
    st.title("Admin Dashboard")
    
    # Auth
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

    # Category Selection for Admin Actions
    st.markdown("---")
    res_category = st.radio("Select Target Newsroom", ["IT", "MVNO"], horizontal=True)
    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs([f"RSS Feeds ({res_category})", f"Analysis Trigger ({res_category})", "Statistics"])
    
    with tab1:
        st.subheader(f"Manage RSS Feeds for {res_category}")
        feeds = data_service.get_feeds(category=res_category)
        
        # Add Feed
        new_feed = st.text_input("Add new RSS URL")
        if st.button("Add Feed"):
            if new_feed and new_feed.startswith("http"):
                if data_service.add_feed(new_feed, category=res_category):
                    st.success(f"Feed added to {res_category}!")
                    st.rerun()
                else:
                    st.warning("Feed already exists.")
            else:
                st.error("Invalid URL")
        
        # List Feeds
        st.markdown("### Current Feeds")
        if not feeds:
            st.info("No feeds found for this category.")
        for feed in feeds:
            col1, col2 = st.columns([4, 1])
            col1.text(feed)
            if col2.button("Remove", key=f"{res_category}_{feed}"):
                data_service.remove_feed(feed, category=res_category)
                st.rerun()

    with tab2:
        st.subheader(f"Run {res_category} Analysis")
        
        default_key = st.secrets.get("GEMINI_API_KEY", "")
        gemini_key = st.text_input("Gemini API Key", value=default_key, type="password")
        
        if st.button("Fetch & Analyze Now"):
            if not gemini_key:
                st.error("Please provide a Gemini API Key.")
            else:
                with st.spinner(f"Fetching {res_category} RSS feeds..."):
                    feeds = data_service.get_feeds(category=res_category)
                    news_items = rss_service.fetch_all_feeds(feeds)
                    st.write(f"Fetched {len(news_items)} items.")
                
                if news_items:
                    with st.spinner("Analyzing with Gemini AI..."):
                        gemini_service.configure_gemini(gemini_key)
                        
                        # Use updated service with category
                        summary = gemini_service.generate_news_summary(news_items, category=res_category)
                        
                        # Save
                        today_str = datetime.date.today().strftime("%Y-%m-%d")
                        data_service.save_archive(today_str, summary, category=res_category)
                        
                        st.success(f"Analysis Complete! Saved to {res_category} archive.")
                        
                        # Preview helper logic (simplified inline reuse)
                        try:
                            data = json.loads(summary)
                            st.markdown("### Preview")
                            
                            st.markdown("<h3>🟦 오늘의 메인 헤드라인</h3>", unsafe_allow_html=True)
                            st.markdown(f"""
                            <div class="news-box box-headline">
                                <div class="news-content">{clean_text(data.get('headline', ''))}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            # ... (preview trends/insight omitted for brevity, implied same pattern or raw for checking)
                            
                        except:
                            st.write(summary)
                else:
                    st.warning("No news items found to analyze.")

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
if page == "IT Newsroom":
    render_newsroom("IT")
elif page == "MVNO Newsroom":
    render_newsroom("MVNO")
elif page == "Admin Dashboard":
    render_admin()

