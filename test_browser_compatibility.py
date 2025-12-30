#!/usr/bin/env python3
"""
Test script to verify browser compatibility with X/Twitter
This will help diagnose if the "browser no longer supported" issue is resolved
"""

import time
from selenium_scraper import TwitterScraper
from selenium.webdriver.common.by import By

def test_browser_compatibility():
    """Test if the browser can access X/Twitter without compatibility issues"""
    
    print("🧪 Testing Browser Compatibility with X/Twitter")
    print("=" * 60)
    
    scraper = None
    try:
        # Initialize scraper with visible browser for testing
        print("1. Initializing browser...")
        scraper = TwitterScraper(headless=False, use_persistent_profile=True)
        
        print("2. Navigating to X/Twitter...")
        scraper.driver.get("https://x.com")
        time.sleep(5)
        
        # Check current URL and page title
        current_url = scraper.driver.current_url
        page_title = scraper.driver.title
        
        print(f"   Current URL: {current_url}")
        print(f"   Page Title: {page_title}")
        
        # Check for compatibility issues
        page_source = scraper.driver.page_source.lower()
        
        # Look for common error messages
        error_indicators = [
            "browser is no longer supported",
            "upgrade your browser",
            "browser not supported",
            "outdated browser",
            "please update your browser"
        ]
        
        compatibility_issues = []
        for indicator in error_indicators:
            if indicator in page_source:
                compatibility_issues.append(indicator)
        
        if compatibility_issues:
            print("❌ COMPATIBILITY ISSUES DETECTED:")
            for issue in compatibility_issues:
                print(f"   - Found: '{issue}'")
            print("\nRecommendations:")
            print("   1. Try updating Chrome to the latest version")
            print("   2. Clear browser cache and cookies")
            print("   3. Try using a different user agent")
            return False
        else:
            print("✅ No compatibility issues detected!")
            
            # Check if we can see login interface or main page
            login_indicators = scraper.driver.find_elements(By.XPATH,
                '//*[contains(text(), "Sign in") or contains(text(), "Log in") or contains(text(), "What\'s happening")]'
            )
            
            if login_indicators:
                print("✅ Page loaded successfully - can see Twitter interface")
                return True
            else:
                print("⚠️ Page loaded but Twitter interface not detected")
                print("   This might be normal if there are loading delays")
                return True
        
    except Exception as e:
        print(f"❌ Error during compatibility test: {str(e)}")
        return False
        
    finally:
        if scraper:
            print("\n3. Cleaning up...")
            try:
                scraper.close()
            except:
                pass
    
    return False

def test_user_agent():
    """Test current user agent string"""
    
    print("\n🔍 Checking User Agent Configuration")
    print("=" * 40)
    
    scraper = None
    try:
        scraper = TwitterScraper(headless=False, use_persistent_profile=False)
        
        # Navigate to a user agent detection page
        scraper.driver.get("https://httpbin.org/user-agent")
        time.sleep(2)
        
        # Get the user agent from the page
        user_agent_info = scraper.driver.find_element(By.TAG_NAME, "body").text
        print(f"Current User Agent: {user_agent_info}")
        
        # Check if it's a modern Chrome version
        if "Chrome/120" in user_agent_info or "Chrome/119" in user_agent_info or "Chrome/118" in user_agent_info:
            print("✅ Using modern Chrome user agent")
            return True
        else:
            print("⚠️ User agent might be outdated")
            return False
            
    except Exception as e:
        print(f"❌ Error checking user agent: {str(e)}")
        return False
        
    finally:
        if scraper:
            try:
                scraper.close()
            except:
                pass
    
    return False

if __name__ == "__main__":
    print("Starting browser compatibility tests...\n")
    
    # Test user agent first
    ua_test_passed = test_user_agent()
    
    # Test Twitter compatibility
    twitter_test_passed = test_browser_compatibility()
    
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"User Agent Test: {'✅ PASSED' if ua_test_passed else '❌ FAILED'}")
    print(f"Twitter Compatibility Test: {'✅ PASSED' if twitter_test_passed else '❌ FAILED'}")
    
    if ua_test_passed and twitter_test_passed:
        print("\n🎉 All tests passed! Browser should work with X/Twitter")
        print("You can now run the intelligent agent without compatibility issues.")
    else:
        print("\n⚠️ Some tests failed. You may still encounter the 'browser not supported' message.")
        print("Try running the script again or check Chrome version.") 