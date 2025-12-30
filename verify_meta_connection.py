import os
import logging
from dotenv import load_dotenv
from meta_api_handler import MetaAPIHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def verify_meta_connection():
    print("----------------------------------------------------------------")
    print("              META (FACEBOOK/INSTAGRAM) CONNECTION TEST         ")
    print("----------------------------------------------------------------")

    # Load environment variables
    load_dotenv('config.env')

    # key check
    access_token = os.getenv("META_ACCESS_TOKEN")
    page_id = os.getenv("META_PAGE_ID")
    ig_user_id = os.getenv("META_IG_USER_ID")

    print(f"[*] Access Token Found: {'YES' if access_token else 'NO'}")
    print(f"[*] Page ID Found:      {'YES' if page_id else 'NO'} ({page_id if page_id else 'N/A'})")
    print(f"[*] IG User ID Found:   {'YES' if ig_user_id else 'NO'} ({ig_user_id if ig_user_id else 'N/A'})")
    
    if not access_token:
        logger.error("❌ CRITICAL: No META_ACCESS_TOKEN found in config.env")
        return

    # Initialize Handler
    handler = MetaAPIHandler()
    
    # 1. Validate Token (Ping /me)
    print("\n[1] Testing Token Validity (/me)...")
    if handler.validate_auth():
        print("[OK] SUCCESS: Access Token is valid.")
    else:
        print("[FAIL] FAILURE: Access Token is INVALID or Expired.")
        return

    # 2. Validate Page Access
    if page_id:
        print(f"\n[2] Testing Facebook Page Access (ID: {page_id})...")
        try:
            # Manually invoke a get requests to check page specifics
            import requests
            url = f"{handler.base_url}/{page_id}"
            params = {"access_token": access_token, "fields": "name,followers_count"}
            res = requests.get(url, params=params)
            
            if res.status_code == 200:
                data = res.json()
                print(f"[OK] SUCCESS: Connected to Page '{data.get('name')}'")
                print(f"   - Followers: {data.get('followers_count')}")
            else:
                print(f"[FAIL] FAILURE: Could not access Page. API Response: {res.text}")
        except Exception as e:
            print(f"[FAIL] ERROR: {e}")
    else:
        print("[WARN] SKIPPING: No META_PAGE_ID provided.")

    # 3. Validate Instagram Access
    if ig_user_id:
        print(f"\n[3] Testing Instagram Business Account Access (ID: {ig_user_id})...")
        try:
            import requests
            url = f"{handler.base_url}/{ig_user_id}"
            params = {"access_token": access_token, "fields": "username,followers_count"}
            res = requests.get(url, params=params)
            
            if res.status_code == 200:
                data = res.json()
                print(f"[OK] SUCCESS: Connected to Instagram Account '@{data.get('username')}'")
                print(f"   - Followers: {data.get('followers_count')}")
            else:
                print(f"[FAIL] FAILURE: Could not access Instagram Account. API Response: {res.text}")
        except Exception as e:
            print(f"[FAIL] ERROR: {e}")
    else:
        print("[WARN] SKIPPING: No META_IG_USER_ID provided.")

    print("\n----------------------------------------------------------------")
    print("Verification Complete.")

if __name__ == "__main__":
    verify_meta_connection()
