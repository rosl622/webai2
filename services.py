import requests
import json
import os
import streamlit as st
from datetime import datetime
import feedparser
import time
from google import genai
from google.genai import types

# ==========================================
# 1. DATABASE SERVICE (Supabase REST API)
# ==========================================

class SimpleSupabaseClient:
    def __init__(self, url, key):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def _get_url(self, table):
        return f"{self.url}/rest/v1/{table}"

    def select(self, table, select="*", order=None, limit=None, **kwargs):
        params = {"select": select}
        for k, v in kwargs.items():
            params[k] = f"eq.{v}"
        if order:
            params["order"] = order
        if limit:
            params["limit"] = limit
        try:
            response = requests.get(self._get_url(table), headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Supabase Select Error: {e}")
            return []

    def insert(self, table, data):
        try:
            response = requests.post(self._get_url(table), headers=self.headers, json=data)
            if response.status_code == 409:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Supabase Insert Error: {e}")
            return None

    def upsert(self, table, data, on_conflict=None):
        headers = self.headers.copy()
        headers["Prefer"] = "return=representation,resolution=merge-duplicates"
        params = {}
        if on_conflict:
            params["on_conflict"] = on_conflict
        try:
            response = requests.post(self._get_url(table), headers=headers, json=data, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Supabase Upsert Error: {e}")
            return None

    def delete(self, table, **kwargs):
        params = {}
        for k, v in kwargs.items():
            params[k] = f"eq.{v}"
        try:
            response = requests.delete(self._get_url(table), headers=self.headers, params=params)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Supabase Delete Error: {e}")
            return False
            
    def update(self, table, data, **kwargs):
        params = {}
        for k, v in kwargs.items():
            params[k] = f"eq.{v}"
        try:
            response = requests.patch(self._get_url(table), headers=self.headers, json=data, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Supabase Update Error: {e}")
            return None

@st.cache_resource(show_spinner=False)
def init_supabase():
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return SimpleSupabaseClient(url, key)

db = init_supabase()

def get_feeds(category="IT"):
    if not db: return []
    data = db.select("feeds", category=category)
    return [item['url'] for item in data]

def add_feed(url, category="IT"):
    if not db: return False
    existing = db.select("feeds", category=category, url=url)
    if existing: return False
    res = db.insert("feeds", {"category": category, "url": url})
    if res is None: return False
    return True

def remove_feed(url, category="IT"):
    if not db: return False
    return db.delete("feeds", category=category, url=url)

def get_archive(date_str, category="IT"):
    if not db: return None
    data = db.select("archives", select="content", date=date_str, category=category)
    if data: return data[0]['content']
    return None

def save_archive(date_str, content, category="IT"):
    if not db: return
    data = {"date": date_str, "category": category, "content": content}
    db.upsert("archives", data, on_conflict="date,category")

def get_stats():
    if not db: return {"total_views": 0, "daily_views": {}}
    g_data = db.select("global_stats", key="total_views")
    total_views = g_data[0]['value'] if g_data else 0
    d_data = db.select("daily_stats", order="date.desc", limit=30)
    daily_views = {item['date']: item['views'] for item in d_data}
    return {"total_views": total_views, "daily_views": daily_views}

def increment_views():
    if not db: return
    today = datetime.now().strftime("%Y-%m-%d")
    curr_global = db.select("global_stats", key="total_views")
    if curr_global:
        db.update("global_stats", {"value": curr_global[0]['value'] + 1}, key="total_views")
    else:
        db.insert("global_stats", {"key": "total_views", "value": 1})
    curr_daily = db.select("daily_stats", date=today)
    if curr_daily:
        db.update("daily_stats", {"views": curr_daily[0]['views'] + 1}, date=today)
    else:
        db.insert("daily_stats", {"date": today, "views": 1})

def get_comments(page_id):
    if not db: return []
    return db.select("comments", page_id=page_id, order="created_at.desc")

def add_comment(page_id, nickname, password, content):
    if not db: return False
    if not nickname or not password or not content: return False
    data = {"page_id": page_id, "nickname": nickname, "password": password, "content": content}
    return db.insert("comments", data) is not None

def delete_comment(comment_id, password):
    if not db: return False
    target = db.select("comments", id=comment_id)
    if not target: return False
    if target[0]['password'] == password:
        return db.delete("comments", id=comment_id)
    return False

# ==========================================
# 2. RSS FEED SERVICE
# ==========================================

def fetch_all_feeds(feed_urls):
    all_news = []
    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            source_title = feed.feed.get('title', 'Unknown Source')
            for entry in feed.entries[:5]:
                news_item = {
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', '#'),
                    'published': entry.get('published', entry.get('updated', '')),
                    'summary': entry.get('summary', ''),
                    'source': source_title
                }
                all_news.append(news_item)
        except Exception as e:
            print(f"Error parsing feed {url}: {e}")
            continue
    return all_news

# ==========================================
# 3. AI / GEMINI SERVICE
# ==========================================

def configure_gemini(api_key):
    global _client
    _client = genai.Client(api_key=api_key)

_client = None

def generate_news_summary(news_items, category="IT"):
    if not news_items:
        return '{"headline": "No news items to analyze.", "trends": "", "insight": ""}'

    news_text = "".join([f"- {item['title']} : {item['summary']}\n" for item in news_items])

    role_description = "IT 전문 뉴스 큐레이터"
    focus_instruction = "오늘 가장 중요한 IT 트렌드를 분석해서"

    if category == "MVNO":
        role_description = "통신 및 알뜰폰(MVNO) 산업 전문가"
        focus_instruction = "다음 키워드(MVNO, 알뜰폰, 통신사, 전파사용료, 망 도매대가)를 중심으로 관련 소식을 분석해서"
    elif category == "KSTARTUP":
        role_description = "한국 창업 생태계 및 스타트업 전문 애널리스트"
        focus_instruction = "다음 키워드(스타트업, 창업, 투자유치, VC, 액셀러레이터, 정부지원, 창업정책, K-startup, 유니콘, 시리즈A/B, 팁스, 중기부)를 중심으로 오늘의 주요 창업 생태계 동향을 분석해서"
    elif category == "VIBECODING":
        role_description = "AI 에이전트 코딩 도구 및 바이브코딩 비즈니스 전문 큐레이터"
        focus_instruction = (
            "다음 키워드(Antigravity, Claude Code, ChatGPT Codex, Cursor AI, Windsurf, "
            "GitHub Copilot, Gemini Code Assist, Amazon Q Developer, "
            "AI agent coding, vibe coding, 바이브코딩, agentic IDE, LLM 코딩, "
            "AI pair programming, 코딩 AI, 코딩 에이전트)를 중심으로 "
            "AI 코딩 도구의 최신 동향과 바이브코딩 생태계를 분석해서"
        )

    prompt = f"""
    당신은 {role_description}입니다. 
    아래 제공된 뉴스 데이터(제목 및 요약)를 바탕으로 {focus_instruction} 브리핑해주세요.
    
    [작성 규칙]
    1. 각 소식의 제목은 반드시 **[제목]** 형식으로 작성하여 강조해주세요. (이 형식이 디자인에 적용됩니다.)
    2. 제목 바로 아래 줄에 내용을 작성하고, 각 소식 사이에는 반드시 빈 줄(엔터)을 하나 추가해주세요.
    3. (매우 중요) 원본 데이터에 요약 내용이 부족하더라도, 제공된 정보를 바탕으로 문맥을 파악하여 반드시 2~3문장 이상의 상세한 기사 내용을 알차게 작성해주세요. 내용 부분이 비어있으면 절대 안 됩니다.
    4. 불필요한 기호( - , bullet point 등)는 사용하지 말고, 깔끔한 줄글 기사 형식으로 작성하세요.
    
    [형식 예시]
    **[뉴스 제목 1]**
    뉴스 내용이 여기에 옵니다. 자연스러운 문장으로 요약합니다.
    
    **[뉴스 제목 2]**
    다음 뉴스 내용이 옵니다...
    
    [뉴스 데이터]
    {news_text}
    
    [필수 요청 사항]
    반드시 아래의 **JSON 형식**으로만 응답해주세요. Markdown 포맷팅(```json 등)없이 순수 JSON 문자열만 반환하세요.
    
    **작성 지침 (매우 중요):**
    1. **절대 리스트 형식(['...'])으로 작성하지 마십시오.** 하나의 긴 문자열로 작성하세요.
    2. 줄바꿈이 필요한 곳에는 `\\n`을 사용하여 명확히 구분해 주세요.
    3. 뉴스 기사처럼 자연스럽고 전문적인 어조로 브리핑하듯 작성하세요.
    4. 형식 예시: "**[제목]** 내용입니다.\\n\\n**[다음 제목]** 다음 내용입니다..."
    
    {{
      "headline": "(가장 중요한 뉴스 1~2개. **[제목]** 형식 사용하여 작성)",
      "trends": "(카테고리별 트렌드. **[카테고리]** 형식 사용하여 작성)",
      "insight": "(기술적 전망. 전문적인 뉴스 어조로 작성)"
    }}
    
    내용은 한국어로 작성하고, 전문성 있으면서도 읽기 편한 톤으로 작성해주세요.
    """

    model_names = [
        "gemini-2.5-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
    ]

    last_error = None
    import time
    for model_name in model_names:
        for attempt in range(3): # Try each model up to 3 times
            try:
                response = _client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    ),
                )
                return response.text.replace("```json", "").replace("```", "").strip()
            except Exception as e:
                last_error = e
                # If it's a rate limit or service unavailable, wait then retry
                if "429" in str(e) or "Too Many Requests" in str(e):
                    time.sleep(60) # Wait 60s for quota to reset
                    continue
                elif "503" in str(e):
                    time.sleep(30)
                    continue
                else:
                    break # Break inner loop (do not retry this model), try next model

    return f'{{"headline": "Error: All models failed.", "trends": "Last error: {str(last_error)}", "insight": ""}}'
