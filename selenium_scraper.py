import time
import random
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Undetected ChromeDriver (helps bypass bot detection)
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except Exception:
    UC_AVAILABLE = False
from typing import List, Dict, Optional, Any
from config import Config, logger
import json
import uuid
import re
from datetime import datetime
try:
    import requests  # optional for posting to /api/analytics/ingest
except Exception:
    requests = None

class TwitterScraper:
    """Selenium-based Twitter scraper for web automation"""
    
    def __init__(self, headless=False, use_persistent_profile=True):
        """
        Initialize the Twitter scraper with Selenium WebDriver
        
        Args:
            headless (bool): Run browser in headless mode
            use_persistent_profile (bool): Use persistent Chrome profile to stay logged in
        """
        self.config = Config()
        self.driver = None
        self.wait = None
        self.headless = headless
        self.use_persistent_profile = use_persistent_profile
        self.profile_dir = self._get_profile_directory()
        self.logged_in = False
        
        # Rate Limiting
        self.daily_view_count = 0
        self.daily_view_limit = 500  # Default for unverified
        self.last_view_reset = datetime.now()
        self.account_type = "unverified"
        
        self.setup_driver()
    
    def _get_profile_directory(self):
        """Resolve persistent Chrome profile directory from Config.PROFILE_DIRECTORY and ensure it exists"""
        try:
            configured = getattr(self.config, "PROFILE_DIRECTORY", None)
        except Exception:
            configured = None

        # Default to workspace-relative path if not configured
        path = Path(configured or "browser_profiles/twitter_automation_profile")

        # Resolve relative paths against current working directory
        if not path.is_absolute():
            path = Path.cwd() / path

        # Ensure directory exists (including parents)
        path.mkdir(parents=True, exist_ok=True)

        print(f"🔒 Using Chrome user data dir: {path}")
        return str(path)

    def _check_and_reset_daily_limit(self):
        """Reset counter if it's a new day"""
        now = datetime.now()
        if now.date() > self.last_view_reset.date():
            self.daily_view_count = 0
            self.last_view_reset = now
            logger.info("🔄 Daily view count reset")

    def _check_view_limit(self) -> bool:
        """Check if daily view limit reached"""
        self._check_and_reset_daily_limit()
        if self.daily_view_count >= self.daily_view_limit:
            logger.warning(f"⚠️ Daily view limit reached ({self.daily_view_count}/{self.daily_view_limit})")
            return False
        return True

    def _increment_view_count(self, amount: int = 1):
        """Increment view count"""
        self.daily_view_count += amount
        if self.daily_view_count % 10 == 0:
            logger.info(f"👀 View count: {self.daily_view_count}/{self.daily_view_limit}")

    
    def _save_bot_status_to_db(self, is_active: bool):
        """Save bot login status to database for multi-tenant visibility"""
        try:
            from database_manager import DatabaseManager
            from config import Config
            from datetime import datetime
            
            db = DatabaseManager()
            user_id = getattr(Config, "DEFAULT_USER_ID", "admin_user")
            db.save_credential(user_id, "twitter_bot", {
                "is_active": is_active,
                "platform": "twitter",
                "type": "selenium_bot",
                "updated_at": datetime.now().isoformat()
            })
            if is_active:
                print(f"💾 Bot login status saved to database for user: {user_id}")
        except Exception as e:
            # Non-fatal - don't break login flow if DB save fails
            print(f"⚠️ Could not save bot status to DB: {e}")
    
    
    def _kill_chrome_processes(self):
        """Kill stray Chrome processes to release locks"""
        try:
            if os.name == 'nt':
                # Use /T to kill child processes
                os.system("taskkill /F /IM chrome.exe /T >nul 2>&1")
                os.system("taskkill /F /IM chromedriver.exe /T >nul 2>&1")
            else:
                os.system("pkill -9 chrome")
                os.system("pkill -9 chromedriver")
        except Exception:
            pass
            
    def setup_driver(self):
        """Setup Chrome WebDriver with persistent profile support and modern browser configuration"""
        self._kill_chrome_processes()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                chrome_options = Options()
                print(f"DEBUG: Attempting to start Chrome (Attempt {attempt+1}/{max_retries})")
                
                # Modern Chrome user agent (more recent version)
                modern_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                chrome_options.add_argument(f"--user-agent={modern_user_agent}")
                
                # Persistent profile configuration
                if self.use_persistent_profile:
                    chrome_options.add_argument(f"--user-data-dir={self.profile_dir}")
                    chrome_options.add_argument("--profile-directory=Default")
                    print(f"🔄 Using persistent profile: {self.profile_dir}")
                
                # Modern browser compatibility options
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                # Force GPU off to avoid D3D/ANGLE issues on headless/Server environments
                chrome_options.add_argument("--disable-gpu")
                # Select ANGLE backend based on environment (RDP/VM => SwiftShader; otherwise D3D11)
                is_rdp_or_vm = (os.environ.get("SESSIONNAME", "").lower().startswith("rdp") or os.environ.get("IS_VM", "").lower() == "true")
                # Prefer SwiftShader when headless or in RDP/VM to avoid D3D11 device queries
                if is_rdp_or_vm or self.headless:
                    # Prefer software rasterizer to avoid missing GL/D3D interop on VMs/RDP/headless
                    chrome_options.add_argument("--use-angle=swiftshader")
                    chrome_options.add_argument("--use-gl=swiftshader")
                    chrome_options.add_argument("--enable-unsafe-swiftshader")
                else:
                    chrome_options.add_argument("--use-angle=d3d11")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                
                # Enable modern web standards
                
                # JavaScript and modern web features
                chrome_options.add_argument("--enable-javascript")
                
                # Security and compatibility
                chrome_options.add_argument("--disable-web-security")
                chrome_options.add_argument("--allow-running-insecure-content")
                # Reduce background services and push messaging noise
                chrome_options.add_argument("--disable-background-networking")
                chrome_options.add_argument("--disable-sync")
                chrome_options.add_argument("--metrics-recording-only")
                # Suppress FedCM (Identity Credential) widget errors seen on some login flows
                chrome_options.add_argument("--disable-features=FedCm")
                # Disable WebGPU to avoid ANGLE/D3D11 queries on constrained VMs
                chrome_options.add_argument("--disable-features=WebGPU")
                # Additional guard to disable WebGPU pipeline explicitly
                chrome_options.add_argument("--disable-webgpu")
                
                # Anti-detection measures (updated)
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                # Removed experimental options that caused InvalidArgumentException on Chrome 142+
                # (excludeSwitches/useAutomationExtension). We rely on JS overrides and blink feature disable.
                
                # Modern viewport and display settings
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--force-device-scale-factor=1")
                
                # Enable all modern web platform features
                chrome_options.add_argument("--enable-features=NetworkService,NetworkServiceLogging")
                chrome_options.add_argument("--disable-features=TranslateUI")
                chrome_options.add_argument("--disable-iframes-during-prerender")
                
                # Experimental features for better compatibility
                chrome_options.add_experimental_option("prefs", {
                    "profile.default_content_setting_values": {
                        "notifications": 2,  # Block notifications
                        "geolocation": 2,    # Block location requests
                    },
                    "profile.default_content_settings.popups": 0,
                    "profile.managed_default_content_settings.images": 1,  # Allow images for better compatibility
                    "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
                })
                
                # Language and locale settings for better compatibility
                chrome_options.add_argument("--lang=en-US")
                chrome_options.add_argument("--accept-lang=en-US,en")
                
                # Headless configuration (if needed)
                if self.headless:
                    chrome_options.add_argument("--headless=new")  # Use new headless mode
                    chrome_options.add_argument("--no-first-run")
                    print("🔇 Running in headless mode with modern configuration")
                else:
                    print("🖥️ Running with visible browser (modern configuration)")
                
                # Initialize driver (prefer undetected-chromedriver if available)
                if UC_AVAILABLE:
                    try:
                        # uc.Chrome can take standard selenium ChromeOptions
                        self.driver = uc.Chrome(options=chrome_options)
                    except Exception as uc_err:
                        print(f"⚠️ undetected-chromedriver failed ({uc_err}), falling back to standard ChromeDriver")
                        service = Service(ChromeDriverManager().install())
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Modern anti-detection scripts
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [{filename: 'internal-pdf-viewer', description: 'Portable Document Format'}]})")
                self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
                
                # Set modern viewport
                self.driver.set_window_size(1920, 1080)
                
                # Setup wait
                self.wait = WebDriverWait(self.driver, 10)
                
                print("✅ Chrome WebDriver initialized with modern browser configuration")
                
                # Check if already logged in and set the flag
                if self.use_persistent_profile:
                    self.logged_in = self._check_login_status()
                else:
                    self.logged_in = False
                
                # If we get here, setup was successful
                break
                    
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error setting up WebDriver (Attempt {attempt+1}): {error_msg}")
                
                # Cleanup broken driver attempt
                try:
                    if self.driver:
                        self.driver.quit()
                except:
                    pass
                self.driver = None
                
                if attempt < max_retries - 1:
                    print("♻️ Retrying driver setup...")
                    self._kill_chrome_processes()
                    time.sleep(3)
                    continue
                else:
                    raise
    
    def _check_login_status(self):
        """Check if user is already logged into X/Twitter using multiple robust indicators."""
        try:
            print("🔍 Checking login status...")
            # Go to home; persistent sessions typically land here if logged in
            self.driver.get("https://x.com/home")
            time.sleep(3)

            current_url = self.driver.current_url.lower()

            # Quick negative checks: presence of obvious login prompts
            try:
                login_cta = self.driver.find_elements(By.XPATH, "//span[normalize-space()='Log in'] | //a[contains(@href,'/login')]")
                if login_cta:
                    print("🔐 Login prompts detected.")
            except Exception:
                pass

            # Positive indicators: any of the following suggest an authenticated UI
            positive_checks = [
                # Side nav account switcher (logged-in left nav)
                (By.CSS_SELECTOR, "[data-testid='SideNav_AccountSwitcher_Button']"),
                # Profile tab in bottom/side app bar
                (By.CSS_SELECTOR, "[data-testid='AppTabBar_Profile_Link']"),
                # Compose button in sidenav
                (By.CSS_SELECTOR, "[data-testid='SideNav_NewTweet_Button']"),
                # Compose textarea in home timeline
                (By.CSS_SELECTOR, "[data-testid='tweetTextarea_0']"),
                # Notifications tab (visible when logged in)
                (By.CSS_SELECTOR, "a[href='/notifications']"),
            ]

            for by, sel in positive_checks:
                try:
                    el = self.driver.find_element(by, sel)
                    if el and el.is_displayed():
                        print("✅ Already logged in! Session restored from profile.")
                        self._save_bot_status_to_db(True)
                        
                        # Auto-detect account type
                        is_premium = self.check_premium_status()
                        if is_premium:
                            self.account_type = "verified"
                            self.daily_view_limit = 5000
                            print("🌟 Premium/Verified account detected. limits increased.")
                        else:
                            self.account_type = "unverified"
                            self.daily_view_limit = 500
                            print("Info: Unverified account detected. Daily view limit set to 500.")
                            
                        return True
                except NoSuchElementException:
                    continue
                except Exception:
                    continue

            # If home didn't show indicators, try profile page for another signal
            try:
                self.driver.get("https://x.com/settings/profile")
                time.sleep(2)
                settings_checks = [
                    (By.CSS_SELECTOR, "[data-testid='SettingsDetail']"),
                    (By.XPATH, "//span[contains(text(),'Edit profile')]")
                ]
                for by, sel in settings_checks:
                    try:
                        el = self.driver.find_element(by, sel)
                        if el and el.is_displayed():
                            print("✅ Logged in (profile settings accessible).")
                            self._save_bot_status_to_db(True)
                            return True
                    except Exception:
                        continue
            except Exception:
                pass

            print("🔐 Not logged in. You'll need to login manually first.")
            self._save_bot_status_to_db(False)
            return False

        except Exception as e:
            error_str = str(e)
            if "Max retries exceeded" in error_str or "10061" in error_str or "Connection refused" in error_str:
                print(f"🔥 Critical driver connection error: {error_str}")
                raise e # Re-raise critical errors to trigger driver restart
                
            print(f"⚠️ Could not determine login status: {error_str}")
            return False
    
    def manual_login_helper(self):
        """Helper method to guide user through manual login"""
        print("\n" + "="*60)
        print("🔐 MANUAL LOGIN REQUIRED")
        print("="*60)
        print("1. The browser will open to Twitter login page")
        print("2. Please login manually with your credentials")
        print("3. Complete any 2FA if required")
        print("4. Navigate to your home timeline")
        print("5. Press ENTER in this terminal when done")
        print("="*60)
        
        try:
            # Navigate to login page
            self.driver.get("https://x.com/i/flow/login")
            
            # Wait for user to complete login
            input("\n⏳ Press ENTER after you've successfully logged in...")
            
            # Verify login worked and set the flag
            login_success = self._check_login_status()
            self.logged_in = login_success
            
            if login_success:
                print("✅ Login successful! Profile saved for future sessions.")
                return True
            else:
                print("❌ Login verification failed. Please try again.")
                return False
                
        except Exception as e:
            print(f"❌ Error during manual login: {str(e)}")
            return False
    
    def ensure_logged_in(self):
        """Ensure user is logged in. Attempt automatic login if credentials are available.

        This method will:
        - Check current login status
        - If not logged in and creds exist in config, attempt automated login flow
        - Otherwise print a non-blocking instruction and return False
        """
        # First check current login status
        self.logged_in = self._check_login_status()

        if not self.logged_in:
            # Try automatic login using config credentials
            uname = getattr(self.config, "TWITTER_USERNAME", None)
            email = getattr(self.config, "TWITTER_EMAIL", None)
            pwd = getattr(self.config, "TWITTER_PASSWORD", None)
            # Build a stable user identifier (prefer email; strip leading '@' from username if present)
            user_identifier = email or uname
            if isinstance(user_identifier, str) and user_identifier.startswith("@"):
                user_identifier = user_identifier[1:]
            # Sanitize username (strip leading @ if present)
            user_identifier = email or uname
            if isinstance(user_identifier, str) and user_identifier.startswith("@"):
                user_identifier = user_identifier[1:]

            if (uname or email) and pwd:
                print("🔐 Not logged in – attempting automated login with configured credentials…")
                try:
                    auto_ok = self._auto_login()
                    self.logged_in = auto_ok and self._check_login_status()
                    if self.logged_in:
                        print("✅ Automated login successful. Session established.")
                        return True
                    else:
                        print("⚠️ Automated login did not verify. You may need to complete any prompts manually.")
                        return False
                except Exception as e:
                    print(f"❌ Automated login failed: {e}. You may need to login manually in the opened browser.")
                    return False
            else:
                # Non-blocking message instead of interactive input
                print("🔐 Login required for this session…")
                print("   No credentials found in config. Please log in to X/Twitter manually using 'Use phone/email/username'.")
                print("   After login, the agent will detect your session automatically. No need to press ENTER.")
                return False

        return True

    def login(self) -> bool:
        """Compatibility wrapper to match anubispro-TSPCC interface."""
        try:
            return self.ensure_logged_in()
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def clear_profile(self):
        """Clear the persistent profile (logout)"""
        try:
            import shutil
            if os.path.exists(self.profile_dir):
                shutil.rmtree(self.profile_dir)
                print("🗑️ Browser profile cleared. You'll need to login again next time.")
            else:
                print("ℹ️ No profile to clear.")
        except Exception as e:
            print(f"❌ Error clearing profile: {str(e)}")
    
    def _random_delay(self, min_seconds: float = 1, max_seconds: float = 3):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def _type_like_human(self, element, text: str):
        """Type text with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def post_tweet(self, text: str, media_paths: Optional[List[str]] = None) -> bool:
        """Post a tweet"""
        if not self.logged_in:
            logger.error("Not logged in")
            return False
        
        try:
            logger.info(f"Posting tweet: {text[:50]}...")
            
            # Navigate to home if not already there
            if "home" not in self.driver.current_url:
                self.driver.get("https://x.com/home")
                self._random_delay(2, 3)
            
            # Find and click tweet compose box
            compose_box = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
            )
            compose_box.click()
            self._random_delay(1, 2)
            
            # Type the tweet text
            self._type_like_human(compose_box, text)
            self._random_delay(1, 2)
            
            # Handle media upload if provided
            if media_paths:
                for media_path in media_paths:
                    if os.path.exists(media_path):
                        try:
                            media_input = self.driver.find_element(By.CSS_SELECTOR, 'input[data-testid="fileInput"]')
                            media_input.send_keys(os.path.abspath(media_path))
                            self._random_delay(2, 4)  # Wait for upload
                        except Exception as e:
                            logger.warning(f"Failed to upload media {media_path}: {e}")
            
            # Click Tweet button
            tweet_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]'))
            )
            tweet_button.click()
            
            # Wait for tweet to be posted
            self._random_delay(3, 5)
            
            logger.info("Tweet posted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return False

    def _auto_login(self) -> bool:
        """Attempt to log in to X/Twitter using credentials from config."""
        try:
            uname = getattr(self.config, "TWITTER_USERNAME", None)
            email = getattr(self.config, "TWITTER_EMAIL", None)
            pwd = getattr(self.config, "TWITTER_PASSWORD", None)

            if not pwd or not (uname or email):
                print("ℹ️ Missing credentials in config (TWITTER_USERNAME/TWITTER_EMAIL and TWITTER_PASSWORD). Skipping auto-login.")
                return False

            # Navigate to login flow
            self.driver.get("https://x.com/i/flow/login")
            time.sleep(2)
            # Some A/B flows require clicking “Use phone, email or username” first
            try:
                use_phone_link = None
                candidates = [
                    '//span[contains(text(),"Use phone") or contains(text(),"email") or contains(text(),"username")]',
                    '//div[@role="button"]//span[contains(text(),"Use phone") or contains(text(),"email") or contains(text(),"username")]',
                ]
                for xp in candidates:
                    els = self.driver.find_elements(By.XPATH, xp)
                    if els:
                        use_phone_link = els[0]
                        break
                if use_phone_link and use_phone_link.is_displayed():
                    self.driver.execute_script("arguments[0].click();", use_phone_link)
                    time.sleep(1)
            except Exception:
                pass

            # Step 1: Enter username or email
            try:
                input_selectors = [
                    'input[name="text"]',
                    'input[autocomplete="username"]',
                    'input[type="text"]'
                ]
                user_input = None
                for sel in input_selectors:
                    try:
                        user_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                        if user_input and user_input.is_displayed():
                            break
                    except Exception:
                        continue

                if not user_input:
                    print("❌ Could not find username/email input on login page.")
                    return False

                user_identifier = email or uname
                if isinstance(user_identifier, str) and user_identifier.startswith("@"):
                    user_identifier = user_identifier[1:]
                value_to_type = user_identifier
                user_input.clear()
                self._type_like_human(user_input, value_to_type)
                time.sleep(0.5)

                # Click Next
                next_candidates = [
                    '[data-testid="LoginForm_Login_Button"]',
                    '[data-testid="LoginForm_Next_Button"]',
                    'div[role="button"][data-testid*="Next"]',
                    'div[role="button"][data-testid*="Login"]',
                    'button[type="submit"]'
                ]
                next_button = None
                for sel in next_candidates:
                    try:
                        btns = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        next_button = next((b for b in btns if b.is_displayed() and b.is_enabled()), None)
                        if next_button:
                            break
                    except Exception:
                        continue

                if next_button:
                    next_button.click()
                else:
                    # Try pressing Enter
                    from selenium.webdriver.common.keys import Keys
                    user_input.send_keys(Keys.RETURN)
                time.sleep(2)
            except Exception as e:
                print(f"❌ Error entering username/email: {e}")
                return False

            # Step 2: If asked for username (after email), enter it
            try:
                username_prompt = None
                # Some flows ask for the username after email
                username_prompt = self.driver.find_elements(By.CSS_SELECTOR, 'input[name="text"]')
                if username_prompt and username_prompt[0].is_displayed():
                    username_prompt[0].clear()
                    self._type_like_human(username_prompt[0], uname or email)
                    time.sleep(0.5)
                    # Click Next again
                    next_buttons = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="LoginForm_Next_Button"]')
                    if next_buttons:
                        next_buttons[0].click()
                        time.sleep(2)
            except Exception:
                pass

            # Step 3: Enter password
            try:
                pwd_input_selectors = [
                    'input[name="password"]',
                    'input[type="password"]'
                ]
                pwd_input = None
                for sel in pwd_input_selectors:
                    try:
                        pwd_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                        if pwd_input and pwd_input.is_displayed():
                            break
                    except Exception:
                        continue

                if not pwd_input:
                    print("⚠️ Password input not found in flow login, trying classic login page…")
                    # Try classic login page which sometimes exposes direct username/password fields
                    self.driver.get("https://x.com/login")
                    time.sleep(2)

                    # Username/email field candidates on classic page
                    classic_user_selectors = [
                        'input[autocomplete="username"]',
                        'input[name="text"]',
                        'input[name="session[username_or_email]"]',
                        'input[type="text"]'
                    ]
                    user_input = None
                    for sel in classic_user_selectors:
                        try:
                            user_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                            if user_input and user_input.is_displayed():
                                break
                        except Exception:
                            continue

                    if user_input:
                        user_input.clear()
                        self._type_like_human(user_input, uname or email)
                        time.sleep(0.5)
                    else:
                        print("❌ Could not find username/email input on classic login page.")
                        return False

                    # Password field candidates on classic page
                    classic_pwd_selectors = [
                        'input[autocomplete="current-password"]',
                        'input[name="password"]',
                        'input[name="session[password]"]',
                        'input[type="password"]'
                    ]
                    pwd_input = None
                    for sel in classic_pwd_selectors:
                        try:
                            pwd_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                            if pwd_input and pwd_input.is_displayed():
                                break
                        except Exception:
                            continue

                    if not pwd_input:
                        print("❌ Could not find password input on classic login page.")
                        return False

                pwd_input.clear()
                self._type_like_human(pwd_input, pwd)
                time.sleep(0.5)

                # Click Log in / Submit
                login_candidates = [
                    '[data-testid="LoginForm_Login_Button"]',
                    'div[role="button"][data-testid*="Login"]',
                    'button[type="submit"]'
                ]
                login_button = None
                for sel in login_candidates:
                    try:
                        btns = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        login_button = next((b for b in btns if b.is_displayed() and b.is_enabled()), None)
                        if login_button:
                            break
                    except Exception:
                        continue

                if login_button:
                    login_button.click()
                else:
                    # Press Enter as fallback
                    from selenium.webdriver.common.keys import Keys
                    pwd_input.send_keys(Keys.RETURN)
                time.sleep(3)
            except Exception as e:
                print(f"❌ Error entering password or submitting form: {e}")
                return False

            # Optional: handle 2FA prompt if email is required
            # We won't automate 2FA; user must complete it manually if prompted.

            # Final check
            ok = self._check_login_status()
            return bool(ok)

        except Exception as e:
            print(f"❌ Auto-login unexpected error: {e}")
            return False
    
    def reply_to_tweet(self, tweet_url: str, reply_text: str) -> bool:
        """Reply to a specific tweet"""
        if not self.logged_in:
            logger.error("Not logged in")
            return False
        
        try:
            logger.info(f"Replying to tweet: {tweet_url}")
            
            # Navigate to the tweet
            self.driver.get(tweet_url)
            self._random_delay(2, 4)
            
            # Find and click reply button
            reply_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="reply"]'))
            )
            reply_button.click()
            self._random_delay(1, 2)
            
            # Find reply text area and type reply
            reply_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
            )
            self._type_like_human(reply_box, reply_text)
            self._random_delay(1, 2)
            
            # Click Reply button
            reply_submit = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]'))
            )
            reply_submit.click()
            
            self._random_delay(2, 3)
            logger.info("Reply posted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reply to tweet: {e}")
            return False
    
    def retweet(self, tweet_url: str) -> bool:
        """Retweet a specific tweet"""
        if not self.logged_in:
            logger.error("Not logged in")
            return False
        
        try:
            logger.info(f"Retweeting: {tweet_url}")
            
            # Navigate to the tweet
            self.driver.get(tweet_url)
            self._random_delay(2, 4)
            
            # Find and click retweet button
            retweet_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="retweet"]'))
            )
            retweet_button.click()
            self._random_delay(1, 2)
            
            # Click confirm retweet
            confirm_retweet = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="retweetConfirm"]'))
            )
            confirm_retweet.click()
            
            self._random_delay(2, 3)
            logger.info("Tweet retweeted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to retweet: {e}")
            return False
    
    def like_tweet(self, tweet_url: str) -> bool:
        """Like a specific tweet"""
        if not self.logged_in:
            logger.error("Not logged in")
            return False
        
        try:
            logger.info(f"Liking tweet: {tweet_url}")
            
            # Navigate to the tweet
            self.driver.get(tweet_url)
            self._random_delay(2, 4)
            
            # Find and click like button
            like_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="like"]'))
            )
            like_button.click()
            
            self._random_delay(1, 2)
            logger.info("Tweet liked successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to like tweet: {e}")
            return False
    
    def search_tweets(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for tweets"""
        if not self.logged_in:
            logger.error("Not logged in")
            return []
        
        try:
            if not self._check_view_limit():
                return []
            self._increment_view_count()
            logger.info(f"Searching for: {query}")
            
            # Navigate to search
            search_url = f"https://x.com/search?q={query.replace(' ', '%20')}&src=typed_query&f=live"
            self.driver.get(search_url)
            self._random_delay(3, 5)
            
            tweets = []
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
            
            for i, tweet_element in enumerate(tweet_elements[:max_results]):
                try:
                    # Extract tweet data
                    tweet_text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                    tweet_text = tweet_text_element.text
                    
                    # Try to get the tweet link
                    time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
                    tweet_link = time_element.find_element(By.XPATH, '..').get_attribute('href')
                    
                    # Extract username
                    username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Names"] a')
                    username = username_element.get_attribute('href').split('/')[-1]
                    
                    tweets.append({
                        'text': tweet_text,
                        'url': tweet_link,
                        'username': username,
                        'timestamp': time.time()
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to extract tweet {i}: {e}")
                    continue
            
            logger.info(f"Found {len(tweets)} tweets for query: {query}")
            return tweets
            
        except Exception as e:
            logger.error(f"Failed to search tweets: {e}")
            return []
    
    def get_trending_topics(self) -> List[Dict]:
        """Get trending topics"""
        if not self.logged_in:
            logger.error("Not logged in")
            return []
        
        try:
            if not self._check_view_limit():
                return []
            self._increment_view_count()
            logger.info("Getting trending topics")
            
            # Navigate to explore/trending
            self.driver.get("https://x.com/explore/tabs/trending")
            self._random_delay(3, 5)
            
            trends = []
            trend_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="trend"]')
            
            for trend_element in trend_elements[:10]:
                try:
                    trend_text = trend_element.find_element(By.CSS_SELECTOR, 'span').text
                    trend_link = trend_element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    
                    trends.append({
                        'name': trend_text,
                        'url': trend_link
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to extract trend: {e}")
                    continue
            
            logger.info(f"Found {len(trends)} trending topics")
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get trending topics: {e}")
            return []
    
    def follow_user(self, username: str) -> bool:
        """Follow a user"""
        if not self.logged_in:
            logger.error("Not logged in")
            return False
        
        try:
            logger.info(f"Following @{username}")
            
            # Navigate to user profile
            self.driver.get(f"https://x.com/{username}")
            self._random_delay(2, 4)
            
            # Find and click follow button
            follow_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid*="follow"]'))
            )
            
            if "Unfollow" not in follow_button.text:
                follow_button.click()
                self._random_delay(1, 2)
                logger.info(f"Followed @{username}")
                return True
            else:
                logger.info(f"Already following @{username}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to follow @{username}: {e}")
            return False
    
    def get_user_tweets(self, username: str, count: int = 10) -> List[Dict]:
        """Get recent tweets from a specific user"""
        if not self.logged_in:
            logger.error("Not logged in")
            return []
            
        if not self._check_view_limit():
            return []
        
        try:
            self._increment_view_count()  # Initial page load
            logger.info(f"Getting tweets from @{username}")
            
            # Navigate to user profile
            self.driver.get(f"https://x.com/{username}")
            self._random_delay(3, 5)
            
            tweets = []
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
            
            for i, tweet_element in enumerate(tweet_elements[:count]):
                try:
                    tweet_text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                    tweet_text = tweet_text_element.text
                    
                    time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
                    tweet_link = time_element.find_element(By.XPATH, '..').get_attribute('href')
                    
                    tweets.append({
                        'text': tweet_text,
                        'url': tweet_link,
                        'username': username,
                        'timestamp': time.time()
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to extract tweet {i} from @{username}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(tweets)} tweets from @{username}")
            return tweets
            
        except Exception as e:
            logger.error(f"Failed to get tweets from @{username}: {e}")
            return []

    def get_mentions(self, count: int = 20) -> List[Dict]:
        """Get recent mentions from notifications tab"""
        if not self.logged_in:
            logger.error("Not logged in")
            return []

        if not self._check_view_limit():
            return []
        
        try:
            self._increment_view_count()
            logger.info("Checking mentions...")
            
            # Navigate to mentions tab specifically
            self.driver.get("https://x.com/notifications/mentions")
            self._random_delay(3, 5)
            
            mentions = []
            
            # Wait for content
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]')))
            except TimeoutException:
                logger.warning("Timeout waiting for mentions to load")
                return []
                
            # Find tweets in notifications
            # Mentions usually appear as standard tweet cells in the mentions tab
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
            
            for i, tweet_element in enumerate(tweet_elements[:count]):
                try:
                    # Extract text
                    try:
                        text_el = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                        text = text_el.text
                    except NoSuchElementException:
                        text = "[Media/No Text]"
                    
                    # Extract author
                    try:
                        user_el = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Names"] a')
                        author_handle = user_el.get_attribute('href').split('/')[-1]
                    except Exception:
                        author_handle = "unknown"
                        
                    # Extract URL
                    try:
                        time_el = tweet_element.find_element(By.CSS_SELECTOR, 'time')
                        url = time_el.find_element(By.XPATH, '..').get_attribute('href')
                    except Exception:
                        url = None

                    mentions.append({
                        "id": url.split('/')[-1] if url else f"mention_{i}",
                        "text": text,
                        "author_username": author_handle,
                        "created_at": datetime.now().isoformat(), # Approximate
                        "url": url
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to parse mention {i}: {e}")
                    continue
            
            logger.info(f"Found {len(mentions)} recent mentions")
            return mentions
            
        except Exception as e:
            logger.error(f"Failed to get mentions: {e}")
            return []
    
    # ===========================
    # Account Analytics Scraping
    # ===========================
    def _parse_compact_number(self, text: str) -> int:
        """Parse compact numbers like '6.5K', '1.1K', '4.7K' into integers; fallback to int if plain."""
        try:
            if not text:
                return 0
            s = text.strip().upper().replace(',', '')
            m = re.match(r'^([0-9]+(?:\.[0-9]+)?)\s*([KMB])?$', s)
            if m:
                val = float(m.group(1))
                suf = m.group(2) or ''
                mult = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000}.get(suf, 1)
                return int(val * mult)
            # Remove non-digits
            digits = re.sub(r'[^0-9]', '', s)
            return int(digits) if digits else 0
        except Exception:
            return 0

    def _parse_percent(self, text: str) -> float:
        """Parse '7.4%' -> 0.074; '0.5' -> 0.5 if already fractional."""
        try:
            if not text:
                return 0.0
            s = text.strip().replace('%', '')
            val = float(s)
            # Assume >1 implies a percentage textual value
            return val / 100.0 if val > 1 else val
        except Exception:
            return 0.0

    def _click_analytics_range(self, time_range: str) -> None:
        """Attempt to click a time range toggle on the analytics page."""
        try:
            # Map friendly ranges
            tr = (time_range or '7D').upper()
            map_alias = {'30D': '4W', '90D': '3M'}
            tr = map_alias.get(tr, tr)
            candidates = [tr]
            # Try multiple locators (span/div/button text)
            for label in candidates:
                try:
                    btn = self.driver.find_element(By.XPATH, f"//button[.//div[normalize-space(text())='{label}'] or normalize-space(text())='{label}']")
                    if btn and btn.is_displayed():
                        btn.click()
                        time.sleep(1.0)
                        return
                except Exception:
                    continue
        except Exception:
            pass

    def _get_tile_number(self, label_text: str) -> Optional[str]:
        """Find the big number associated with a tile label (e.g., 'Impressions', 'Likes')."""
        try:
            # Find the tile by its label then read nearest bold/large number
            # Strategy: find div with font-medium containing label, then the next sibling with font-bold numeric
            # Use contains-based matching for robustness
            tile = self.driver.find_element(
                By.XPATH,
                f"//div[contains(@class,'font-medium') and contains(., '{label_text}')]"
            )
            if tile:
                # Look for a font-bold number in following nodes
                try:
                    val_el = tile.find_element(By.XPATH, "following::div[contains(@class,'font-bold')][1]")
                    return val_el.text.strip()
                except Exception:
                    pass
                # Fallback: search number-flow-react parent
                try:
                    val_el = tile.find_element(By.XPATH, "following::number-flow-react[1]")
                    return val_el.text.strip()
                except Exception:
                    pass
        except Exception:
            return None
        return None

    def fetch_account_analytics(self, time_range: str = "7D") -> Dict[str, Optional[float]]:
        """Scrape account analytics from X/Twitter Analytics page; returns a dict of metrics."""
        if not self.ensure_logged_in():
            logger.error("Cannot fetch analytics: not logged in")
            return {}

        try:
            self.driver.get("https://x.com/i/analytics")
            time.sleep(3)
            # Attempt to set range
            self._click_analytics_range(time_range)

            # Extract tiles
            metrics = {}
            def read(label, parser):
                raw = self._get_tile_number(label)
                if raw is None or raw == '':
                    return None
                try:
                    return parser(raw)
                except Exception:
                    return None

            metrics["verified_followers"] = read("Verified followers", self._parse_compact_number)
            metrics["impressions"] = read("Impressions", self._parse_compact_number)
            metrics["engagement_rate"] = read("Engagement rate", self._parse_percent)
            metrics["engagements"] = read("Engagements", self._parse_compact_number)
            metrics["profile_visits"] = read("Profile visits", self._parse_compact_number)
            metrics["replies"] = read("Replies", self._parse_compact_number)
            metrics["likes"] = read("Likes", self._parse_compact_number)
            metrics["reposts"] = read("Reposts", self._parse_compact_number)
            metrics["bookmarks"] = read("Bookmarks", self._parse_compact_number)
            metrics["shares"] = read("Shares", self._parse_compact_number)

            # Followers total may be on the page header or another location; try to find generic 'Followers'
            # If not found here, it can be supplied externally during ingest.
            followers_guess = read("Followers", self._parse_compact_number)
            if followers_guess is not None:
                metrics["total_followers"] = followers_guess

            # Sanitize None -> 0 for integers; keep engagement_rate as float with default 0.0
            for k in ["verified_followers","impressions","engagements","profile_visits","replies","likes","reposts","bookmarks","shares","total_followers"]:
                if metrics.get(k) is None:
                    metrics[k] = 0
            if metrics.get("engagement_rate") is None:
                metrics["engagement_rate"] = 0.0

            return metrics
        except Exception as e:
            logger.error(f"Error scraping account analytics: {e}")
            return {}

    def ingest_account_analytics(self, server_url: str = "http://127.0.0.1:5000", date: Optional[str] = None, time_range: str = "7D", metrics: Optional[Dict[str, Any]] = None) -> bool:
        """Fetch account analytics (if not provided) and POST to dashboard ingest endpoint."""
        try:
            payload = {
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "time_range": time_range.upper()
            }
            data = metrics or self.fetch_account_analytics(time_range=time_range)
            payload.update({k: v for k, v in (data or {}).items() if v is not None})

            if requests is None:
                # Provide a curl hint
                try:
                    curl_json = json.dumps(payload)
                    print("requests not available. Use this curl to ingest:")
                    print(f'curl -X POST {server_url}/api/analytics/ingest -H "Content-Type: application/json" -d \'{curl_json}\'')
                except Exception:
                    pass
                return False
            
            resp = requests.post(f"{server_url}/api/analytics/ingest", json=payload, headers={"Content-Type": "application/json"})
            if resp.status_code in (200, 201):
                return True
            else:
                logger.error(f"Failed to ingest analytics: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Error ingesting analytics: {e}")
            return False

    def check_premium_status(self) -> bool:
        """Check if the current account has Premium status"""
        try:
            # If not logged in, can't check
            if not self.ensure_logged_in():
                 return False
            
            # Navigate to profile to check for verified badge
            self.driver.get("https://x.com/settings/profile")
            time.sleep(3)
            
            # Look for verified badge (SVG path usually contains specific shape)
            # This is a heuristic; simpler is to assume False if unsure, or True if we want to enable features
            # For now, we'll try to find the "Verified" text or icon
            try:
                verified_indicators = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="icon-verified"]')
                if verified_indicators:
                    return True
            except Exception:
                pass
                
            return False
        except Exception as e:
            logger.error(f"Error checking premium status: {e}")
            return False

    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            logger.info("Driver closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
