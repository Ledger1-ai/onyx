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
import undetected_chromedriver as uc

from typing import List, Dict, Optional, Any
from config import Config, logger
import json
from datetime import datetime

class LinkedInScraper:
    """Selenium-based LinkedIn scraper for web automation"""
    
    def __init__(self, headless=False, use_persistent_profile=True):
        """
        Initialize the LinkedIn scraper with Selenium WebDriver
        """
        self.config = Config()
        self.driver = None
        self.wait = None
        self.headless = headless
        self.use_persistent_profile = use_persistent_profile
        self.profile_dir = self._get_profile_directory()
        self.logged_in = False
        self.setup_driver()
        
    def _get_profile_directory(self):
        """Resolve persistent Chrome profile directory"""
        try:
            configured = getattr(self.config, "PROFILE_DIRECTORY", None)
        except Exception:
            configured = None

        # Use a distinct profile for LinkedIn if possible, or share. 
        # Ideally, we should separate them to avoid cross-contamination or locking issues.
        # But for now, we'll use a specific LinkedIn profile folder.
        path = Path("browser_profiles/linkedin_automation_profile")

        if not path.is_absolute():
            path = Path.cwd() / path

        path.mkdir(parents=True, exist_ok=True)
        print(f"[LCK] Using Chrome user data dir for LinkedIn: {path}")
        return str(path)
    
    def setup_driver(self):
        """Setup Chrome WebDriver with persistent profile support"""
        try:
            chrome_options = Options()
            
            # Persistent profile
            if self.use_persistent_profile:
                chrome_options.add_argument(f"--user-data-dir={self.profile_dir}")
                chrome_options.add_argument("--profile-directory=Default")
            
            # Anti-detection
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Headless?
            if self.headless:
                chrome_options.add_argument("--headless=new")
                
            # Initialize driver
            try:
                self.driver = uc.Chrome(options=chrome_options)
            except Exception:
                print("⚠️ undetected-chromedriver failed, falling back to standard")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
            self.driver.set_window_size(1920, 1080)
            self.wait = WebDriverWait(self.driver, 15)
            
            print("[OK] LinkedIn WebDriver initialized")
            
            # Check login
            self.logged_in = self.check_login_status()
            
        except Exception as e:
            print(f"[ERR] Error setting up LinkedIn WebDriver: {e}")
            raise

    def check_login_status(self):
        """Check if logged into LinkedIn"""
        try:
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)
            
            # Look for feed indicators
            indicators = [
                (By.ID, "global-nav-typeahead"),
                (By.CSS_SELECTOR, ".global-nav__me-photo"),
                (By.CSS_SELECTOR, "div.feed-identity-module")
            ]
            
            for by, sel in indicators:
                try:
                    if self.driver.find_element(by, sel).is_displayed():
                        print("[OK] Already logged in to LinkedIn")
                        return True
                except:
                    continue
            
            print("[LCK] Not logged in to LinkedIn")
            return False
        except Exception:
            return False

    def login(self):
        """Perform login flow"""
        if self.logged_in:
            return True
            
        print("[REQ] LinkedIn Login Required")
        print("Please log in manually in the browser window.")
        self.driver.get("https://www.linkedin.com/login")
        
        # Wait for user to log in
        input("Press ENTER after you have successfully logged in to LinkedIn...")
        
        self.logged_in = self.check_login_status()
        return self.logged_in

    def _random_delay(self, min_s=2, max_s=5):
        time.sleep(random.uniform(min_s, max_s))
        
    def _type_like_human(self, element, text):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

    def post_content(self, text: str, media_path: Optional[str] = None):
        """Post content to LinkedIn with robust selectors"""
        if not self.logged_in:
            logger.error("Not logged in to LinkedIn")
            return False
            
        try:
            self.driver.get("https://www.linkedin.com/feed/")
            self._random_delay(3, 5)
            
            # Click "Start a post" - Try multiple robust selectors
            try:
                # Primary: Text based
                start_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Start a post')]/..")))
                start_btn.click()
            except:
                try:
                    # Secondary: Class based (fallback)
                    self.driver.find_element(By.CSS_SELECTOR, "button.share-box-feed-entry__trigger").click()
                except Exception as e:
                    logger.error(f"Could not find 'Start a post' button: {e}")
                    return False

            self._random_delay(1, 2)
            
            # Handle media
            if media_path:
                try:
                    # Finding the hidden file input is usually the most reliable way
                    # LinkedIn's file input is mostly consistently present in the modal
                    file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                    file_input.send_keys(os.path.abspath(media_path))
                    logger.info(f"Media uploaded: {media_path}")
                    self._random_delay(5, 8) # Wait for upload
                    
                    # Check for "Done" button if it opens an image editor
                    try:
                        done_btn = self.driver.find_element(By.XPATH, "//span[text()='Done']/..")
                        if done_btn.is_displayed():
                            done_btn.click()
                            self._random_delay(1, 2)
                    except:
                        pass
                except Exception as e:
                    logger.warning(f"Failed to upload media: {e}")

            # Type text - Look for the editor
            try:
                # Editor usually has role='textbox' and aria-label='Text editor...'
                editor = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='textbox']")))
                editor.click()
                self._type_like_human(editor, text)
            except Exception as e:
                logger.error(f"Could not type text: {e}")
                return False
                
            self._random_delay(2, 3)
            
            # Click Post
            try:
                # Button usually says "Post"
                post_btn = self.driver.find_element(By.XPATH, "//button[contains(., 'Post')]")
                # specific check to ensure we get the primary action button in the modal footer
                # filtering enabled buttons only
                
                if post_btn.is_enabled():
                    post_btn.click()
                    logger.info("Content posted to LinkedIn")
                    self._random_delay(3, 5)
                    return True
                else:
                    logger.warning("Post button not enabled")
                    return False
            except Exception as e:
                logger.error(f"Could not find or click Post button: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {e}")
            return False

    def engage_feed(self, count=5):
        """Scroll feed and like/comment with robust selectors"""
        if not self.logged_in:
            return False
        
        try:
            self.driver.get("https://www.linkedin.com/feed/")
            self._random_delay(3, 5)
            
            actions = 0
            scrolled = 0
            
            while actions < count and scrolled < 10:
                # Scroll down
                self.driver.execute_script("window.scrollBy(0, 500);")
                self._random_delay(1, 2)
                scrolled += 1
                
                # Find posts (urn:li:activity)
                # Using XPATH to find posts that have a Like button specifically
                # This avoids ad wrappers that might not be interactable in the same way
                try:
                    # Find buttons that look like "Like"
                    # LinkedIn "Like" button typically has aria-label="React Like..." (or similar depending on language)
                    # We look for buttons with "Like" in aria-label but NOT "Undo Like"
                    like_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Like') and not(contains(@aria-label, 'Undo'))]")
                    
                    for btn in like_buttons:
                        if actions >= count:
                            break
                            
                        try:
                            if not btn.is_displayed():
                                continue
                                
                            # Like random posts
                            if random.random() > 0.6:
                                self.driver.execute_script("arguments[0].click();", btn)
                                logger.info(f"Liked a post")
                                actions += 1
                                self._random_delay(2, 4)
                        except:
                            continue
                except:
                    pass
                        
            return True
        except Exception as e:
            logger.error(f"Error engaging feed: {e}")
            return False

    def search_and_engage(self, keyword: str, count: int = 3) -> bool:
        """Search for a keyword and engage with top posts"""
        if not self.logged_in: 
            return False
            
        try:
            # 1. Perform Search
            logger.info(f"🔎 Searching LinkedIn for: {keyword}")
            encoded_keyword = requests.utils.quote(keyword)
            # Filter by "Posts" (cluster=content) and "Latest" (sortBy="date_posted") implies 'relevance' usually better for engagement
            # actually sortBy="date_posted" is correct for "Monitor"
            self.driver.get(f"https://www.linkedin.com/search/results/content/?keywords={encoded_keyword}&origin=GLOBAL_SEARCH_HEADER&sortBy=\"date_posted\"")
            self._random_delay(4, 6)
            
            actions = 0
            scrolled = 0
            
            #Reuse basic scroll & like logic
            while actions < count and scrolled < 5:
                self.driver.execute_script("window.scrollBy(0, 500);")
                self._random_delay(1, 2)
                scrolled += 1
                
                try:
                    # Look for Like buttons in search results
                    like_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Like') and not(contains(@aria-label, 'Undo'))]")
                    for btn in like_buttons:
                        if actions >= count: break
                        try:
                            if btn.is_displayed() and random.random() > 0.5:
                                self.driver.execute_script("arguments[0].click();", btn)
                                logger.info(f"Liked a search result for '{keyword}'")
                                actions += 1
                                self._random_delay(2, 5)
                        except: pass
                except: pass
                
            return True
        except Exception as e:
            logger.error(f"Error searching and engaging: {e}")
            return False

    def get_notifications(self, max_count=5) -> List[Dict]:
        """Scrape recent notifications"""
        if not self.logged_in: return []
        
        notifications = []
        try:
            self.driver.get("https://www.linkedin.com/notifications/")
            self._random_delay(3, 5)
            
            # Notification cards
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".nt-card")
            
            for card in cards[:max_count]:
                try:
                    text_elem = card.find_element(By.CSS_SELECTOR, ".nt-card__text")
                    text = text_elem.text
                    # Check if unread
                    unread = "nt-card--unread" in card.get_attribute("class")
                    
                    notifications.append({
                        "text": text,
                        "unread": unread,
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    continue
                    
            logger.info(f"📥 Scraped {len(notifications)} notifications")
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []

    def scrape_analytics(self) -> Dict:
        """Scrape basic account analytics (followers, profile views)"""
        if not self.logged_in: return {}
        
        analytics = {"timestamp": datetime.now().isoformat()}
        
        try:
            self.driver.get("https://www.linkedin.com/in/me/dashboard/") # LinkedIn dashboard sometimes redirects
            self._random_delay(3, 5)
            
            # Attempt to find stats on profile page or dashboard
            # Usually checking profile is safer
            self.driver.get("https://www.linkedin.com/in/") # Redirects to own profile
            self._random_delay(3, 5)

            # Followers (often in header)
            try:
                # "500 connections" or "1,200 followers"
                # This selector is very brittle, using a generic text search might be better
                # Look for "followers" link
                followers_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, "followers")
                followers_text = followers_link.text
                # Extract number
                count = ''.join(filter(str.isdigit, followers_text))
                analytics["followers"] = int(count) if count else 0
            except:
                analytics["followers"] = 0
            
            logger.info(f"📊 Scraped Analytics: {analytics}")
            return analytics
            
        except Exception as e:
            logger.error(f"Error scraping analytics: {e}")
            return analytics
