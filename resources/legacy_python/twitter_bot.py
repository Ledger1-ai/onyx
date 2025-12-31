import time
import random
import schedule
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from selenium_scraper import TwitterScraper
from config import Config, logger
import json
import os

class TwitterBot:
    """Main Twitter bot controller for autonomous operations"""
    
    def __init__(self):
        self.config = Config()
        self.scraper = None
        self.activity_log = []
        self.last_actions = {
            'tweet': datetime.min,
            'reply': datetime.min,
            'retweet': datetime.min,
            'search': datetime.min
        }
        self._load_activity_log()
    
    def _load_activity_log(self):
        """Load activity log from file"""
        log_file = 'activity_log.json'
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    self.activity_log = json.load(f)
                logger.info(f"Loaded {len(self.activity_log)} activity records")
            except Exception as e:
                logger.error(f"Failed to load activity log: {e}")
                self.activity_log = []
    
    def _save_activity_log(self):
        """Save activity log to file"""
        log_file = 'activity_log.json'
        try:
            with open(log_file, 'w') as f:
                json.dump(self.activity_log[-1000:], f, indent=2)  # Keep last 1000 records
        except Exception as e:
            logger.error(f"Failed to save activity log: {e}")
    
    def _log_activity(self, action: str, details: Dict):
        """Log bot activity"""
        activity = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        self.activity_log.append(activity)
        self._save_activity_log()
    
    def _should_perform_action(self, action_type: str) -> bool:
        """Check if action should be performed based on rate limits and timing"""
        now = datetime.now()
        last_action = self.last_actions.get(action_type, datetime.min)
        
        # Check time-based limits
        time_limits = {
            'tweet': timedelta(minutes=30),  # At least 30 min between tweets
            'reply': timedelta(minutes=10),  # At least 10 min between replies
            'retweet': timedelta(minutes=15), # At least 15 min between retweets
            'search': timedelta(minutes=5)    # At least 5 min between searches
        }
        
        if now - last_action < time_limits.get(action_type, timedelta(minutes=5)):
            return False
        
        # Check hourly limits
        hour_ago = now - timedelta(hours=1)
        recent_actions = [
            log for log in self.activity_log 
            if log['action'] == action_type and 
               datetime.fromisoformat(log['timestamp']) > hour_ago
        ]
        
        hourly_limits = {
            'tweet': self.config.MAX_TWEETS_PER_HOUR,
            'reply': self.config.MAX_REPLIES_PER_HOUR,
            'retweet': self.config.MAX_RETWEETS_PER_HOUR,
            'search': 20  # Search limit
        }
        
        return len(recent_actions) < hourly_limits.get(action_type, 10)
    
    def initialize(self) -> bool:
        """Initialize the bot and login"""
        try:
            logger.info("Initializing Twitter Bot")
            
            # Validate configuration
            config_status = self.config.validate()
            if not config_status['valid']:
                logger.error(f"Invalid configuration: {config_status['missing_fields']}")
                return False
            
            # Initialize scraper
            self.scraper = TwitterScraper()
            
            # Login
            if not self.scraper.login():
                logger.error("Failed to login")
                return False
            
            logger.info("Twitter Bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            return False
    
    def generate_tweet_content(self, topic: str = None) -> str:
        """Generate tweet content based on topic or trending keywords"""
        # Simple tweet templates - you can enhance this with AI/ML
        templates = [
            "Exploring {topic} today. What are your thoughts? 🤔",
            "Just discovered something interesting about {topic}! 💡",
            "Working with {topic} - always learning something new! 🚀",
            "Anyone else excited about the future of {topic}? 🌟",
            "Quick thoughts on {topic}: It's evolving so fast! ⚡",
            "Diving deep into {topic} today. The possibilities are endless! 🔥"
        ]
        
        if not topic:
            topic = random.choice(self.config.SEARCH_KEYWORDS)
        
        template = random.choice(templates)
        tweet = template.format(topic=topic)
        
        # Add random hashtag
        if random.random() < 0.7:  # 70% chance to add hashtag
            hashtag = random.choice(self.config.TARGET_HASHTAGS)
            tweet += f" {hashtag}"
        
        return tweet
    
    def generate_reply_content(self, original_tweet: str) -> str:
        """Generate reply content based on original tweet"""
        reply_templates = [
            "Great point! I think {sentiment}",
            "Interesting perspective! {sentiment}",
            "Thanks for sharing this! {sentiment}",
            "This is really insightful. {sentiment}",
            "Love this! {sentiment}",
            "Couldn't agree more! {sentiment}"
        ]
        
        sentiments = [
            "this could have significant implications.",
            "there's so much potential here.",
            "the future looks promising.",
            "innovation never stops amazing me.",
            "we're living in exciting times.",
            "technology is truly transformative."
        ]
        
        template = random.choice(reply_templates)
        sentiment = random.choice(sentiments)
        
        return template.format(sentiment=sentiment)
    
    def autonomous_tweet(self) -> bool:
        """Post an autonomous tweet"""
        if not self._should_perform_action('tweet'):
            logger.debug("Tweet action rate limited")
            return False
        
        try:
            # Generate content
            tweet_content = self.generate_tweet_content()
            
            # Post tweet
            success = self.scraper.post_tweet(tweet_content)
            
            if success:
                self.last_actions['tweet'] = datetime.now()
                self._log_activity('tweet', {
                    'content': tweet_content,
                    'success': True
                })
                logger.info(f"Posted autonomous tweet: {tweet_content[:50]}...")
                return True
            else:
                self._log_activity('tweet', {
                    'content': tweet_content,
                    'success': False
                })
                return False
                
        except Exception as e:
            logger.error(f"Failed to post autonomous tweet: {e}")
            return False
    
    def search_and_engage(self) -> bool:
        """Search for tweets and engage with them"""
        if not self._should_perform_action('search'):
            logger.debug("Search action rate limited")
            return False
        
        try:
            # Pick random keyword to search
            keyword = random.choice(self.config.SEARCH_KEYWORDS)
            
            # Search for tweets
            tweets = self.scraper.search_tweets(keyword, max_results=5)
            
            if not tweets:
                logger.info(f"No tweets found for keyword: {keyword}")
                return False
            
            self.last_actions['search'] = datetime.now()
            
            # Engage with tweets
            engagement_count = 0
            for tweet in tweets:
                try:
                    # Random engagement decision
                    action = random.choice(['like', 'retweet', 'reply', 'skip'])
                    
                    if action == 'like':
                        if self.scraper.like_tweet(tweet['url']):
                            engagement_count += 1
                            self._log_activity('like', {
                                'tweet_url': tweet['url'],
                                'tweet_text': tweet['text'][:100],
                                'success': True
                            })
                    
                    elif action == 'retweet' and self._should_perform_action('retweet'):
                        if self.scraper.retweet(tweet['url']):
                            engagement_count += 1
                            self.last_actions['retweet'] = datetime.now()
                            self._log_activity('retweet', {
                                'tweet_url': tweet['url'],
                                'tweet_text': tweet['text'][:100],
                                'success': True
                            })
                    
                    elif action == 'reply' and self._should_perform_action('reply'):
                        reply_content = self.generate_reply_content(tweet['text'])
                        if self.scraper.reply_to_tweet(tweet['url'], reply_content):
                            engagement_count += 1
                            self.last_actions['reply'] = datetime.now()
                            self._log_activity('reply', {
                                'tweet_url': tweet['url'],
                                'reply_content': reply_content,
                                'original_text': tweet['text'][:100],
                                'success': True
                            })
                    
                    # Random delay between actions
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Failed to engage with tweet: {e}")
                    continue
            
            logger.info(f"Engaged with {engagement_count} tweets for keyword: {keyword}")
            return engagement_count > 0
            
        except Exception as e:
            logger.error(f"Failed to search and engage: {e}")
            return False
    
    def follow_trending_users(self) -> bool:
        """Follow users from trending topics"""
        try:
            trending_topics = self.scraper.get_trending_topics()
            
            if not trending_topics:
                logger.info("No trending topics found")
                return False
            
            # Pick a random trending topic and search for tweets
            topic = random.choice(trending_topics)
            tweets = self.scraper.search_tweets(topic['name'], max_results=3)
            
            follow_count = 0
            for tweet in tweets:
                try:
                    # Random chance to follow (10% chance)
                    if random.random() < 0.1:
                        username = tweet['username']
                        if self.scraper.follow_user(username):
                            follow_count += 1
                            self._log_activity('follow', {
                                'username': username,
                                'reason': f"trending_topic:{topic['name']}",
                                'success': True
                            })
                        
                        # Limit follows to prevent spam
                        if follow_count >= 2:
                            break
                            
                except Exception as e:
                    logger.error(f"Failed to follow user: {e}")
                    continue
            
            logger.info(f"Followed {follow_count} users from trending topics")
            return follow_count > 0
            
        except Exception as e:
            logger.error(f"Failed to follow trending users: {e}")
            return False
    
    def run_autonomous_cycle(self):
        """Run one cycle of autonomous operations"""
        logger.info("Starting autonomous cycle")
        
        try:
            # Random actions with weighted probabilities
            actions = [
                ('search_engage', 0.4),  # 40% chance
                ('tweet', 0.3),          # 30% chance
                ('follow_trending', 0.1), # 10% chance
                ('rest', 0.2)            # 20% chance - do nothing
            ]
            
            # Choose action based on weights
            rand = random.random()
            cumulative = 0
            chosen_action = 'rest'
            
            for action, probability in actions:
                cumulative += probability
                if rand <= cumulative:
                    chosen_action = action
                    break
            
            # Execute chosen action
            if chosen_action == 'search_engage':
                self.search_and_engage()
            elif chosen_action == 'tweet':
                self.autonomous_tweet()
            elif chosen_action == 'follow_trending':
                self.follow_trending_users()
            else:
                logger.info("Resting this cycle")
            
            # Random delay before next cycle
            delay = random.uniform(300, 900)  # 5-15 minutes
            logger.info(f"Next cycle in {delay/60:.1f} minutes")
            time.sleep(delay)
            
        except Exception as e:
            logger.error(f"Error in autonomous cycle: {e}")
    
    def start_autonomous_mode(self):
        """Start autonomous mode with scheduled operations"""
        if not self.initialize():
            logger.error("Failed to initialize bot")
            return
        
        logger.info("Starting autonomous mode")
        
        # Schedule periodic activities
        schedule.every(30).to(90).minutes.do(self.search_and_engage)
        schedule.every(1).to(3).hours.do(self.autonomous_tweet)
        schedule.every(6).hours.do(self.follow_trending_users)
        
        try:
            while True:
                # Run scheduled tasks
                schedule.run_pending()
                
                # Run autonomous cycle
                self.run_autonomous_cycle()
                
        except KeyboardInterrupt:
            logger.info("Stopping autonomous mode")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.scraper:
            self.scraper.close()
        logger.info("Bot cleanup completed")
    
    def get_activity_stats(self) -> Dict:
        """Get activity statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_activities = [
            log for log in self.activity_log 
            if datetime.fromisoformat(log['timestamp']) > last_24h
        ]
        
        stats = {
            'total_activities_24h': len(recent_activities),
            'tweets_24h': len([a for a in recent_activities if a['action'] == 'tweet']),
            'replies_24h': len([a for a in recent_activities if a['action'] == 'reply']),
            'retweets_24h': len([a for a in recent_activities if a['action'] == 'retweet']),
            'likes_24h': len([a for a in recent_activities if a['action'] == 'like']),
            'follows_24h': len([a for a in recent_activities if a['action'] == 'follow']),
            'last_activity': self.activity_log[-1]['timestamp'] if self.activity_log else 'None'
        }
        
        return stats

if __name__ == "__main__":
    bot = TwitterBot()
    
    # You can run different modes:
    # bot.start_autonomous_mode()  # Full autonomous mode
    
    # Or test individual functions:
    if bot.initialize():
        print("Bot initialized successfully!")
        print("Activity Stats:", bot.get_activity_stats())
        
        # Example: Post a single tweet
        # bot.autonomous_tweet()
        
        # Example: Search and engage
        # bot.search_and_engage()
        
        bot.cleanup() 