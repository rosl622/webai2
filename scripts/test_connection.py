import streamlit as st
from supabase import create_client, Client
import sys

st.title("Supabase Connection Test")

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    
    st.write(f"Supabase URL: `{url}`")
    st.write(f"Supabase Key: `{'*' * len(key)}` (Hidden)")
    
    supabase: Client = create_client(url, key)
    
    # Try to select from feeds table (should be empty or have data)
    st.info("Attempting to connect to 'feeds' table...")
    response = supabase.table("feeds").select("*").limit(1).execute()
    
    st.success("✅ Connection Successful!")
    st.write("Response:", response)
    
except Exception as e:
    st.error(f"❌ Connection Failed: {e}")
    st.write("Please check your secrets.toml file and ensure you ran the SQL setup queries.")
