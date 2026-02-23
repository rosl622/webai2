"""
auto_fetch.py
-------------
매일 자동으로 IT / MVNO / K-startup 뉴스를 fetch하고 Gemini로 분석 후 Supabase에 저장합니다.
Windows 작업 스케줄러(Task Scheduler)에 등록하여 매일 원하는 시간에 실행하세요.

실행 방법 (수동 테스트):
    python auto_fetch.py

로그 파일: auto_fetch.log (같은 폴더에 저장)
"""

import datetime
import json
import os
import sys
import tomllib  # Python 3.11+; 하위 버전은 pip install tomli 후 import tomli as tomllib
import logging

# --- 로그 설정 ---
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_fetch.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# --- secrets 읽기: 환경변수(GitHub Actions) 우선, 없으면 secrets.toml(로컬) ---
def load_secrets():
    # 1) GitHub Actions: 환경변수에서 읽기
    env_key = os.environ.get("GEMINI_API_KEY")
    env_url = os.environ.get("SUPABASE_URL")
    env_sb_key = os.environ.get("SUPABASE_KEY")

    if env_key and env_url and env_sb_key:
        log.info("환경변수에서 secrets 로드 (GitHub Actions 모드)")
        return {
            "GEMINI_API_KEY": env_key,
            "SUPABASE_URL": env_url,
            "SUPABASE_KEY": env_sb_key,
        }

    # 2) 로컬 실행: secrets.toml에서 읽기
    secrets_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        ".streamlit",
        "secrets.toml",
    )
    if not os.path.exists(secrets_path):
        log.error(f"secrets.toml not found at: {secrets_path}")
        sys.exit(1)
    log.info("secrets.toml에서 secrets 로드 (로컬 모드)")
    with open(secrets_path, "rb") as f:
        return tomllib.load(f)

# --- Supabase direct client (Streamlit 의존성 제거) ---
import requests

class SupabaseClient:
    def __init__(self, url, key):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def select(self, table, **kwargs):
        params = {"select": "*"}
        for k, v in kwargs.items():
            params[k] = f"eq.{v}"
        r = requests.get(f"{self.url}/rest/v1/{table}", headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()

    def upsert(self, table, data, on_conflict=None):
        headers = self.headers.copy()
        headers["Prefer"] = "return=representation,resolution=merge-duplicates"
        params = {}
        if on_conflict:
            params["on_conflict"] = on_conflict
        r = requests.post(f"{self.url}/rest/v1/{table}", headers=headers, json=data, params=params)
        r.raise_for_status()
        return r.json()

# --- RSS fetch (rss_service.py 재사용) ---
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services import rss_service, gemini_service

def get_feeds(db, category):
    rows = db.select("feeds", category=category)
    return [row["url"] for row in rows]

def save_archive(db, date_str, content, category):
    db.upsert(
        "archives",
        {"date": date_str, "category": category, "content": content},
        on_conflict="date,category",
    )

# --- 메인 실행 ---
def run():
    log.info("=" * 50)
    log.info("Auto-fetch 시작")

    secrets = load_secrets()
    gemini_key = secrets.get("GEMINI_API_KEY", "")
    supabase_url = secrets.get("SUPABASE_URL", "")
    supabase_key = secrets.get("SUPABASE_KEY", "")

    if not gemini_key or not supabase_url or not supabase_key:
        log.error("API 키가 secrets.toml에 없습니다. 종료.")
        sys.exit(1)

    db = SupabaseClient(supabase_url, supabase_key)
    gemini_service.configure_gemini(gemini_key)

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    log.info(f"대상 날짜: {today_str}")

    categories = ["IT", "MVNO", "KSTARTUP"]

    for category in categories:
        log.info(f"--- [{category}] 처리 시작 ---")
        try:
            feeds = get_feeds(db, category)
            if not feeds:
                log.warning(f"[{category}] RSS 피드가 없습니다. 건너뜁니다.")
                continue

            log.info(f"[{category}] {len(feeds)}개 피드 fetch 중...")
            news_items = rss_service.fetch_all_feeds(feeds)
            log.info(f"[{category}] {len(news_items)}개 뉴스 수집 완료")

            if not news_items:
                log.warning(f"[{category}] 뉴스 없음. 건너뜁니다.")
                continue

            log.info(f"[{category}] Gemini 분석 중...")
            summary = gemini_service.generate_news_summary(news_items, category=category)

            # 에러 응답 체크
            try:
                parsed = json.loads(summary)
                if "Error" in parsed.get("headline", ""):
                    log.error(f"[{category}] Gemini 에러 응답: {summary}")
                    continue
            except json.JSONDecodeError:
                log.error(f"[{category}] JSON 파싱 실패: {summary[:200]}")
                continue

            save_archive(db, today_str, summary, category)
            log.info(f"[{category}] ✅ 저장 완료!")

        except Exception as e:
            log.error(f"[{category}] 오류 발생: {e}", exc_info=True)

    log.info("Auto-fetch 완료")
    log.info("=" * 50)

if __name__ == "__main__":
    run()
