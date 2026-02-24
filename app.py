import streamlit as st
import datetime
import pandas as pd
import json
import re
from services import data_service, rss_service, gemini_service

# =============================================
# PAGE CONFIG (must be first)
# =============================================
st.set_page_config(
    page_title="Eric's AI Newsroom",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# UTILS
# =============================================
def load_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def clean_text(text):
    if not text:
        return ""
    cleaned = str(text).strip()
    if cleaned.startswith("['") and cleaned.endswith("']"):
        cleaned = cleaned[2:-2]
    elif cleaned.startswith('["') and cleaned.endswith('"]'):
        cleaned = cleaned[2:-2]
    cleaned = cleaned.replace("\\n", "\n")
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', cleaned)
    return cleaned

# Load CSS
try:
    load_css("assets/style.css")
except FileNotFoundError:
    st.warning("CSS file not found.")


# SESSION STATE
# =============================================
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'view_counted' not in st.session_state:
    st.session_state.view_counted = False
if 'page' not in st.session_state:
    st.session_state.page = "IT"

# =============================================
# PAGE ROUTING (via session state)
# =============================================
page = st.session_state.page
if page not in ["IT", "MVNO", "KSTARTUP", "ADMIN"]:
    page = "IT"

# =============================================
# FIXED ADMIN GEAR ICON (top-right)
# =============================================
# Admin gear icon SVG (used in sidebar)
gear_svg = """<svg width="13" height="13" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="2.2"
     stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="3"/>
  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06
           a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09
           A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83
           l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4
           h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1
           2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1
           4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1
           2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0
           1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
</svg>"""

# =============================================
# SIDEBAR
# =============================================
st.logo("assets/logo.svg")

stats = data_service.get_stats()
today_key = datetime.datetime.now().strftime('%Y-%m-%d')
today_views = stats['daily_views'].get(today_key, 0)

# Nav items — labels shortened, no "Newsroom"
nav_items = [
    ("IT",       "📡", "IT"),
    ("MVNO",     "📱", "MVNO"),
    ("KSTARTUP", "🚀", "K-STARTUP"),
]

# Render nav buttons using Streamlit buttons (no new tab issues)
st.sidebar.markdown('<span class="nav-section-label">Newsrooms</span>', unsafe_allow_html=True)

for key, icon, label in nav_items:
    is_active = (page == key)
    btn_label = f"{icon} {label}"
    # Use custom HTML for active state styling
    if is_active:
        active_class_map = {"IT": "active-it", "MVNO": "active-mvno", "KSTARTUP": "active-kst"}
        st.sidebar.markdown(
            f'<div class="nav-btn active {active_class_map[key]}"><span class="nav-icon">{icon}</span>{label}</div>',
            unsafe_allow_html=True
        )
    else:
        if st.sidebar.button(btn_label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

nav_stats_html = f"""
<div class="nav-stats">
    Total Views&nbsp;&nbsp;<span class="stat-value">{stats['total_views']}</span><br>
    Today&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="stat-value">{today_views}</span>
</div>
"""
st.sidebar.markdown(nav_stats_html, unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div class="sidebar-footer">
    <a href="mailto:sanghoon.e.kim@gmail.com" class="footer-link" target="_self">
        <svg class="footer-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
        </svg>
        sanghoon.e.kim@gmail.com
    </a>
    <a href="https://linkedin.com/in/erickiiim" target="_blank" class="footer-link">
        <svg class="footer-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
        </svg>
        Eric Kim
    </a>
    <div class="footer-divider"></div>
</div>
""", unsafe_allow_html=True)

# Admin button in sidebar footer (gear icon + label)
if st.sidebar.button("⚙️  Admin", key="admin_sidebar_btn"):
    st.session_state.page = "ADMIN"
    st.rerun()

# =============================================
# COUNT VIEWS ONCE PER SESSION
# =============================================
if not st.session_state.view_counted:
    data_service.increment_views()
    st.session_state.view_counted = True

# =============================================
# NEWSROOM RENDERER — Option 3 Layout
# =============================================
CATEGORY_CONFIG = {
    "IT": {
        "title": "IT Trends Daily Briefing",
        "icon": "📡",
        "css_class": "it",
        "badge_class": "",
        "section_colors": {
            "headline": ("🟦", "#1D4ED8"),
            "trends":   ("💠", "#0369A1"),
            "insight":  ("🏙️", "#4F46E5"),
        }
    },
    "MVNO": {
        "title": "MVNO Trends Daily Briefing",
        "icon": "📱",
        "css_class": "mvno",
        "badge_class": "date-badge-mvno",
        "section_colors": {
            "headline": ("🟩", "#065F46"),
            "trends":   ("💠", "#0369A1"),
            "insight":  ("🏙️", "#1E40AF"),
        }
    },
    "KSTARTUP": {
        "title": "K-startup Daily Briefing",
        "icon": "🚀",
        "css_class": "kstartup",
        "badge_class": "date-badge-kstartup",
        "section_colors": {
            "headline": ("🟧", "#92400E"),
            "trends":   ("💠", "#B91C1C"),
            "insight":  ("🌱", "#065F46"),
        }
    },
}

def render_newsroom(category):
    cfg = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG["IT"])

    # --- Header row: icon + title + date badge ---
    selected_date = st.date_input("날짜", datetime.date.today(), label_visibility="collapsed")
    date_str = selected_date.strftime("%Y-%m-%d")

    st.markdown(
        f'<div class="page-title-row">'
        f'<h1>{cfg["icon"]} {cfg["title"]}</h1>'
        f'<span class="date-badge {cfg["badge_class"]}">'
        f'<span class="live-dot"></span>{date_str}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    # --- Load content ---
    content = data_service.get_archive(date_str, category=category)

    if content:
        try:
            data = json.loads(content)
            sc = cfg["section_colors"]

            # --- HEADLINE (full width) ---
            st.markdown(
                f'<div class="section-header">'
                f'<span class="section-label">{sc["headline"][0]} 오늘의 메인 헤드라인</span>'
                f'<div class="section-line"></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="news-box box-headline {cfg["css_class"]}">'
                f'<div class="news-content">{clean_text(data.get("headline", ""))}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # --- TRENDS + INSIGHT (2-column grid) ---
            col_l, col_r = st.columns(2)

            with col_l:
                st.markdown(
                    f'<div class="section-header">'
                    f'<span class="section-label">{sc["trends"][0]} 주요 트렌드 &amp; 이슈</span>'
                    f'<div class="section-line"></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div class="news-box box-trends {cfg["css_class"]}">'
                    f'<div class="news-content">{clean_text(data.get("trends", ""))}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with col_r:
                insight_label = "🌱 스타트업 생태계 전망" if category == "KSTARTUP" else f'{sc["insight"][0]} 기술적 통찰과 전망'
                st.markdown(
                    f'<div class="section-header">'
                    f'<span class="section-label">{insight_label}</span>'
                    f'<div class="section-line"></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div class="news-box box-insight {cfg["css_class"]}">'
                    f'<div class="news-content">{clean_text(data.get("insight", ""))}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        except json.JSONDecodeError:
            st.markdown(content)
    else:
        st.info(f"No {category} briefing available for {date_str}.")
        if date_str == datetime.date.today().strftime("%Y-%m-%d"):
            st.info("Check back later or ask the admin to run the analysis!")

    st.markdown("---")
    render_comments(f"{category}_{date_str}")


# =============================================
# COMMENTS
# =============================================
def render_comments(page_id):
    st.subheader("💬 Comments")
    comments = data_service.get_comments(page_id)
    if comments:
        for c in comments:
            col1, col2 = st.columns([8, 1])
            with col1:
                st.markdown(
                    f"**{c['nickname']}** "
                    f"<span style='color:#94A3B8; font-size:0.8em'>"
                    f"({c['created_at'][:16].replace('T', ' ')})</span>",
                    unsafe_allow_html=True
                )
                st.markdown(c['content'])
            with col2:
                with st.popover("🗑️"):
                    pwd = st.text_input("Password", key=f"del_pwd_{c['id']}", type="password")
                    if st.button("Delete", key=f"del_btn_{c['id']}"):
                        if data_service.delete_comment(c['id'], pwd):
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error("Wrong Password")
            st.divider()
    else:
        st.info("No comments yet. Be the first!")

    with st.form(key=f"comment_form_{page_id}"):
        st.markdown("### Leave a Comment")
        c1, c2 = st.columns(2)
        with c1:
            nick = st.text_input("Nickname")
        with c2:
            pwd = st.text_input("Password (for deletion)", type="password")
        content = st.text_area("Comment")
        if st.form_submit_button("Post Comment"):
            if nick and pwd and content:
                if data_service.add_comment(page_id, nick, pwd, content):
                    st.success("Comment posted!")
                    st.rerun()
                else:
                    st.error("Failed to post comment.")
            else:
                st.warning("Please fill all fields.")


# =============================================
# ADMIN DASHBOARD
# =============================================
def render_admin():
    if st.button("← Back to Newsroom", key="admin_back_btn"):
        st.session_state.page = "IT"
        st.rerun()
    st.title("⚙️ Admin Dashboard")

    secret_password = st.secrets.get("ADMIN_PASSWORD", "admin123")

    if not st.session_state.admin_logged_in:
        st.markdown("---")
        _, col, _ = st.columns([1, 2, 1])
        with col:
            password = st.text_input("Enter Admin Password", type="password", placeholder="Password")
            if st.button("Login", use_container_width=True):
                if password == secret_password:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        return

    st.markdown("---")
    res_category = st.radio("Select Target Newsroom", ["IT", "MVNO", "KSTARTUP"], horizontal=True)
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        f"RSS Feeds ({res_category})",
        f"Analysis Trigger ({res_category})",
        "Statistics"
    ])

    with tab1:
        st.subheader(f"Manage RSS Feeds — {res_category}")
        feeds = data_service.get_feeds(category=res_category)
        new_feed = st.text_input("Add new RSS URL", placeholder="https://...")
        if st.button("Add Feed"):
            if new_feed and new_feed.startswith("http"):
                if data_service.add_feed(new_feed, category=res_category):
                    st.success(f"Feed added to {res_category}!")
                    st.rerun()
                else:
                    st.warning("Feed already exists.")
            else:
                st.error("Invalid URL")
        st.markdown("#### Current Feeds")
        if not feeds:
            st.info("No feeds found for this category.")
        for feed in feeds:
            col1, col2 = st.columns([5, 1])
            col1.code(feed, language=None)
            if col2.button("Remove", key=f"{res_category}_{feed}"):
                data_service.remove_feed(feed, category=res_category)
                st.rerun()

    with tab2:
        st.subheader(f"Run {res_category} Analysis")
        default_key = st.secrets.get("GEMINI_API_KEY", "")
        gemini_key = st.text_input("Gemini API Key", value=default_key, type="password")
        if st.button("🚀 Fetch & Analyze Now", use_container_width=True):
            if not gemini_key:
                st.error("Please provide a Gemini API Key.")
            else:
                with st.spinner(f"Fetching {res_category} RSS feeds..."):
                    feeds = data_service.get_feeds(category=res_category)
                    news_items = rss_service.fetch_all_feeds(feeds)
                    st.write(f"Fetched **{len(news_items)}** items.")
                if news_items:
                    with st.spinner("Analyzing with Gemini AI..."):
                        gemini_service.configure_gemini(gemini_key)
                        summary = gemini_service.generate_news_summary(news_items, category=res_category)
                        today_str = datetime.date.today().strftime("%Y-%m-%d")
                        data_service.save_archive(today_str, summary, category=res_category)
                        st.success(f"Analysis Complete! Saved to {res_category} archive.")
                        try:
                            data = json.loads(summary)
                            st.markdown("#### Preview")
                            st.markdown(
                                f'<div class="news-box box-headline">'
                                f'<div class="news-content">{clean_text(data.get("headline", ""))}</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        except Exception:
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


# =============================================
# ROUTING
# =============================================
if page == "IT":
    render_newsroom("IT")
elif page == "MVNO":
    render_newsroom("MVNO")
elif page == "KSTARTUP":
    render_newsroom("KSTARTUP")
elif page == "ADMIN":
    render_admin()
else:
    render_newsroom("IT")
