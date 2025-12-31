import tweepy
import time
import random
from typing import List, Dict, Optional, Any
from config import Config, logger
from datetime import datetime, timedelta
import json

class TwitterAPI:
    """Twitter API client using tweepy"""
    
    def __init__(self):
        self.config = Config()
        self.client = None
        self.api = None
        self.rate_limits = {
            'tweets': {'count': 0, 'reset_time': datetime.now() + timedelta(hours=1)},
            'replies': {'count': 0, 'reset_time': datetime.now() + timedelta(hours=1)},
            'retweets': {'count': 0, 'reset_time': datetime.now() + timedelta(hours=1)}
        }
        self._initialize_api()
    
    def _initialize_api(self):
        """Initialize Twitter API client"""
        try:
            # Initialize API v2 client
            self.client = tweepy.Client(
                bearer_token=self.config.TWITTER_BEARER_TOKEN,
                consumer_key=self.config.TWITTER_API_KEY,
                consumer_secret=self.config.TWITTER_API_SECRET,
                access_token=self.config.TWITTER_ACCESS_TOKEN,
                access_token_secret=self.config.TWITTER_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )
            
            # Initialize API v1.1 for some features
            auth = tweepy.OAuth1UserHandler(
                self.config.TWITTER_API_KEY,
                self.config.TWITTER_API_SECRET,
                self.config.TWITTER_ACCESS_TOKEN,
                self.config.TWITTER_ACCESS_TOKEN_SECRET
            )
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Test authentication
            self.client.get_me()
            logger.info("Twitter API initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twitter API: {e}")
            raise
    
    def _check_rate_limit(self, action_type: str) -> bool:
        """Check if action is within rate limits"""
        now = datetime.now()
        rate_limit = self.rate_limits[action_type]
        
        # Reset counter if window has passed
        if now > rate_limit['reset_time']:
            rate_limit['count'] = 0
            rate_limit['reset_time'] = now + timedelta(hours=1)
        
        # Check limits
        max_limits = {
            'tweets': self.config.MAX_TWEETS_PER_HOUR,
            'replies': self.config.MAX_REPLIES_PER_HOUR,
            'retweets': self.config.MAX_RETWEETS_PER_HOUR
        }
        
        return rate_limit['count'] < max_limits[action_type]
    
    def _increment_rate_limit(self, action_type: str):
        """Increment rate limit counter"""
        self.rate_limits[action_type]['count'] += 1
    
    def post_tweet(self, text: str, media_paths: Optional[List[str]] = None) -> Optional[Dict]:
        """Post a tweet"""
        if not self._check_rate_limit('tweets'):
            logger.warning("Tweet rate limit exceeded")
            return None
        
        try:
            media_ids = []
            if media_paths:
                for media_path in media_paths:
                    media = self.api.media_upload(media_path)
                    media_ids.append(media.media_id)
            
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids if media_ids else None
            )
            
            self._increment_rate_limit('tweets')
            logger.info(f"Tweet posted successfully: {text[:50]}...")
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return None
    
    def reply_to_tweet(self, tweet_id: str, reply_text: str) -> Optional[Dict]:
        """Reply to a specific tweet"""
        if not self._check_rate_limit('replies'):
            logger.warning("Reply rate limit exceeded")
            return None
        
        try:
            response = self.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=tweet_id
            )
            
            self._increment_rate_limit('replies')
            logger.info(f"Reply posted to tweet {tweet_id}: {reply_text[:50]}...")
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to reply to tweet {tweet_id}: {e}")
            return None
    
    def retweet(self, tweet_id: str) -> bool:
        """Retweet a specific tweet"""
        if not self._check_rate_limit('retweets'):
            logger.warning("Retweet rate limit exceeded")
            return False
        
        try:
            self.client.retweet(tweet_id)
            self._increment_rate_limit('retweets')
            logger.info(f"Retweeted tweet {tweet_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to retweet {tweet_id}: {e}")
            return False
    
    def like_tweet(self, tweet_id: str) -> bool:
        """Like a specific tweet"""
        try:
            self.client.like(tweet_id)
            logger.info(f"Liked tweet {tweet_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to like tweet {tweet_id}: {e}")
            return False
    
    def search_tweets(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for tweets based on query"""
        try:
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=min(max_results, 100),
                tweet_fields=['author_id', 'created_at', 'public_metrics', 'context_annotations']
            ).flatten(limit=max_results)
            
            results = []
            for tweet in tweets:
                results.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'author_id': tweet.author_id,
                    'created_at': tweet.created_at,
                    'public_metrics': tweet.public_metrics
                })
            
            logger.info(f"Found {len(results)} tweets for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search tweets: {e}")
            return []
    
    def get_trending_topics(self, woeid: int = 1) -> List[Dict]:
        """Get trending topics (WOEID 1 = worldwide)"""
        try:
            trends = self.api.get_place_trends(woeid)
            trending_topics = []
            
            for trend in trends[0]['trends'][:10]:  # Top 10 trends
                trending_topics.append({
                    'name': trend['name'],
                    'url': trend['url'],
                    'tweet_volume': trend['tweet_volume']
                })
            
            logger.info(f"Retrieved {len(trending_topics)} trending topics")
            return trending_topics
            
        except Exception as e:
            logger.error(f"Failed to get trending topics: {e}")
            return []
    
    def get_user_timeline(self, username: str, count: int = 10) -> List[Dict]:
        """Get user's recent tweets"""
        try:
            user = self.client.get_user(username=username)
            tweets = self.client.get_users_tweets(
                user.data.id,
                max_results=count,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            results = []
            if tweets.data:
                for tweet in tweets.data:
                    results.append({
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'public_metrics': tweet.public_metrics
                    })
            
            logger.info(f"Retrieved {len(results)} tweets from @{username}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get timeline for @{username}: {e}")
            return []
    
    def get_mentions(self, count: int = 10) -> List[Dict]:
        """Get mentions of the authenticated user"""
        try:
            mentions = self.client.get_users_mentions(
                self.client.get_me().data.id,
                max_results=count,
                tweet_fields=['author_id', 'created_at', 'public_metrics']
            )
            
            results = []
            if mentions.data:
                for mention in mentions.data:
                    results.append({
                        'id': mention.id,
                        'text': mention.text,
                        'author_id': mention.author_id,
                        'created_at': mention.created_at,
                        'public_metrics': mention.public_metrics
                    })
            
            logger.info(f"Retrieved {len(results)} mentions")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get mentions: {e}")
            return []
    
    def follow_user(self, username: str) -> bool:
        """Follow a user"""
        try:
            user = self.client.get_user(username=username)
            self.client.follow_user(user.data.id)
            logger.info(f"Followed @{username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to follow @{username}: {e}")
            return False
    
    def unfollow_user(self, username: str) -> bool:
        """Unfollow a user"""
        try:
            user = self.client.get_user(username=username)
            self.client.unfollow_user(user.data.id)
            logger.info(f"Unfollowed @{username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unfollow @{username}: {e}")
            return False 