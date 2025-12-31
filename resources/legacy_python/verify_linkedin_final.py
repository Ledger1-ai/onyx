
import sys
from linkedin_api_handler import LinkedInAPIHandler
from config import logger
import logging

# Configure logger to print to console
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Ensure env vars are loaded
try:
    from dotenv import load_dotenv
    load_dotenv('config.env')
except ImportError:
    print("[WARN] python-dotenv not installed. Attempting manual load...")
    import os
    if os.path.exists('config.env'):
        with open('config.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def test_auth():
    print("------------------------------------------------")
    print("[TEST] Testing LinkedIn API Authentication...")
    
    try:
        handler = LinkedInAPIHandler()
        print(f"[OK] Handler Initialized")
    except Exception as e:
        print(f"[FAIL] Handler Init Failed: {e}")
        return

    if handler.validate_auth():
        print("[SUCCESS] API Connection Successful! (200 OK from /me)")
        print(f"Org URN: {handler.organization_urn}")
        print("------------------------------------------------")
        print("[READY] LinkedIn is ready for Safe Mode operations.")
    else:
        print("[FAIL] API Auth Validation Failed.")
        print("Check your Access Token and Organization URN in config.env")
        print("------------------------------------------------")

if __name__ == "__main__":
    test_auth()
