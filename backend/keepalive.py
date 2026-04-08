import requests
import time
import os

# Get URL from environment or fallback to production
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://vaakazhipeer.onrender.com") + "/health"
PING_INTERVAL = 600  # 10 minutes

def ping():
    try:
        r = requests.get(RENDER_URL, timeout=15)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ping OK: {r.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ping failed: {e}")

if __name__ == "__main__":
    print(f"Keep-alive started for {RENDER_URL}")
    print(f"Pinging every {PING_INTERVAL//60} mins...")
    while True:
        ping()
        time.sleep(PING_INTERVAL)
