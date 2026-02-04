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
def get_feeds(category="IT"):
    data = _load_json(FEEDS_FILE, default={})
    
    # Migration: If data is a list (old format), wrap it in "IT"
    if isinstance(data, list):
        data = {"IT": data, "MVNO": []}
        _save_json(FEEDS_FILE, data)
        
    return data.get(category, [])

def add_feed(url, category="IT"):
    data = _load_json(FEEDS_FILE, default={})
    
    # Migration logic same as above
    if isinstance(data, list):
        data = {"IT": data, "MVNO": []}
    
    # Ensure category exists
    if category not in data:
        data[category] = []
        
    if url not in data[category]:
        data[category].append(url)
        _save_json(FEEDS_FILE, data)
        return True
    return False

def remove_feed(url, category="IT"):
    data = _load_json(FEEDS_FILE, default={})
    
    if isinstance(data, list):
        data = {"IT": data, "MVNO": []}
        
    if category in data and url in data[category]:
        data[category].remove(url)
        _save_json(FEEDS_FILE, data)
        return True
    return False

# --- Archive ---
def get_archive(date_str, category="IT"):
    """
    date_str format: YYYY-MM-DD
    category: "IT" or "MVNO"
    """
    archive = _load_json(ARCHIVE_FILE)
    # Key format: "2024-02-04" (for IT default) or "2024-02-04_MVNO"
    key = date_str if category == "IT" else f"{date_str}_{category}"
    return archive.get(key)

def save_archive(date_str, content, category="IT"):
    archive = _load_json(ARCHIVE_FILE)
    key = date_str if category == "IT" else f"{date_str}_{category}"
    archive[key] = content
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
