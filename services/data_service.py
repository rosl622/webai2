import requests
import json
import os
import streamlit as st
from datetime import datetime

# --- Direct Supabase REST API Client (No external libraries needed) ---
class SimpleSupabaseClient:
    def __init__(self, url, key):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation" # Return data after insert/update
        }

    def _get_url(self, table):
        return f"{self.url}/rest/v1/{table}"

    def select(self, table, select="*", order=None, limit=None, **kwargs):
        """
        Generic select. kwargs are treated as equality filters (eq).
        Example: client.select("feeds", category="IT")
        """
        params = {"select": select}
        
        # Simple equality filters
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
            # 201 Created or 409 Conflict
            if response.status_code == 409: # Conflict
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Supabase Insert Error: {e}")
            return None

    def upsert(self, table, data, on_conflict=None):
        """
        Upsert requires the header Prefer: resolution=merge-duplicates.
        """
        headers = self.headers.copy()
        headers["Prefer"] = "return=representation,resolution=merge-duplicates"
        if on_conflict:
            headers["On-Conflict"] = on_conflict # Not standard PostgREST header but specific to some clients? 
            # Actually PostgREST handles upsert via POST with ?on_conflict query param usually or just merge-duplicates prefer
        
        # For standard PostgREST: POST with Prefer: resolution=merge-duplicates matches on PK.
        # If we need to match on other columns, we usually specify ?on_conflict=col1,col2 in URL params
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

# --- Init Client ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return SimpleSupabaseClient(url, key)

db = init_supabase()

# --- Feeds ---
def get_feeds(category="IT"):
    if not db: return []
    data = db.select("feeds", category=category)
    return [item['url'] for item in data]

def add_feed(url, category="IT"):
    if not db: return False
    # Check strict uniqueness locally or rely on DB constraint
    # Let's request to insert
    res = db.insert("feeds", {"category": category, "url": url})
    return res is not None

def remove_feed(url, category="IT"):
    if not db: return False
    return db.delete("feeds", category=category, url=url)

# --- Archive ---
def get_archive(date_str, category="IT"):
    if not db: return None
    data = db.select("archives", select="content", date=date_str, category=category)
    if data:
        return data[0]['content']
    return None

def save_archive(date_str, content, category="IT"):
    if not db: return
    data = {
        "date": date_str,
        "category": category,
        "content": content
    }
    # Upsert matching on date, category
    db.upsert("archives", data, on_conflict="date,category")

# --- Stats ---
def get_stats():
    if not db: return {"total_views": 0, "daily_views": {}}
    
    # 1. Global
    g_data = db.select("global_stats", key="total_views")
    total_views = g_data[0]['value'] if g_data else 0
    
    # 2. Daily (last 30)
    d_data = db.select("daily_stats", order="date.desc", limit=30)
    daily_views = {item['date']: item['views'] for item in d_data}
    
    return {
        "total_views": total_views,
        "daily_views": daily_views
    }

def increment_views():
    if not db: return
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Total Views
    # Direct SQL increment is hard via REST without RPC.
    # Read-Modify-Write is easiest here.
    curr_global = db.select("global_stats", key="total_views")
    if curr_global:
        new_val = curr_global[0]['value'] + 1
        db.update("global_stats", {"value": new_val}, key="total_views")
    else:
        db.insert("global_stats", {"key": "total_views", "value": 1})
        
    # 2. Daily Views
    curr_daily = db.select("daily_stats", date=today)
    if curr_daily:
        new_val = curr_daily[0]['views'] + 1
        db.update("daily_stats", {"views": new_val}, date=today)
    else:
        db.insert("daily_stats", {"date": today, "views": 1})


