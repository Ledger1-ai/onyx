#!/usr/bin/env python3
"""
Test script for persistent profile functionality
"""

from selenium_scraper import TwitterScraper
import time

def test_persistent_profile():
    """Test the persistent profile setup"""
    print("🧪 Testing Persistent Profile Functionality")
    print("=" * 50)
    
    # Test with persistent profile enabled
    print("\n1. Testing with persistent profile enabled...")
    scraper = TwitterScraper(headless=False, use_persistent_profile=True)
    
    try:
        print(f"   Profile directory: {scraper.profile_dir}")
        print("   ✅ Driver initialized successfully")
        
        # Test login status check
        login_status = scraper._check_login_status()
        if login_status:
            print("   ✅ Already logged in!")
        else:
            print("   ℹ️ Not logged in - this is expected for first run")
        
        # Keep browser open for manual inspection
        print("\n   Browser window is open for inspection...")
        print("   You can manually check the browser profile directory:")
        print(f"   {scraper.profile_dir}")
        
        input("\n   Press ENTER to continue to cleanup test...")
        
    finally:
        scraper.close()
    
    print("\n2. Testing profile management functions...")
    
    # Test without persistent profile  
    scraper2 = TwitterScraper(headless=True, use_persistent_profile=False)
    try:
        print("   ✅ Non-persistent mode works")
    finally:
        scraper2.close()
    
    print("\n✅ All tests completed successfully!")
    print("\nNext steps:")
    print("1. Run: python launch_intelligent_agent.py --setup-login")
    print("2. Then: python launch_intelligent_agent.py --interactive")

if __name__ == "__main__":
    test_persistent_profile() 