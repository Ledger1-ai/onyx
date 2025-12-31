#!/usr/bin/env python3
"""
Debug script to check LinkedIn and Twitter login status in database and filesystem.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager

def check_status():
    print("=" * 60)
    print("[DEBUG] ANUBIS LOGIN STATUS DIAGNOSTIC")
    print("=" * 60)
    
    # 1. Check Filesystem (Bot Status)
    print("\n[FILESYSTEM] Bot Status:")
    print("-" * 40)
    
    twitter_profile_dir = "browser_profiles/twitter_automation_profile"
    linkedin_auth_file = "browser_profiles/linkedin_auth.json"
    linkedin_profile_dir = "browser_profiles/linkedin_automation_profile"
    legacy_marker = os.path.join(linkedin_profile_dir, "auth_success.marker")
    
    twitter_bot = os.path.exists(twitter_profile_dir)
    linkedin_bot = os.path.exists(linkedin_auth_file) or (os.path.exists(linkedin_profile_dir) and os.path.exists(legacy_marker))
    
    print(f"  Twitter Profile Dir: {twitter_profile_dir}")
    print(f"    Exists: {'[OK] YES' if twitter_bot else '[X] NO'}")
    
    print(f"  LinkedIn Auth File: {linkedin_auth_file}")
    print(f"    Exists: {'[OK] YES' if os.path.exists(linkedin_auth_file) else '[X] NO'}")
    
    print(f"  LinkedIn Profile Dir: {linkedin_profile_dir}")
    print(f"    Exists: {'[OK] YES' if os.path.exists(linkedin_profile_dir) else '[X] NO'}")
    
    print(f"  LinkedIn Legacy Marker: {legacy_marker}")
    print(f"    Exists: {'[OK] YES' if os.path.exists(legacy_marker) else '[X] NO'}")
    
    print(f"\n  [BOT] Twitter Bot Status: {'[OK] CONNECTED' if twitter_bot else '[X] NOT CONNECTED'}")
    print(f"  [BOT] LinkedIn Bot Status: {'[OK] CONNECTED' if linkedin_bot else '[X] NOT CONNECTED'}")
    
    # 2. Check Database (API Status)
    print("\n[DATABASE] API Status:")
    print("-" * 40)
    
    try:
        db_manager = DatabaseManager()
        print("  Database connection: [OK] SUCCESS")
        
        # Use the same DEFAULT_USER_ID as the rest of the application
        from config import Config
        user_id = getattr(Config, "DEFAULT_USER_ID", "admin_user")
        
        # Check for user
        user = db_manager.get_user(user_id)
        if user:
            print(f"  User 'admin' found: [OK] YES")
            print(f"  User data keys: {list(user.keys())}")
            
            creds = user.get("credentials", {})
            print(f"\n  Credentials structure:")
            print(f"    Twitter: {creds.get('twitter', 'NOT FOUND')}")
            print(f"    LinkedIn: {creds.get('linkedin', 'NOT FOUND')}")
            print(f"    Facebook: {creds.get('facebook', 'NOT FOUND')}")
            print(f"    Instagram: {creds.get('instagram', 'NOT FOUND')}")
            
            twitter_api = creds.get("twitter", {}).get("is_active", False)
            linkedin_api = creds.get("linkedin", {}).get("is_active", False)
            
            print(f"\n  [API] Twitter API Status: {'[OK] ACTIVE' if twitter_api else '[X] INACTIVE'}")
            print(f"  [API] LinkedIn API Status: {'[OK] ACTIVE' if linkedin_api else '[X] INACTIVE'}")
        else:
            print(f"  User 'admin' found: [X] NO")
            print("  [!] No 'admin' user in database - API status will show as inactive")
            
        # Also check for other user IDs
        print("\n  Checking all users in database...")
        users_collection = db_manager.db.users
        all_users = list(users_collection.find())
        print(f"  Total users found: {len(all_users)}")
        for u in all_users:
            print(f"    - user_id: {u.get('user_id', u.get('_id'))}")
            
    except Exception as e:
        print(f"  Database connection: [X] FAILED")
        print(f"  Error: {e}")
    
    print("\n" + "=" * 60)
    print("[END] DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    check_status()
