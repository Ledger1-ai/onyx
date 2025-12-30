import time
from selenium_scraper import TwitterScraper
from config import logger

def manual_login():
    """
    Opens a non-headless browser session for the user to manually log in to Twitter.
    The session is saved to the persistent profile.
    """
    print("🚀 Starting Twitter Manual Login Session...")
    print("PLEASE NOTE: A browser window will open.")
    print("1. Log in to Twitter manually.")
    print("2. Navigate around to ensure cookies are set.")
    print("3. Close the browser window or press Enter here when done.")
    
    try:
        # Initialize Scraper in Headed Mode
        scraper = TwitterScraper(headless=False, use_persistent_profile=True)
        
        # Navigate to login
        scraper.driver.get("https://twitter.com/login")
        
        input("\n[PRESS ENTER TO CLOSE AND SAVE SESSION]\n")
        
        scraper.driver.quit()
        print("✅ Session saved to persistent profile.")
        
    except Exception as e:
        print(f"❌ Error during manual login: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    manual_login()
