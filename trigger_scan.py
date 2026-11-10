import os
import requests
import sys
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
USERNAME = os.environ.get("PROBLEM_RADAR_USERNAME")
PASSWORD = os.environ.get("PROBLEM_RADAR_PASSWORD")

def execute_secure_scan():
    if not USERNAME or not PASSWORD:
        sys.exit("Set PROBLEM_RADAR_USERNAME and PROBLEM_RADAR_PASSWORD first.")

    print("📡 [Trigger Script] Connecting to FastAPI security center...")

    # 1. AUTOMATED REGISTER STEP: Ensure this user account profile exists in the database
    print("👤 Registering account profile if missing...")
    reg_payload = {"username": USERNAME, "password": PASSWORD}
    try:
        requests.post(f"{BASE_URL}/api/v1/auth/register", json=reg_payload)
    except Exception as e:
        print(f"⚠️ Registration step skipped or server unreachable: {e}")

    # 2. LOGIN STEP: Authenticate cleanly to fetch a guaranteed fresh access token string
    print("🔐 Authenticating credentials...")
    auth_payload = {"username": USERNAME, "password": PASSWORD}
    try:
        token_response = requests.post(f"{BASE_URL}/api/v1/auth/token", data=auth_payload)
        if token_response.status_code != 200:
            print(f"❌ Login Failed ({token_response.status_code}): {token_response.text}")
            print("💡 Pro-Tip: Make sure your main Uvicorn server is running on port 8000!")
            sys.exit(1)

        token_data = token_response.json()
        access_token = token_data["access_token"]
        print("✅ Fresh security access token acquired successfully.")
    except Exception as e:
        print(f"❌ Connection error during login: {e}")
        sys.exit(1)

    # 3. HEADER STEP: Build the network verification header mapping dictionary
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    scan_parameters = {
        "niche": "Logistics",
        "limit_per_source": 1
    }

    # 4. TRIGGER STEP: Fire the background scraping task fleet drop
    print(f"🚀 Deploying scraping fleet for niche: '{scan_parameters['niche']}'...")
    scan_response = requests.post(f"{BASE_URL}/api/v1/scan", json=scan_parameters, headers=headers)

    print("\n--- SERVER RESPONSE MAP ---")
    print(f"HTTP Status Code: {scan_response.status_code}")
    print(f"Response Body: {scan_response.text}")
    print("---------------------------\n")

    if scan_response.status_code == 200:
        print("🎉 SUCCESS! Your entire pipeline is fully unlocked.")
        print("👀 Look back at your main Uvicorn terminal window to watch your web crawlers execute!")
    else:
        print("❌ Authorization rejected. Let's inspect the server's debug logs.")

if __name__ == "__main__":
    execute_secure_scan()
