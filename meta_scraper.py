import time
import random
import os
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False

from config import Config, logger

class MetaScraper:
    """Selenium-based scraper for Facebook and Instagram"""

    def __init__(self, headless=False, use_persistent_profile=True):
        self.config = Config()
        self.driver = None
        self.wait = None
        self.headless = headless
        self.use_persistent_profile = use_persistent_profile
        self.profile_dir = self._get_profile_directory()
        self.setup_driver()

    def _get_profile_directory(self):
        """Resolve persistent Chrome profile directory"""
        # We use a separate profile for Meta to avoid lock conflicts with Twitter bot
        path = Path("browser_profiles/meta_automation_profile")
        
        if not path.is_absolute():
            path = Path.cwd() / path
            
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def setup_driver(self):
        """Setup Chrome WebDriver with persistent profile support"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                chrome_options = Options()
                
                # Modern Chrome user agent
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                if self.use_persistent_profile:
                    chrome_options.add_argument(f"--user-data-dir={self.profile_dir}")
                    chrome_options.add_argument("--profile-directory=Default")
                
                # Graphics / VDI compatibility
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                # Anti-detection
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_argument("--disable-notifications")
                
                if self.headless:
                    chrome_options.add_argument("--headless=new")
                
                # Initialize
                if UC_AVAILABLE:
                    try:
                        self.driver = uc.Chrome(options=chrome_options)
                    except Exception as e:
                        print(f"⚠️ undetected-chromedriver failed ({e}), falling back to standard...")
                        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
                else:
                    self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
                
                self.driver.set_window_size(1920, 1080)
                self.wait = WebDriverWait(self.driver, 10)
                
                logger.info(f"✅ Meta Scraper initialized with profile: {self.profile_dir}")
                break

            except Exception as e:
                if "user data directory is already in use" in str(e):
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    else:
                        raise Exception("Meta profile directory is locked by another browser instance.")
                raise e

    def login_facebook_manual(self):
        """Guide user through manual Facebook login"""
        try:
            print("\n🔵 OPENING FACEBOOK LOGIN...")
            self.driver.get("https://www.facebook.com/login")
            input("\n⏳ Please log in to Facebook manually in the browser window, then press ENTER here...")
            print("✅ Facebook Login Marked as Complete.")
            return True
        except Exception as e:
            logger.error(f"Error during Facebook login: {e}")
            return False

    def login_instagram_manual(self):
        """Guide user through manual Instagram login"""
        try:
            print("\n🟣 OPENING INSTAGRAM LOGIN...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            input("\n⏳ Please log in to Instagram manually in the browser window, then press ENTER here...")
            print("✅ Instagram Login Marked as Complete.")
            return True
        except Exception as e:
            logger.error(f"Error during Instagram login: {e}")
            return False

    def check_facebook_login(self):
        """Verify if logged into Facebook"""
        try:
            self.driver.get("https://www.facebook.com/")
            time.sleep(3)
            if "login" in self.driver.current_url or "welcome" in self.driver.title.lower():
                return False
            # Check for specific elements like the nav bar or 'Home'
            try:
                self.driver.find_element(By.CSS_SELECTOR, '[role="navigation"]')
                return True
            except:
                return False
        except:
            return False

    def check_instagram_login(self):
        """Verify if logged into Instagram"""
        try:
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)
            # Look for nav bar or profile icon
            try:
                self.driver.find_element(By.CSS_SELECTOR, 'svg[aria-label="Home"]')
                return True
            except:
                return False
        except:
            return False

    def _take_screenshot(self, name):
        """Take a screenshot for debugging/verification"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshots/{name}_{timestamp}.png"
            os.makedirs("screenshots", exist_ok=True)
            self.driver.save_screenshot(filename)
            logger.info(f"📸 Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    def get_facebook_stories(self):
        """Fetch Facebook Stories (Navigation & Screenshot)"""
        if not self.check_facebook_login():
            logger.warning("Not logged into Facebook. Cannot fetch stories.")
            return "Not logged in"
        
        logger.info("Navigate to Facebook Stories...")
        self.driver.get("https://www.facebook.com/stories")
        time.sleep(5) # Wait for load
        
        screenshot = self._take_screenshot("fb_stories")
        return f"Checked Facebook Stories. Screenshot: {screenshot}"

    def get_instagram_stories(self):
        """Fetch Instagram Stories (Navigation & Screenshot)"""
        if not self.check_instagram_login():
             logger.warning("Not logged into Instagram. Cannot fetch stories.")
             return "Not logged in"
        
        logger.info("Navigate to Instagram Stories...")
        self.driver.get("https://www.instagram.com/stories")
        time.sleep(5)
        
        screenshot = self._take_screenshot("ig_stories")
        return f"Checked Instagram Stories. Screenshot: {screenshot}"

    def get_facebook_reels(self):
        """Fetch Facebook Reels"""
        if not self.check_facebook_login():
            return "Not logged in"
        
        self.driver.get("https://www.facebook.com/reel")
        time.sleep(5)
        screenshot = self._take_screenshot("fb_reels")
        return f"Checked Facebook Reels. Screenshot: {screenshot}"

    def get_cookies(self):
        """Export current session cookies"""
        if self.driver:
            return self.driver.get_cookies()
        return []

    def set_cookies(self, cookies):
        """Inject cookies into the session"""
        if not self.driver or not cookies:
            return
        
        try:
            # Must visit domain first to set cookies
            # We assume FB/IG cookies. Visit FB first.
            self.driver.get("https://www.facebook.com/")
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    # Domain mismatch errors are common if mixing FB/IG cookies
                    pass
            logger.info(f"🍪 Injected {len(cookies)} cookies")
            self.driver.refresh()
        except Exception as e:
            logger.error(f"Failed to set cookies: {e}")

    def close(self):
        if self.driver:
            self.driver.quit()
