import time
import random
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from data_models import ScheduleSlot, ActivityType
from linkedin_scraper import LinkedInScraper
from config import Config
from openai import AzureOpenAI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from data_models import ScheduleSlot, ActivityType
from linkedin_scraper import LinkedInScraper
from linkedin_api_handler import LinkedInAPIHandler
from config import Config
from openai import AzureOpenAI
from database_manager import DatabaseManager
from performance_tracker import PerformanceTracker

# Media Generation
try:
    from social_media_generator import (
        generate_image,
        resize_for_platform, 
        is_media_available
    )
    MEDIA_AVAILABLE = is_media_available()
except ImportError:
    MEDIA_AVAILABLE = False
    
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LinkedInAgent:
    def __init__(self, config_file: str = "agent_config.json"):
        self.config = Config()
        self.scraper = LinkedInScraper()
        self.api_handler = LinkedInAPIHandler()
        self.api_enabled = self.api_handler.validate_auth()
        
        if self.api_enabled:
            logger.info("✅ LinkedIn API Enabled (Hybrid Mode)")
        else:
            logger.info("⚠️ LinkedIn API Disabled (Browser Only Mode)")
        
        # Initialize Database and Tracker
        try:
            self.db_manager = DatabaseManager()
            self.performance_tracker = PerformanceTracker(self.db_manager)
        except Exception as e:
            logger.error(f"Failed to initialize DB/Tracker: {e}")
            self.db_manager = None
            self.performance_tracker = None
        
        # Load agent configuration
        try:
            with open(config_file, 'r') as f:
                self.agent_config = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            self.agent_config = self._get_default_config()
            
        # Azure OpenAI setup
        self.client = AzureOpenAI(
            api_key=self.config.AZURE_OPENAI_KEY if hasattr(self.config, 'AZURE_OPENAI_KEY') else "aefad978082243b2a79e279b203efc29",  
            api_version="2025-04-01-preview",
            azure_endpoint=self.config.AZURE_OPENAI_ENDPOINT if hasattr(self.config, 'AZURE_OPENAI_ENDPOINT') else "https://Panopticon.openai.azure.com/"
        )
        
    def _get_default_config(self):
        """Return default configuration"""
        return {
            "linkedin_topics": ["Industrial Automation", "Manufacturing Technology", "Future of Work"],
            "reply_styles": ["professional_insightful", "supportive_colleague"],
            "limits": {"posts_per_day": 1, "connections_per_day": 5}
        }

    def generate_post_content(self, topic: str = None) -> str:
        """Generate professional LinkedIn post content"""
        if not topic:
            topic = random.choice(self.agent_config.get('linkedin_topics', []))
            
        system_prompt = """You are a thought leader in Industrial Automation and Technology.
        Write a LinkedIn post that is professional, insightful, and engaging.
        - Use a professional but accessible tone.
        - Include relevant hashtags.
        - Encourage discussion with a question at the end.
        - Keep it under 1500 characters.
        """
        
        user_prompt = f"Write a LinkedIn post about: {topic}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=400,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating post content: {e}")
            return None

    def perform_activity(self, slot: ScheduleSlot) -> bool:
        """Execute a specific scheduled activity"""
        logger.info(f"🚀 Executing LinkedIn Activity: {slot.activity_type.value}")
        
        # Ensure login
        if not self.scraper.login():
            logger.error("❌ Failed to login to LinkedIn")
            return False

        try:
            if slot.activity_type == ActivityType.LINKEDIN_POST:
                return self._handle_post_creation(slot)
            elif slot.activity_type == ActivityType.LINKEDIN_IMAGE_POST:
                return self._handle_post_creation(slot, content_type="image")
            elif slot.activity_type == ActivityType.LINKEDIN_VIDEO_POST:
                return self._handle_post_creation(slot, content_type="video")
            elif slot.activity_type == ActivityType.LINKEDIN_THREAD:
                return self._handle_post_creation(slot, content_type="article")
                    
            elif slot.activity_type == ActivityType.LINKEDIN_ENGAGE or slot.activity_type == ActivityType.LINKEDIN_SCROLL_ENGAGE:
                logger.info("👀 Engaging with feed...")
                count = slot.activity_config.get('engagement_goals', {}).get('likes', 5)
                return self.scraper.engage_feed(count=count)

            elif slot.activity_type == ActivityType.LINKEDIN_SEARCH_ENGAGE:
                logger.info("🔍 Performing Search & Engage...")
                keywords = self.agent_config.get('linkedin_topics', ["AI", "Tech"])
                keyword = random.choice(keywords) if keywords else "Technology"
                return self.scraper.search_and_engage(keyword, count=3)
            
            elif slot.activity_type == ActivityType.LINKEDIN_REPLY or slot.activity_type == ActivityType.LINKEDIN_AUTO_REPLY:
                return self._handle_auto_reply(slot)
            
            elif slot.activity_type == ActivityType.LINKEDIN_CONTENT_CREATION:
                 logger.info("🧠 Brainstorming Content...")
                 time.sleep(5)
                 return True

            elif slot.activity_type == ActivityType.LINKEDIN_CONNECT:
                 # TODO: Implement connection logic
                 logger.info("👥 Connection management (placeholder)")
                 return True

            elif slot.activity_type == ActivityType.LINKEDIN_MONITOR:
                 logger.info("👀 Monitoring LinkedIn Feed (Passive Data Collection)...")
                 return self.scraper.engage_feed(count=3)
            
            elif slot.activity_type == ActivityType.LINKEDIN_RADAR_DISCOVERY:
                 logger.info("📡 Radar Discovery (placeholder)")
                 return True

            elif slot.activity_type == ActivityType.LINKEDIN_ANALYTICS or slot.activity_type == ActivityType.LINKEDIN_PERFORMANCE_ANALYSIS:
                 logger.info("📊 Performing Analytics Check...")
                 data = self.scraper.scrape_analytics()
                 logger.info(f"Analytics Data captured: {data}")
                 # Future: Save to DB explicitly if not already done in scraper
                 return True

            elif slot.activity_type == ActivityType.LINKEDIN_STRATEGY:
                 logger.info("🧠 Performing Strategy Review (Placeholder)...")
                 # Future: Call StrategyOptimizer.review("linkedin")
                 return True
            
            else:
                logger.warning(f"Unknown LinkedIn activity type: {slot.activity_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing activity: {e}")
            return False

    def _handle_post_creation(self, slot: ScheduleSlot) -> bool:
        """Handle content creation and posting with media support"""
        logger.info("✍️ Generating and posting content...")
        topic = slot.activity_config.get('topic')
        content = self.generate_post_content(topic)
        
        if not content:
            logger.error("❌ Failed to generate text content")
            return False
            
        media_path = None
        if MEDIA_AVAILABLE:
            # 50% chance of image if available
            if random.random() > 0.5:
                try:
                    logger.info("🎨 Generating media for post...")
                    # Generate prompt based on content
                    media_prompt = f"Professional minimal corporate illustration about: {content[:100]}..., vector style, business blue and white"
                    media_path = generate_image(media_prompt)
                    if media_path:
                        # Resize for LinkedIn (using imported helper if I had one, or generic)
                        media_path = resize_for_platform(media_path, "linkedin", "standard")
                except Exception as e:
                    logger.error(f"Media generation failed: {e}")
        
        # Try API First
        if self.api_enabled:
            logger.info("📡 Attempting API Post...")
            try:
                # Use the handler's simplified method which handles upload internally and returns Post ID
                post_id = self.api_handler.post_commentary(content, media_path)
                
                if post_id:
                     logger.info(f"✅ API Post Successful: {post_id}")
                     self._track_post(content, "api")
                     return True
                else:
                    logger.warning("⚠️ API Post Failed, falling back to Selenium...")
            except Exception as e:
                logger.error(f"API Post Error: {e}")

        # Fallback to Selenium
        if self.scraper.post_content(content, media_path=media_path):
            logger.info("✅ Selenium Post successful")
            self._track_post(content, "selenium")
            return True
        else:
            logger.error("❌ Post failed at scraper level")
            return False

    def _track_post(self, content, source):
        # Log to tracker
        if self.performance_tracker:
                self.performance_tracker.track_tweet_performance("linkedin_generic_id", {
                    "impressions": 0, "likes": 0, "replies": 0, # Placeholder
                    "platform": "linkedin",
                    "text": content,
                    "source": source
                })

    def _handle_auto_reply(self, slot: ScheduleSlot) -> bool:
        """Check notifications and reply"""
        logger.info("🔔 Checking notifications for auto-reply...")
        notifications = self.scraper.get_notifications(max_count=5)
        
        if not notifications:
            logger.info("No notifications to process")
            return True
            
        # For now, we just analyze them as we lack deep linking to reply
        # Future: Use LLM to classify priority
        for notif in notifications:
            logger.info(f"Analyzed notification: {notif['text']} (Unread: {notif['unread']})")
            
        return True
