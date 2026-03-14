import os
import sys
import importlib.metadata

def print_versions():
    packages = ["supabase", "gotrue", "postgrest", "storage3", "realtime", "httpx", "pydantic"]
    print("--- Installed Versions ---")
    for pkg in packages:
        try:
            version = importlib.metadata.version(pkg)
            print(f"{pkg}: {version}")
        except importlib.metadata.PackageNotFoundError:
            print(f"{pkg}: Not Found")
    print("--------------------------")

print_versions()

# Try to import tomllib (Python 3.11+) or toml
try:
    import tomllib as toml
except ImportError:
    try:
        import toml
    except ImportError:
        print("❌ neither 'tomllib' nor 'toml' module found. Installing 'toml'...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "toml"])
        import toml

from supabase import create_client, Client

# Manually load secrets
secrets_path = os.path.join(".streamlit", "secrets.toml")
if not os.path.exists(secrets_path):
    print("❌ secrets.toml not found")
    exit(1)

with open(secrets_path, "rb") as f: # tomllib requires binary mode
    secrets = toml.load(f)

# Handle [secrets] section if present (streamlit style) or flat
if "secrets" in secrets:
    # Some users might put [secrets] block, but usually top level in secrets.toml
    # But Streamlit docs say top level. `[secrets]` is for older versions or specific configs.
    # Let's check top level first.
    pass

url = secrets.get("SUPABASE_URL")
key = secrets.get("SUPABASE_KEY")

if not url or not key:
    # Check if nested under [secrets] just in case
    # secrets.toml is usually flat key-value pairs?
    # Actually streamlit secrets.toml is TOML.
    pass

if not url or not key:
    print("❌ URL or KEY missing in secrets.toml")
    print(f"Keys found: {list(secrets.keys())}")
    exit(1)

print(f"✅ Found Credentials.")
print(f"URL: {url}")

try:
    print("Attempting to connect to Supabase...")
    supabase: Client = create_client(url, key)
    
    # Try simple query
    # We use table('feeds') because we know it exists from the SQL setup
    response = supabase.table("feeds").select("count", count="exact").execute()
    
    print("✅ Connection Successful!")
    print(f"Response: {response}")
    
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    # Print more details if available
    import traceback
    traceback.print_exc()
    exit(1)
