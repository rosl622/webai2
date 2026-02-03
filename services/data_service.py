import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
FEEDS_FILE = os.path.join(DATA_DIR, 'feeds.json')
ARCHIVE_FILE = os.path.join(DATA_DIR, 'news_archive.json')
STATS_FILE = os.path.join(DATA_DIR, 'stats.json')

def _load_json(filepath, default=None):
    if not os.path.exists(filepath):
        return default if default is not None else {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

def _save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Feeds ---
def get_feeds():
    return _load_json(FEEDS_FILE, default=[])

def add_feed(url):
    feeds = get_feeds()
    if url not in feeds:
        feeds.append(url)
        _save_json(FEEDS_FILE, feeds)
        return True
    return False

def remove_feed(url):
    feeds = get_feeds()
    if url in feeds:
        feeds.remove(url)
        _save_json(FEEDS_FILE, feeds)
        return True
    return False

# --- Archive ---
def get_archive(date_str):
    """date_str format: YYYY-MM-DD"""
    archive = _load_json(ARCHIVE_FILE)
    return archive.get(date_str)

def save_archive(date_str, content):
    """date_str format: YYYY-MM-DD"""
    archive = _load_json(ARCHIVE_FILE)
    archive[date_str] = content
    _save_json(ARCHIVE_FILE, archive)

# --- Stats ---
def get_stats():
    return _load_json(STATS_FILE, default={"total_views": 0, "daily_views": {}})

def increment_views():
    stats = get_stats()
    stats["total_views"] += 1
    
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in stats["daily_views"]:
        stats["daily_views"][today] = 0
    stats["daily_views"][today] += 1
    
    _save_json(STATS_FILE, stats)
    return stats
