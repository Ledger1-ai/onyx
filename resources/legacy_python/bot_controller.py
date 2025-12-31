import time
import random
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
# from selenium_scraper import TwitterScraper # Note: SeleniumScraper import removed from top-level to avoid immediate browser launch
from config import Config, logger
from openai import AzureOpenAI
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from unified_publisher import UnifiedPublisher  # Imported from new module

# Set up logging (if not already configured by config.py)
# If config.py handles logging setup, this block might be redundant or need adjustment.
# For now, keeping it as it was in the original document, assuming config.logger is a separate instance or configured similarly.
# If config.py's logger is meant to be the primary, this block should be removed.
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)



class TwitterSuperAgent: # Renamed to TwitterBot in the instruction's provided snippet, but keeping original name for consistency with the rest of the file.
    """
    Main controller for the Twitter bot.
    Now utilizes UnifiedPublisher for posting.
    """
    def __init__(self, config_file: str = "agent_config.json"):
        self.config = Config()
        self.publisher = UnifiedPublisher() # 'The Suit'
        
        # Legacy/Rogue components (Browser)
        # Initiated lazily or via 'Afterlife Mode' switch in future
        self.scraper = None # Original was TwitterScraper(), now set to None as per instruction
        
        # Load agent configuration
        try:
            with open(config_file, 'r') as f:
                self.agent_config = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            self.agent_config = self._get_default_config()
        
        # The Utility Company vision and mission
        self.company_vision = {
            "mission": "Industrial Automation as a Service - Democratizing access to advanced automation tools and empowering communities through technology",
            "core_values": [
                "Breaking down technological barriers",
                "Community-driven innovation", 
                "Sustainable industrial development",
                "Democratizing advanced automation",
                "Empowering local communities",
                "Ethical technology deployment",
                "Collaborative problem-solving",
                "Accessible industrial solutions"
            ],
            "focus_areas": [
                "Industrial IoT and automation",
                "Robotics and manufacturing",
                "Supply chain optimization", 
                "Community-scale manufacturing",
                "Sustainable production methods",
                "Technology education and access",
                "Local economic development",
                "Open-source automation tools"
            ]
        }
        
        # Dynamic account tracking
        self.discovered_accounts = []
        self.account_scores = {}
        
        # Azure OpenAI setup
        self.client = AzureOpenAI(
            api_key="aefad978082243b2a79e279b203efc29",  
            api_version="2025-04-01-preview",
            azure_endpoint="https://Panopticon.openai.azure.com/"
        )
        
        # Initialize database
        self.init_database()
        
        # Performance tracking
        self.strategy_metrics = {
            'reply_success_rate': 0.8,
            'trending_engagement_rate': 0.6,
            'quote_tweet_performance': 0.7,
            'content_performance': 0.5
        }
        
    def _get_default_config(self):
        """Return default configuration if file not found"""
        return {
            "target_accounts": ["elonmusk", "OpenAI", "sama"],
            "search_keywords": ["AI automation", "technology", "future"],
            "content_topics": ["AI and automation in society", "Philosophy of technology"],
            "reply_styles": ["insightful_sage", "curious_questioner"],
            "limits": {"replies_per_session": 5, "trending_interactions_per_session": 10},
            "delays": {"between_replies": [30, 90], "between_functions": [300, 900]},
            "filters": {"min_tweet_length": 30, "keywords_of_interest": ["AI", "technology"]},
            "performance_thresholds": {"min_replies_per_week": 10}
        }
        
    def init_database(self):
        """Initialize SQLite database for tracking activities and performance"""
        conn = sqlite3.connect('super_agent.db')
        
        # Activity tracking tables
        conn.execute('''CREATE TABLE IF NOT EXISTS replies_sent (
                            id INTEGER PRIMARY KEY,
                            original_tweet_id TEXT,
                            reply_id TEXT,
                            reply_text TEXT,
                            timestamp DATETIME,
                            engagement_score INTEGER DEFAULT 0
                        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS trending_interactions (
                            id INTEGER PRIMARY KEY,
                            tweet_id TEXT,
                            tweet_text TEXT,
                            action_type TEXT,
                            our_response TEXT,
                            timestamp DATETIME,
                            engagement_score INTEGER DEFAULT 0
                        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS quote_tweets (
                            id INTEGER PRIMARY KEY,
                            original_tweet_id TEXT,
                            quote_tweet_id TEXT,
                            quote_text TEXT,
                            timestamp DATETIME,
                            engagement_score INTEGER DEFAULT 0
                        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS content_posts (
                            id INTEGER PRIMARY KEY,
                            tweet_id TEXT,
                            content_text TEXT,
                            content_type TEXT,
                            timestamp DATETIME,
                            views INTEGER DEFAULT 0,
                            likes INTEGER DEFAULT 0,
                            retweets INTEGER DEFAULT 0,
                            replies INTEGER DEFAULT 0
                        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS performance_metrics (
                            id INTEGER PRIMARY KEY,
                            metric_type TEXT,
                            metric_value REAL,
                            timestamp DATETIME
                        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS analytics_data (
                            id INTEGER PRIMARY KEY,
                            tweet_id TEXT,
                            impressions INTEGER,
                            engagements INTEGER,
                            likes INTEGER,
                            retweets INTEGER,
                            replies INTEGER,
                            profile_clicks INTEGER,
                            url_clicks INTEGER,
                            hashtag_clicks INTEGER,
                            detail_expands INTEGER,
                            timestamp DATETIME
                        )''')
        
        # Add table for discovered accounts
        conn.execute('''CREATE TABLE IF NOT EXISTS discovered_accounts (
                            id INTEGER PRIMARY KEY,
                            username TEXT UNIQUE,
                            relevance_score REAL,
                            discovery_reason TEXT,
                            bio TEXT,
                            follower_count INTEGER,
                            following_count INTEGER,
                            tweet_count INTEGER,
                            last_evaluated DATETIME,
                            is_tracking BOOLEAN DEFAULT 0,
                            timestamp DATETIME
                        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS account_interactions (
                            id INTEGER PRIMARY KEY,
                            username TEXT,
                            interaction_type TEXT,
                            success BOOLEAN,
                            content TEXT,
                            timestamp DATETIME
                        )''')
        
        conn.commit()
        conn.close()
        
    def scrape_analytics_data(self):
        """Scrape analytics data from Twitter Analytics page"""
        logger.info("📊 Scraping analytics data...")
        
        try:
            # Navigate to analytics page
            self.scraper.driver.get("https://analytics.x.com")
            time.sleep(5)
            
            # Look for tweet performance data
            analytics_data = []
            
            # Find tweet cards or analytics rows
            tweet_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR, '[data-testid="analytics-tweet-row"]')
            
            if not tweet_elements:
                # Try alternative selectors
                tweet_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR, '.tweet-activity-row')
            
            for tweet_element in tweet_elements[:10]:  # Process last 10 tweets
                try:
                    # Extract metrics (this will need to be adapted based on Twitter's current analytics UI)
                    tweet_data = {}
                    
                    # Look for impressions
                    impressions_elem = tweet_element.find_element(By.CSS_SELECTOR, '[data-metric="impressions"]')
                    tweet_data['impressions'] = int(impressions_elem.text.replace(',', '')) if impressions_elem else 0
                    
                    # Look for engagements
                    engagements_elem = tweet_element.find_element(By.CSS_SELECTOR, '[data-metric="engagements"]')
                    tweet_data['engagements'] = int(engagements_elem.text.replace(',', '')) if engagements_elem else 0
                    
                    # Get tweet ID from link
                    tweet_link = tweet_element.find_element(By.CSS_SELECTOR, 'a[href*="/status/"]')
                    tweet_id = tweet_link.get_attribute('href').split('/status/')[-1].split('?')[0] if tweet_link else None
                    
                    if tweet_id:
                        tweet_data['tweet_id'] = tweet_id
                        analytics_data.append(tweet_data)
                        
                except Exception as e:
                    logger.debug(f"Error extracting analytics for tweet: {e}")
                    continue
            
            # Store analytics data in database
            if analytics_data:
                conn = sqlite3.connect('super_agent.db')
                for data in analytics_data:
                    conn.execute("""INSERT OR REPLACE INTO analytics_data 
                                   (tweet_id, impressions, engagements, timestamp) 
                                   VALUES (?, ?, ?, ?)""",
                               (data.get('tweet_id'), data.get('impressions', 0), 
                                data.get('engagements', 0), datetime.now()))
                conn.commit()
                conn.close()
                
                logger.info(f"📈 Stored analytics for {len(analytics_data)} tweets")
            else:
                logger.info("ℹ️ No analytics data found - may need to update selectors")
                
        except Exception as e:
            logger.error(f"Error scraping analytics data: {e}")
        
    def generate_reply(self, original_tweet: str, style: str = "insightful_sage") -> str:
        """Generate contextual replies using Azure OpenAI"""
        style_prompts = {
            "insightful_sage": "You are a wise, thoughtful commentator who adds valuable insights to conversations. Respond with depth and wisdom.",
            "curious_questioner": "You are genuinely curious and ask thoughtful follow-up questions that deepen the conversation.",
            "supportive_community": "You are supportive and encouraging, building up the community and fostering positive discussion.",
            "philosophical_thinker": "You approach topics from a philosophical angle, adding deeper meaning and context.",
            "practical_advisor": "You provide practical, actionable advice and real-world applications."
        }
        
        system_prompt = f"""You are @the_futility_co, a thoughtful Twitter account focused on technology, philosophy, and community empowerment. {style_prompts.get(style, style_prompts['insightful_sage'])}

        Guidelines:
        - Keep responses under 280 characters
        - Be genuine and add value to the conversation
        - Avoid generic responses or stock phrases
        - Vary sentence openings and rhythm
        - Don't be overly promotional
        - Match the tone of the original tweet
        - Ask questions when appropriate to encourage engagement
        - Do not repeat points already made in the tweet
        """
        
        user_prompt = f"Reply to this tweet in a way that adds value and encourages further discussion. Avoid repeating yourself. Tweet: '{original_tweet}'"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=100,
                temperature=1,
                frequency_penalty=0.7,
                presence_penalty=0.5
            )
            
            reply = response.choices[0].message.content.strip()
            max_length = self.agent_config.get('limits', {}).get('max_tweet_length', 280)
            return reply if len(reply) <= max_length else reply[:max_length-3] + "..."
            
        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            return None
    
    def generate_quote_tweet_commentary(self, original_tweet: str, context: str = "") -> str:
        """Generate insightful commentary for quote tweets"""
        system_prompt = """You are @the_futility_co, creating quote tweet commentary that adds valuable perspective to interesting content.
        
        Your commentary should:
        - Provide additional insight or context
        - Connect to broader themes of technology, philosophy, or community
        - Be thought-provoking but accessible
        - Encourage discussion
        - Stay under 200 characters to leave room for the quoted content
        - Use emojis appropriately but sparingly
        """
        
        user_prompt = f"Create quote tweet commentary for this tweet: '{original_tweet}'"
        if context:
            user_prompt += f" Context: {context}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=80,
                temperature=1
            )
            
            commentary = response.choices[0].message.content.strip()
            max_length = self.agent_config.get('limits', {}).get('max_quote_commentary_length', 200)
            return commentary if len(commentary) <= max_length else commentary[:max_length-3] + "..."
            
        except Exception as e:
            logger.error(f"Error generating quote tweet commentary: {e}")
            return None
    
    def generate_original_content(self, topic: str = None) -> str:
        """Generate original content posts"""
        if not topic:
            topic = random.choice(self.agent_config.get('content_topics', []))
            
        system_prompt = """You are @the_futility_co, creating original thought-provoking content about technology, philosophy, and community empowerment.
        
        Your content should:
        - Be original and insightful
        - Encourage thoughtful discussion
        - Connect to broader themes about human potential and technology
        - Be engaging but not clickbait
        - Include relevant emojis
        - Stay under 280 characters
        - Avoid being preachy or overly technical
        """
        
        user_prompt = f"Create an original tweet about: {topic}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=100,
                temperature=1
            )
            
            content = response.choices[0].message.content.strip()
            max_length = self.agent_config.get('limits', {}).get('max_tweet_length', 280)
            return content if len(content) <= max_length else content[:max_length-3] + "..."
            
        except Exception as e:
            logger.error(f"Error generating original content: {e}")
            return None
    
    def reply_bot_function(self):
        """Monitor and reply to mentions using API ('The Suit')"""
        logger.info("🤖 Running reply bot function (API Mode)...")
        
        try:
            # Get mentions via API
            mentions = self.publisher.twitter.get_mentions(count=10)
            
            max_replies = self.agent_config.get('limits', {}).get('replies_per_session', 5)
            replies_sent = 0
            
            for mention in mentions:
                if replies_sent >= max_replies:
                    break
                    
                mention_id = mention.get('id')
                mention_text = mention.get('text')
                author_id = mention.get('author_id')
                
                # Check if we've already replied
                conn = sqlite3.connect('super_agent.db')
                cursor = conn.execute("SELECT id FROM replies_sent WHERE original_tweet_id = ?", (mention_id,))
                
                if not cursor.fetchone():
                    # Generate reply
                    style = random.choice(self.agent_config.get('reply_styles', ['insightful_sage']))
                    generated_reply = self.generate_reply(mention_text, style)
                    
                    if generated_reply:
                        # Post reply via API
                        success = self.publisher.twitter.reply_to_tweet(mention_id, generated_reply)
                        
                        if success:
                            # Log the reply
                            conn.execute("INSERT INTO replies_sent (original_tweet_id, reply_text, timestamp) VALUES (?, ?, ?)",
                                       (mention_id, generated_reply, datetime.now()))
                            conn.commit()
                            
                            replies_sent += 1
                            logger.info(f"✅ Replied to mention {mention_id}: {generated_reply}")
                            
                            # Random delay
                            time.sleep(random.randint(5, 15))
                            
                conn.close()
                        
        except Exception as e:
            logger.error(f"Error in reply bot function: {e}")
    
    def trending_monitor_function(self):
        """Monitor trending tweets and engage with relevant content via API"""
        logger.info("📈 Running trending monitor function (API Mode)...")
        
        try:
            # Use API for trends search
            keywords = self.agent_config.get('search_keywords', [])
            max_interactions = self.agent_config.get('limits', {}).get('trending_interactions_per_session', 10)
            interactions_made = 0
            
            for keyword in keywords[:3]:  # Process first 3 keywords
                if interactions_made >= max_interactions:
                    break
                    
                logger.info(f"🔍 Searching for: {keyword}")
                # API Search
                tweets = self.publisher.twitter.search_tweets(keyword, max_results=10)
                
                for tweet in tweets:
                    if interactions_made >= max_interactions:
                        break
                        
                    tweet_text = tweet.get('text', '')
                    tweet_id = tweet.get('id', '')
                    # tweet_url = tweet.get('url', '') # API tweets might not have URL field directly
                    
                    # Apply filters
                    min_length = self.agent_config.get('filters', {}).get('min_tweet_length', 30)
                    spam_keywords = self.agent_config.get('filters', {}).get('avoid_spam_keywords', [])
                    
                    if len(tweet_text) < min_length or any(spam in tweet_text.lower() for spam in spam_keywords):
                        continue
                    
                    # Check if we've already interacted with this tweet
                    conn = sqlite3.connect('super_agent.db')
                    cursor = conn.execute("SELECT id FROM trending_interactions WHERE tweet_id = ?", (tweet_id,))
                    
                    if not cursor.fetchone():
                        # Decide on action (like, reply, or both)
                        action_type = random.choice(['like', 'reply', 'both'])
                        
                        if action_type in ['like', 'both']:
                            success = self.publisher.twitter.like_tweet(tweet_id)
                            if success:
                                logger.info(f"❤️ Liked tweet {tweet_id}")
                        
                        if action_type in ['reply', 'both']:
                            style = random.choice(self.agent_config.get('reply_styles', ['insightful_sage']))
                            reply_text = self.generate_reply(tweet_text, style)
                            
                            if reply_text:
                                success = self.publisher.twitter.reply_to_tweet(tweet_id, reply_text)
                                if success:
                                    logger.info(f"💬 Replied: {reply_text}")
                                    
                                    # Log the interaction
                                    conn.execute("INSERT INTO trending_interactions (tweet_id, tweet_text, action_type, our_response, timestamp) VALUES (?, ?, ?, ?, ?)",
                                               (tweet_id, tweet_text, action_type, reply_text, datetime.now()))
                        
                        conn.commit()
                        conn.close()
                        interactions_made += 1
                        
                        # Random delay between interactions
                        time.sleep(random.randint(45, 120))
                        
        except Exception as e:
            logger.error(f"Error in trending monitor function: {e}")
    
    def quote_tweet_function(self):
        """Find interesting tweets to quote tweet with commentary"""
        logger.info("🔄 Running quote tweet function...")
        
        try:
            # Use dynamic target accounts instead of static list
            target_accounts = self.get_dynamic_target_accounts()
            max_quotes = self.agent_config.get('limits', {}).get('quote_tweets_per_session', 3)
            quote_tweets_made = 0
            
            for account in target_accounts[:5]:  # Process top 5 accounts
                if quote_tweets_made >= max_quotes:
                    break
                    
                logger.info(f"🎯 Checking tweets from @{account}")
                tweets = self.scraper.get_user_tweets(account, count=5)
                
                for tweet in tweets:
                    if quote_tweets_made >= max_quotes:
                        break
                        
                    tweet_text = tweet.get('text', '')
                    tweet_id = tweet.get('id', '')
                    tweet_url = tweet.get('url', '')
                    
                    # Check if we've already quote tweeted this
                    conn = sqlite3.connect('super_agent.db')
                    cursor = conn.execute("SELECT id FROM quote_tweets WHERE original_tweet_id = ?", (tweet_id,))
                    
                    min_length = self.agent_config.get('filters', {}).get('min_tweet_length', 30)
                    keywords_of_interest = self.agent_config.get('filters', {}).get('keywords_of_interest', [])
                    
                    if not cursor.fetchone() and len(tweet_text) > min_length:
                        # Use AI to determine if tweet is relevant to our vision
                        if self.is_tweet_relevant_to_vision(tweet_text):
                            # Generate commentary
                            commentary = self.generate_quote_tweet_commentary(tweet_text, f"From @{account}")
                            
                            if commentary:
                                # Navigate to tweet
                                self.scraper.driver.get(tweet_url)
                                time.sleep(3)
                                
                                # Find and click retweet button
                                try:
                                    retweet_button = self.scraper.driver.find_element(By.CSS_SELECTOR, '[data-testid="retweet"]')
                                    retweet_button.click()
                                    time.sleep(2)
                                    
                                    # Click "Quote Tweet" option
                                    quote_option = self.scraper.driver.find_element(By.CSS_SELECTOR, '[data-testid="retweetConfirm"]')
                                    quote_option.click()
                                    time.sleep(2)
                                    
                                    # Add commentary
                                    comment_box = self.scraper.driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]')
                                    self.scraper._type_like_human(comment_box, commentary)
                                    time.sleep(2)
                                    
                                    # Send quote tweet
                                    send_button = self.scraper.driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetButton"]')
                                    send_button.click()
                                    time.sleep(3)
                                    
                                    # Log the quote tweet
                                    conn.execute("INSERT INTO quote_tweets (original_tweet_id, quote_text, timestamp) VALUES (?, ?, ?)",
                                               (tweet_id, commentary, datetime.now()))
                                    conn.commit()
                                    
                                    quote_tweets_made += 1
                                    logger.info(f"🔄 Quote tweeted with: {commentary}")
                                    
                                    # Random delay between quote tweets
                                    delay_range = self.agent_config.get('delays', {}).get('between_quote_tweets', [300, 600])
                                    time.sleep(random.randint(*delay_range))
                                    
                                except Exception as e:
                                    logger.error(f"Error quote tweeting: {e}")
                    
                    conn.close()
                    
        except Exception as e:
            logger.error(f"Error in quote tweet function: {e}")
    
    def content_creation_function(self):
        """Create and post original content via API"""
        logger.info("✍️ Running content creation function (API Mode)...")
        
        try:
            # Check daily content limit
            conn = sqlite3.connect('super_agent.db')
            today = datetime.now().date()
            today_posts = conn.execute("SELECT COUNT(*) FROM content_posts WHERE DATE(timestamp) = ?", (today,)).fetchone()[0]
            max_posts_per_day = self.agent_config.get('limits', {}).get('content_posts_per_day', 3)
            
            if today_posts >= max_posts_per_day:
                logger.info(f"ℹ️ Daily content limit reached ({today_posts}/{max_posts_per_day})")
                conn.close()
                return False
            
            # Generate original content
            topic = random.choice(self.agent_config.get('content_topics', []))
            content = self.generate_original_content(topic)
            
            if content:
                # Use UnifiedPublisher to post to Twitter (and potentially others)
                # For Phase 1, we stick to Twitter default.
                # ToDo: Add logic to decide platforms based on topic/schedule?
                results = asyncio.run(self.publisher.publish(content, platforms=["twitter"]))
                
                if results.get("twitter", {}).get("success"):
                    # Log the content post
                    conn.execute("INSERT INTO content_posts (content_text, content_type, timestamp) VALUES (?, ?, ?)",
                               (content, 'original', datetime.now()))
                    conn.commit()
                    logger.info(f"📝 Posted original content: {content}")
                    conn.close()
                    return True
                else:
                    logger.error(f"Failed to publish content: {results}")
            
            conn.close()
                    
        except Exception as e:
            logger.error(f"Error in content creation function: {e}")
            
        return False
    
    def performance_monitoring_function(self):
        """Monitor performance metrics and adjust strategy"""
        logger.info("📊 Running performance monitoring function...")
        
        try:
            # Scrape analytics data first
            self.scrape_analytics_data()
            
            conn = sqlite3.connect('super_agent.db')
            
            # Count recent activities
            recent_date = datetime.now() - timedelta(days=7)
            
            replies_count = conn.execute("SELECT COUNT(*) FROM replies_sent WHERE timestamp > ?", (recent_date,)).fetchone()[0]
            trending_count = conn.execute("SELECT COUNT(*) FROM trending_interactions WHERE timestamp > ?", (recent_date,)).fetchone()[0]
            quote_count = conn.execute("SELECT COUNT(*) FROM quote_tweets WHERE timestamp > ?", (recent_date,)).fetchone()[0]
            content_count = conn.execute("SELECT COUNT(*) FROM content_posts WHERE timestamp > ?", (recent_date,)).fetchone()[0]
            
            # Calculate engagement rates from analytics
            total_impressions = conn.execute("SELECT SUM(impressions) FROM analytics_data WHERE timestamp > ?", (recent_date,)).fetchone()[0] or 0
            total_engagements = conn.execute("SELECT SUM(engagements) FROM analytics_data WHERE timestamp > ?", (recent_date,)).fetchone()[0] or 0
            engagement_rate = (total_engagements / total_impressions * 100) if total_impressions > 0 else 0
            
            # Log metrics
            metrics = {
                'replies_per_week': replies_count,
                'trending_interactions_per_week': trending_count,
                'quote_tweets_per_week': quote_count,
                'content_posts_per_week': content_count,
                'engagement_rate': engagement_rate,
                'total_impressions': total_impressions,
                'total_engagements': total_engagements
            }
            
            for metric, value in metrics.items():
                conn.execute("INSERT INTO performance_metrics (metric_type, metric_value, timestamp) VALUES (?, ?, ?)",
                           (metric, value, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📈 Weekly metrics: {metrics}")
            
            # Strategy adjustment based on thresholds
            thresholds = self.agent_config.get('performance_thresholds', {})
            
            if replies_count < thresholds.get('min_replies_per_week', 10):
                logger.info("🔧 Strategy adjustment: Increasing reply frequency")
                self.strategy_metrics['reply_success_rate'] += 0.1
            
            if trending_count < thresholds.get('min_trending_interactions_per_week', 20):
                logger.info("🔧 Strategy adjustment: Increasing trending monitoring")
                self.strategy_metrics['trending_engagement_rate'] += 0.1
            
            if engagement_rate < 2.0:  # Less than 2% engagement rate
                logger.info("🔧 Strategy adjustment: Focusing on higher quality content")
                self.strategy_metrics['content_performance'] += 0.1
                
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
    
    def discover_relevant_accounts(self, seed_keywords: List[str] = None) -> List[str]:
        """Discover accounts relevant to The Utility Company's vision"""
        logger.info("🔍 Discovering relevant accounts...")
        
        if seed_keywords is None:
            seed_keywords = [
                "industrial automation",
                "manufacturing technology", 
                "IoT industry",
                "robotics manufacturing",
                "automation solutions",
                "industrial IoT",
                "smart manufacturing",
                "Industry 4.0",
                "automation as a service",
                "democratizing technology"
            ]
        
        discovered_accounts = []
        
        try:
            for keyword in seed_keywords[:5]:  # Process first 5 keywords
                logger.info(f"🔎 Searching for accounts discussing: {keyword}")
                
                # Search for tweets about the keyword
                tweets = self.scraper.search_tweets(keyword, max_results=20)
                
                for tweet in tweets:
                    author = tweet.get('author', '')
                    if author and author not in discovered_accounts:
                        # Evaluate account relevance
                        relevance_score = self.evaluate_account_relevance(author)
                        
                        if relevance_score > 0.6:  # Threshold for relevance
                            discovered_accounts.append(author)
                            self.account_scores[author] = relevance_score
                            
                            # Store in database
                            self.store_discovered_account(author, relevance_score, f"Found via '{keyword}' search")
                            
                            logger.info(f"✅ Discovered relevant account: @{author} (score: {relevance_score:.2f})")
                
                time.sleep(random.randint(10, 30))  # Rate limiting
                
        except Exception as e:
            logger.error(f"Error discovering accounts: {e}")
        
        return discovered_accounts

    def evaluate_account_relevance(self, username: str) -> float:
        """Evaluate how relevant an account is to The Utility Company's vision"""
        try:
            # Get account information
            account_info = self.scraper.get_user_profile(username)
            if not account_info:
                return 0.0
                
            bio = account_info.get('bio', '')
            recent_tweets = self.scraper.get_user_tweets(username, count=10)
            
            # Combine bio and recent tweets for analysis
            content_to_analyze = bio + " " + " ".join([tweet.get('text', '') for tweet in recent_tweets])
            
            # Use AI to score relevance
            system_prompt = f"""You are evaluating Twitter accounts for relevance to The Utility Company's mission and vision.

Company Mission: {self.company_vision['mission']}

Core Values: {', '.join(self.company_vision['core_values'])}

Focus Areas: {', '.join(self.company_vision['focus_areas'])}

Evaluate the following account content and provide a relevance score from 0.0 to 1.0, where:
- 0.0-0.3: Not relevant or contradictory to our mission
- 0.4-0.6: Somewhat relevant, occasional overlap
- 0.7-0.8: Highly relevant, strong alignment
- 0.9-1.0: Extremely relevant, perfect alignment

Consider:
1. Alignment with industrial automation and manufacturing
2. Focus on democratizing technology access
3. Community empowerment and local development
4. Sustainable and ethical technology use
5. Innovation in automation and IoT
6. Educational content about technology
7. Open-source and accessible solutions

Return only the numerical score (e.g., 0.75)."""

            user_prompt = f"Account content to evaluate: {content_to_analyze[:2000]}"  # Limit content length
            
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=10,
                temperature=1
            )
            
            score_text = response.choices[0].message.content.strip()
            try:
                score = float(score_text)
                return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            except ValueError:
                logger.warning(f"Could not parse relevance score for @{username}: {score_text}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error evaluating account @{username}: {e}")
            return 0.0

    def store_discovered_account(self, username: str, score: float, reason: str):
        """Store discovered account in database"""
        try:
            conn = sqlite3.connect('super_agent.db')
            
            # Get additional account info if available
            account_info = self.scraper.get_user_profile(username)
            bio = account_info.get('bio', '') if account_info else ''
            follower_count = account_info.get('followers', 0) if account_info else 0
            following_count = account_info.get('following', 0) if account_info else 0
            tweet_count = account_info.get('tweets', 0) if account_info else 0
            
            conn.execute("""INSERT OR REPLACE INTO discovered_accounts 
                           (username, relevance_score, discovery_reason, bio, follower_count, 
                            following_count, tweet_count, last_evaluated, timestamp) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (username, score, reason, bio, follower_count, following_count, 
                         tweet_count, datetime.now(), datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing discovered account: {e}")

    def get_dynamic_target_accounts(self, min_score: float = 0.7, max_accounts: int = 15) -> List[str]:
        """Get dynamically discovered target accounts based on relevance scores"""
        try:
            conn = sqlite3.connect('super_agent.db')
            
            # Get top accounts by relevance score
            cursor = conn.execute("""SELECT username, relevance_score 
                                   FROM discovered_accounts 
                                   WHERE relevance_score >= ? 
                                   ORDER BY relevance_score DESC, follower_count DESC 
                                   LIMIT ?""", (min_score, max_accounts))
            
            accounts = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # If we don't have enough discovered accounts, run discovery
            if len(accounts) < 5:
                logger.info("🔄 Not enough relevant accounts found, running discovery...")
                self.discover_relevant_accounts()
                
                # Try again after discovery
                conn = sqlite3.connect('super_agent.db')
                cursor = conn.execute("""SELECT username, relevance_score 
                                       FROM discovered_accounts 
                                       WHERE relevance_score >= ? 
                                       ORDER BY relevance_score DESC, follower_count DESC 
                                       LIMIT ?""", (min_score, max_accounts))
                accounts = [row[0] for row in cursor.fetchall()]
                conn.close()
            
            # Fallback to static accounts if still not enough
            if len(accounts) < 3:
                fallback_accounts = ["elonmusk", "OpenAI", "sama", "ylecun", "karpathy"]
                accounts.extend([acc for acc in fallback_accounts if acc not in accounts])
            
            logger.info(f"📊 Using {len(accounts)} dynamically discovered target accounts")
            return accounts[:max_accounts]
            
        except Exception as e:
            logger.error(f"Error getting dynamic target accounts: {e}")
            return ["elonmusk", "OpenAI", "sama"]  # Fallback

    def update_account_discovery(self):
        """Periodically update account discovery and relevance scores"""
        logger.info("🔄 Updating account discovery...")
        
        try:
            # Run discovery for new accounts
            self.discover_relevant_accounts()
            
            # Re-evaluate existing accounts that haven't been checked recently
            conn = sqlite3.connect('super_agent.db')
            one_week_ago = datetime.now() - timedelta(days=7)
            
            cursor = conn.execute("""SELECT username FROM discovered_accounts 
                                   WHERE last_evaluated < ? OR last_evaluated IS NULL""", 
                                 (one_week_ago,))
            
            accounts_to_update = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            for username in accounts_to_update[:10]:  # Limit to 10 updates per run
                logger.info(f"🔄 Re-evaluating @{username}")
                new_score = self.evaluate_account_relevance(username)
                
                conn = sqlite3.connect('super_agent.db')
                conn.execute("""UPDATE discovered_accounts 
                               SET relevance_score = ?, last_evaluated = ? 
                               WHERE username = ?""",
                            (new_score, datetime.now(), username))
                conn.commit()
                conn.close()
                
                time.sleep(random.randint(10, 20))  # Rate limiting
                
        except Exception as e:
            logger.error(f"Error updating account discovery: {e}")

    def is_tweet_relevant_to_vision(self, tweet_text: str) -> bool:
        """Use AI to determine if a tweet is relevant to The Utility Company's vision"""
        try:
            system_prompt = f"""You are evaluating tweets for relevance to The Utility Company's mission.

Mission: {self.company_vision['mission']}
Focus Areas: {', '.join(self.company_vision['focus_areas'])}

Determine if this tweet is relevant to our vision and worth engaging with. 
Return only 'YES' if relevant, 'NO' if not relevant."""

            user_prompt = f"Tweet to evaluate: {tweet_text}"
            
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=5,
                temperature=1
            )
            
            result = response.choices[0].message.content.strip().upper()
            return result == "YES"
            
        except Exception as e:
            logger.error(f"Error evaluating tweet relevance: {e}")
            return False

    def run_autonomous_cycle(self):
        """Run one complete autonomous cycle"""
        logger.info("🚀 Starting autonomous cycle...")
        
        # Login if not already logged in
        if not self.scraper.logged_in:
            logger.info("🔐 Logging in...")
            success = self.scraper.login()
            if not success:
                logger.error("❌ Login failed, cannot proceed")
                return False
        
        # Update account discovery periodically (every few cycles)
        if random.random() < 0.3:  # 30% chance to update discovery
            self.update_account_discovery()
        
        # Run functions in order with delays
        functions = [
            ('reply_bot', self.reply_bot_function),
            ('trending_monitor', self.trending_monitor_function),
            ('quote_tweet', self.quote_tweet_function),
            ('content_creation', self.content_creation_function),
            ('performance_monitoring', self.performance_monitoring_function)
        ]
        
        for func_name, func in functions:
            try:
                logger.info(f"🔄 Running {func_name}...")
                func()
                
                # Random delay between functions
                delay_range = self.agent_config.get('delays', {}).get('between_functions', [300, 900])
                delay = random.randint(*delay_range)
                logger.info(f"⏱️ Waiting {delay//60} minutes before next function...")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ Error in {func_name}: {e}")
                continue
        
        logger.info("✅ Autonomous cycle completed")
        return True
    
    def run_continuous(self, cycle_interval_hours: int = None):
        """Run the super agent continuously"""
        if cycle_interval_hours is None:
            cycle_interval_hours = self.agent_config.get('delays', {}).get('cycle_interval_hours', 4)
            
        logger.info(f"🤖 Starting Twitter Super Agent - Running cycles every {cycle_interval_hours} hours")
        
        while True:
            try:
                success = self.run_autonomous_cycle()
                
                if success:
                    logger.info(f"✅ Cycle completed successfully")
                else:
                    logger.error("❌ Cycle failed")
                
                # Wait for next cycle
                wait_time = cycle_interval_hours * 3600  # Convert to seconds
                logger.info(f"😴 Sleeping for {cycle_interval_hours} hours until next cycle...")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logger.info("👋 Shutting down Super Agent...")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                logger.info("⏱️ Waiting 30 minutes before retry...")
                time.sleep(1800)  # Wait 30 minutes on error
    
    def close(self):
        """Clean shutdown"""
        if self.scraper:
            self.scraper.close()

if __name__ == "__main__":
    import sys
    
    agent = TwitterSuperAgent()
    
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == "test":
                # Run single cycle for testing
                agent.run_autonomous_cycle()
            elif sys.argv[1] == "reply":
                agent.reply_bot_function()
            elif sys.argv[1] == "trending":
                agent.trending_monitor_function()
            elif sys.argv[1] == "quote":
                agent.quote_tweet_function()
            elif sys.argv[1] == "content":
                agent.content_creation_function()
            elif sys.argv[1] == "monitor":
                agent.performance_monitoring_function()
            elif sys.argv[1] == "analytics":
                agent.scrape_analytics_data()
            else:
                print("Usage: python bot_controller.py [test|reply|trending|quote|content|monitor|analytics]")
        else:
            # Run continuously
            agent.run_continuous()
            
    except KeyboardInterrupt:
        print("\n👋 Super Agent shutting down...")
    finally:
        agent.close() 