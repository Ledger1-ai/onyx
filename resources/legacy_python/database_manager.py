#!/usr/bin/env python3
"""
Database Manager for Intelligent Twitter Agent
==============================================
Handles MongoDB operations for scheduling, performance tracking, and analytics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from urllib.parse import quote_plus
import json
from uuid import uuid4

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import PyMongoError, DuplicateKeyError
except ImportError:
    logging.warning("PyMongo not installed. Install with: pip install pymongo")
    MongoClient = None

from data_models import (
    ScheduleSlot, DailySchedule, TweetPerformance, EngagementSession,
    PerformanceAnalysis, TrendAnalysis, StrategyTemplate, OptimizationRule,
    ActivityType, PerformanceMetric, SlotStatus, convert_to_dict,
    ActivityType, PerformanceMetric, SlotStatus, convert_to_dict,
    create_default_strategy, AccountAnalytics, User, PlatformCredentials,
    SystemIdentity, CompanyConfig, PersonalityConfig
)

logger = logging.getLogger(__name__)

def generate_slot_id() -> str:
    """Generate a unique slot ID"""
    return f"slot_{uuid4().hex[:12]}"

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return f"session_{uuid4().hex[:12]}"

class DatabaseManager:
    """Manage MongoDB operations for the intelligent agent"""
    
    def __init__(self, connection_string: Optional[str] = None, database_name: str = "intelligent_agent"):
        """Initialize database manager"""
        # Lazy import to avoid circular dependencies if any
        from config import Config
        self.connection_string = connection_string or Config.MONGODB_URI
        self.database_name = database_name
        self.client = None
        self.db = None
        
        # Initialize connection
        self._connect()
        
        # Initialize collections and indexes
        self._setup_collections()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            if MongoClient is None:
                raise ImportError("PyMongo is required for database operations")
            
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {self.database_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _setup_collections(self):
        """Set up collections and create indexes"""
        try:
            # Create indexes for performance
            collections_indexes = {
                "daily_schedules": [
                    ("date", ASCENDING),
                    ("strategy_focus", ASCENDING),
                    ("created_at", DESCENDING)
                ],
                "schedule_slots": [
                    ("slot_id", ASCENDING),
                    ("start_time", ASCENDING),
                    ("activity_type", ASCENDING),
                    ("status", ASCENDING),
                    ("priority", DESCENDING)
                ],
                "tweet_performance": [
                    ("tweet_id", ASCENDING),
                    ("timestamp", DESCENDING),
                    ("posting_time", ASCENDING),
                    ("content_type", ASCENDING)
                ],
                "engagement_sessions": [
                    ("session_id", ASCENDING),
                    ("start_time", DESCENDING),
                    ("activity_type", ASCENDING)
                ],
                "performance_analysis": [
                    ("date", ASCENDING),
                    ("analysis_timestamp", DESCENDING)
                ],
                "strategy_templates": [
                    ("strategy_name", ASCENDING),
                    ("is_active", ASCENDING)
                ],
                "optimization_rules": [
                    ("rule_id", ASCENDING),
                    ("is_active", ASCENDING),
                    ("priority", DESCENDING)
                ],
                "account_analytics": [
                    ("date", ASCENDING),
                    ("time_range", ASCENDING)
                ],
                "follower_shoutouts": [
                    ("username", ASCENDING),
                    ("timestamp", DESCENDING),
                    ("created_by", ASCENDING)
                ],
                "tweet_replies": [
                    ("tweet_url", ASCENDING),
                    ("timestamp", DESCENDING),
                    ("replied_by", ASCENDING)
                ],
                "users": [
                    ("email", ASCENDING),
                    ("user_id", ASCENDING)
                ],
                "system_identities": [
                    ("user_id", ASCENDING)
                ]
            }
            
            for collection_name, indexes in collections_indexes.items():
                collection = self.db[collection_name]
                
                for index_spec in indexes:
                    try:
                        collection.create_index([index_spec])
                    except Exception as e:
                        logger.warning(f"Could not create index {index_spec} on {collection_name}: {e}")
            
            logger.info("Database collections and indexes set up successfully")
            
        except Exception as e:
            logger.error(f"Error setting up collections: {e}")

    # save reply management as a dictionary with multiple replies per username and tweet_url and it shouldn't replace the existing record
    def save_reply_management(self, username: str, tweet_url: str = None, created_by: str = "intelligent_agent") -> bool:
        """Save a reply management record"""
        try:
            reply_record = {
                "tweet_url": tweet_url,
                "created_by": created_by
            }
            
            # Insert a new record as an array under the username
            self.db.reply_management.update_one(
                {"username": username.lower()},
                {"$push": {"replies": reply_record}},
                upsert=True
            )
            
            logger.info(f"Saved reply management record for @{username}")
            return True
        except Exception as e:
            logger.error(f"Error saving reply management: {e}")
            return False
        
    def save_tweet_reply(self, tweet_url: str, reply_content: str, replied_by: str = "intelligent_agent") -> bool:
        """Save a tweet reply record"""
        try:
            reply_record = {
                "tweet_url": tweet_url,
                "reply_content": reply_content,
                "timestamp": datetime.now(),
                "replied_by": replied_by
            }
            
            self.db.tweet_replies.insert_one(reply_record)
            logger.info(f"Saved tweet reply record for: {tweet_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving tweet reply: {e}")
            return False

    def has_replied_to_tweet(self, tweet_url: str) -> bool:
        """Check if we've already replied to this specific tweet"""
        try:
            result = self.db.tweet_replies.find_one({"tweet_url": tweet_url})
            return result is not None
        except Exception as e:
            logger.error(f"Error checking tweet reply: {e}")
            return False
        
    def save_follower_shoutout(self, username: str, tweet_url: str = None, created_by: str = "intelligent_agent") -> bool:
        """Save a follower shoutout record"""
        try:
            shoutout_record = {
                "username": username.lower(),
                "original_username": username,
                "timestamp": datetime.now(),
                "tweet_url": tweet_url,
                "created_by": created_by
            }
            
            # Use upsert to avoid duplicates
            self.db.follower_shoutouts.replace_one(
                {"username": username.lower()},
                shoutout_record,
                upsert=True
            )
            
            logger.info(f"Saved follower shoutout record for @{username}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving follower shoutout: {e}")
            return False
        
    # has reply been managed with tweet_url, replies are now an array under the username
    def has_reply_been_managed(self, username: str, tweet_url: str) -> bool:
        """Check if a reply has already been managed"""
        try:
            # Navigate to the username entry in the reply_management collection 
            result = self.db.reply_management.find_one({
                "username": username.lower()
            })
            # Check if the tweet_url is in the replies array
            if result and "replies" in result:
                for reply in result["replies"]:
                    if reply["tweet_url"] == tweet_url:
                        return True
            return False
        except Exception as e:
            logger.error(f"Error checking reply management: {e}")
            return False    
    
    def has_follower_shoutout(self, username: str) -> bool:
        """Check if a follower has already been shouted out"""
        try:
            result = self.db.follower_shoutouts.find_one({
                "username": username.lower()
            })
            return result is not None
        except Exception as e:
            logger.error(f"Error checking follower shoutout: {e}")
            return False
    
    def get_follower_shoutouts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent follower shoutouts"""
        try:
            results = list(self.db.follower_shoutouts.find(
                {},
                {"_id": 0}
            ).sort("timestamp", DESCENDING).limit(limit))
            
            return results
        except Exception as e:
            logger.error(f"Error getting follower shoutouts: {e}")
            return []
    
    def get_follower_shoutout_stats(self) -> Dict[str, Any]:
        """Get statistics about follower shoutouts"""
        try:
            total_shoutouts = self.db.follower_shoutouts.count_documents({})
            
            # Get shoutouts from last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            recent_shoutouts = self.db.follower_shoutouts.count_documents({
                "timestamp": {"$gte": week_ago}
            })
            
            # Get shoutouts from today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_shoutouts = self.db.follower_shoutouts.count_documents({
                "timestamp": {"$gte": today_start}
            })
            
            return {
                "total_shoutouts": total_shoutouts,
                "last_7_days": recent_shoutouts,
                "today": today_shoutouts
            }
        except Exception as e:
            logger.error(f"Error getting follower shoutout stats: {e}")
            return {}
    
            return {}
        except Exception as e:
            logger.error(f"Error getting follower shoutout stats: {e}")
            return {}

    # User Management Methods
    def save_user(self, user: User) -> bool:
        """Save a user record"""
        try:
            user_dict = convert_to_dict(user)
            # Ensure email is unique (though index handles this, good to have explicit check logic if needed)
            
            self.db.users.replace_one(
                {"user_id": user.user_id},
                user_dict,
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            doc = self.db.users.find_one({"user_id": user_id})
            if doc:
                # Parse credentials if available
                credentials_data = doc.get("credentials", {})
                credentials = {}
                for platform, cred_dict in credentials_data.items():
                    if isinstance(cred_dict, dict):
                         credentials[platform] = PlatformCredentials(
                             access_token=cred_dict.get("access_token"),
                             refresh_token=cred_dict.get("refresh_token"),
                             expires_at=datetime.fromisoformat(cred_dict["expires_at"]) if cred_dict.get("expires_at") else None,
                             platform_user_id=cred_dict.get("platform_user_id"),
                             session_cookies=cred_dict.get("session_cookies"),
                             is_active=cred_dict.get("is_active", True)
                         )

                return User(
                    user_id=doc["user_id"],
                    email=doc["email"],
                    name=doc.get("name", ""),
                    created_at=datetime.fromisoformat(doc["created_at"]) if isinstance(doc.get("created_at"), str) else doc.get("created_at"),
                    credentials=credentials,
                    tokens=doc.get("tokens", {}),
                    preferences=doc.get("preferences", {})
                )
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by Email"""
        try:
            doc = self.db.users.find_one({"email": email})
            if doc:
                # Parse credentials if available
                credentials_data = doc.get("credentials", {})
                credentials = {}
                for platform, cred_dict in credentials_data.items():
                    if isinstance(cred_dict, dict):
                         credentials[platform] = PlatformCredentials(
                             access_token=cred_dict.get("access_token"),
                             refresh_token=cred_dict.get("refresh_token"),
                             expires_at=datetime.fromisoformat(cred_dict["expires_at"]) if cred_dict.get("expires_at") else None,
                             platform_user_id=cred_dict.get("platform_user_id"),
                             session_cookies=cred_dict.get("session_cookies"),
                             is_active=cred_dict.get("is_active", True)
                         )

                return User(
                    user_id=doc["user_id"],
                    email=doc["email"],
                    name=doc.get("name", ""),
                    created_at=datetime.fromisoformat(doc["created_at"]) if isinstance(doc.get("created_at"), str) else doc.get("created_at"),
                    credentials=credentials,
                    tokens=doc.get("tokens", {}),
                    preferences=doc.get("preferences", {})
                )
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    # Schedule Management Methods
    def save_daily_schedule(self, schedule: DailySchedule) -> bool:
        """Save a daily schedule to the database"""
        try:
            schedule_dict = convert_to_dict(schedule)
            
            # Use upsert to replace existing schedule for the date
            result = self.db.daily_schedules.replace_one(
                {"date": schedule.date},
                schedule_dict,
                upsert=True
            )
            
            logger.info(f"Saved daily schedule for {schedule.date}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving daily schedule: {e}")
            return False
    
    def get_daily_schedule(self, date: str) -> Optional[DailySchedule]:
        """Get daily schedule for a specific date"""
        try:
            doc = self.db.daily_schedules.find_one({"date": date})
            
            if doc:
                # Convert back to DailySchedule object
                # Note: This is a simplified conversion - in production you'd want proper deserialization
                return DailySchedule(
                    date=doc["date"],
                    slots=[],  # Slots are loaded separately
                    strategy_focus=doc.get("strategy_focus", ""),
                    daily_goals=doc.get("daily_goals", {}),
                    performance_targets=doc.get("performance_targets", {}),
                    completion_rate=doc.get("completion_rate", 0.0),
                    total_activities=doc.get("total_activities", 0)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting daily schedule: {e}")
            return None
    
    def save_schedule_slot(self, slot: ScheduleSlot) -> bool:
        """Save a schedule slot to the database"""
        try:
            slot_dict = convert_to_dict(slot)
            
            # Add date field for easier querying
            slot_dict["date"] = slot.start_time.strftime("%Y-%m-%d")
            
            result = self.db.schedule_slots.replace_one(
                {"slot_id": slot.slot_id},
                slot_dict,
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving schedule slot: {e}")
            return False
    
    def get_schedule_slots(self, date: str, status: Optional[str] = None) -> List[ScheduleSlot]:
        """Get schedule slots for a specific date"""
        try:
            query = {"date": date}
            if status:
                query["status"] = status
            
            docs = list(self.db.schedule_slots.find(query).sort("start_time", ASCENDING))
            
            slots = []
            for doc in docs:
                try:
                    # Convert back to ScheduleSlot object
                    slot = ScheduleSlot(
                        slot_id=doc["slot_id"],
                        start_time=datetime.fromisoformat(doc["start_time"]),
                        end_time=datetime.fromisoformat(doc["end_time"]),
                        activity_type=ActivityType(doc["activity_type"]),
                        activity_config=doc.get("activity_config", {}),
                        priority=doc.get("priority", 1),
                        is_flexible=doc.get("is_flexible", True),
                        status=SlotStatus(doc["status"]) if "status" in doc else SlotStatus.SCHEDULED,
                        performance_data=doc.get("performance_data")
                    )
                    slots.append(slot)
                except Exception as e:
                    logger.warning(f"Error converting slot document: {e}")
                    continue
            
            return slots
            
        except Exception as e:
            logger.error(f"Error getting schedule slots: {e}")
            return []
    
    def update_slot_status(self, slot_id: str, status: str, performance_data: Optional[Dict] = None) -> bool:
        """Update the status of a schedule slot"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            if performance_data:
                update_data["performance_data"] = performance_data
            
            result = self.db.schedule_slots.update_one(
                {"slot_id": slot_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating slot status: {e}")
            return False

    # System Identity Management
    def save_system_identity(self, identity: SystemIdentity) -> bool:
        """Save a system identity configuration"""
        try:
            identity_dict = convert_to_dict(identity)
            identity_dict["updated_at"] = datetime.now().isoformat()
            
            self.db.system_identities.replace_one(
                {"user_id": identity.user_id},
                identity_dict,
                upsert=True
            )
            logger.info(f"Saved system identity for user {identity.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving system identity: {e}")
            return False

    def get_system_identity(self, user_id: str) -> Optional[SystemIdentity]:
        """Get system identity by user_id"""
        try:
            doc = self.db.system_identities.find_one({"user_id": user_id})
            if doc:
                comp_data = doc.get("company_config", {})
                pers_data = doc.get("personality_config", {})
                
                company = CompanyConfig(
                    name=comp_data.get("name", ""),
                    industry=comp_data.get("industry", ""),
                    mission=comp_data.get("mission", ""),
                    brand_colors=comp_data.get("brand_colors", {}),
                    twitter_username=comp_data.get("twitter_username", ""),
                    company_logo_path=comp_data.get("company_logo_path", ""),
                    values=comp_data.get("values", []),
                    focus_areas=comp_data.get("focus_areas", []),
                    brand_voice=comp_data.get("brand_voice", ""),
                    target_audience=comp_data.get("target_audience", ""),
                    key_products=comp_data.get("key_products", []),
                    competitive_advantages=comp_data.get("competitive_advantages", []),
                    location=comp_data.get("location", ""),
                    contact_info=comp_data.get("contact_info", {}),
                    business_model=comp_data.get("business_model", ""),
                    core_philosophy=comp_data.get("core_philosophy", ""),
                    subsidiaries=comp_data.get("subsidiaries", []),
                    partner_categories=comp_data.get("partner_categories", [])
                )
                
                personality = PersonalityConfig(
                    tone=pers_data.get("tone", ""),
                    engagement_style=pers_data.get("engagement_style", ""),
                    communication_style=pers_data.get("communication_style", ""),
                    hashtag_strategy=pers_data.get("hashtag_strategy", ""),
                    content_themes=pers_data.get("content_themes", []),
                    posting_frequency=pers_data.get("posting_frequency", "")
                )
                
                return SystemIdentity(
                    user_id=doc["user_id"],
                    company_logo_path=doc.get("company_logo_path", ""),
                    company_config=company,
                    personality_config=personality,
                    created_at=datetime.fromisoformat(doc["created_at"]) if isinstance(doc.get("created_at"), str) else doc.get("created_at"),
                    updated_at=datetime.fromisoformat(doc["updated_at"]) if isinstance(doc.get("updated_at"), str) else doc.get("updated_at")
                )
            return None
        except Exception as e:
            logger.error(f"Error getting system identity: {e}")
            return None

    def delete_schedule_slot(self, slot_id: str) -> bool:
        """Delete a schedule slot"""
        try:
            result = self.db.schedule_slots.delete_one({"slot_id": slot_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting schedule slot: {e}")
            return False

    def delete_daily_schedule(self, date: str) -> bool:
        """Delete a daily schedule"""
        try:
            result = self.db.daily_schedules.delete_one({"date": date})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting daily schedule: {e}")
            return False

    def update_slot_activity_type(self, slot_id: str, new_activity_type: ActivityType, new_config: Optional[Dict] = None) -> bool:
        """Update the activity type of a schedule slot"""
        try:
            update_data = {
                "activity_type": new_activity_type.value,
                "updated_at": datetime.now().isoformat()
            }
            
            if new_config:
                update_data["activity_config"] = new_config
            
            result = self.db.schedule_slots.update_one(
                {"slot_id": slot_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating slot activity type: {e}")
            return False

    def update_schedule_slot(self, slot_id: str, updates: Dict[str, Any]) -> bool:
        """Update a schedule slot with arbitrary fields"""
        try:
            # Prepare update data
            update_data = updates.copy()
            update_data["updated_at"] = datetime.now().isoformat()
            
            # Convert activity_type to enum value if present
            if "activity_type" in update_data and isinstance(update_data["activity_type"], str):
                try:
                    # If it's already a valid ActivityType value, keep it
                    ActivityType(update_data["activity_type"])
                except ValueError:
                    # If not, assume it's a string that needs to be converted
                    logger.warning(f"Invalid activity type: {update_data['activity_type']}")
                    return False
            
            result = self.db.schedule_slots.update_one(
                {"slot_id": slot_id},
                {"$set": update_data}
            )
            
            logger.info(f"Update result for slot {slot_id}: matched={result.matched_count}, modified={result.modified_count}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating schedule slot {slot_id}: {e}", exc_info=True)
            return False
    
    # Performance Tracking Methods
    def save_tweet_performance(self, performance: TweetPerformance) -> bool:
        """Save tweet performance data"""
        try:
            performance_dict = convert_to_dict(performance)
            
            result = self.db.tweet_performance.replace_one(
                {"tweet_id": performance.tweet_id},
                performance_dict,
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving tweet performance: {e}")
            return False
    
    def get_tweet_performances_by_date(self, date: str) -> List[TweetPerformance]:
        """Get tweet performances for a specific date"""
        try:
            # Query for tweets posted on the specified date
            start_date = datetime.strptime(date, "%Y-%m-%d")
            end_date = start_date + timedelta(days=1)
            
            query = {
                "posting_time": {
                    "$gte": start_date.isoformat(),
                    "$lt": end_date.isoformat()
                }
            }
            
            docs = list(self.db.tweet_performance.find(query).sort("posting_time", ASCENDING))
            
            performances = []
            for doc in docs:
                try:
                    # Simplified conversion - you'd want proper deserialization in production
                    performance = TweetPerformance(
                        tweet_id=doc["tweet_id"],
                        metrics=doc.get("metrics", {}),
                        engagement_data=doc.get("engagement_data", {}),  # This should be properly converted
                        timestamp=datetime.fromisoformat(doc["timestamp"]),
                        content_type=doc.get("content_type", "text"),
                        hashtags=doc.get("hashtags", []),
                        mentions=doc.get("mentions", []),
                        posting_time=datetime.fromisoformat(doc["posting_time"]) if doc.get("posting_time") else None,
                        audience_reached=doc.get("audience_reached", 0),
                        sentiment_score=doc.get("sentiment_score", 0.0),
                        virality_score=doc.get("virality_score", 0.0)
                    )
                    performances.append(performance)
                except Exception as e:
                    logger.warning(f"Error converting performance document: {e}")
                    continue
            
            return performances
            
        except Exception as e:
            logger.error(f"Error getting tweet performances: {e}")
            return []
    
    def save_performance_analysis(self, analysis: PerformanceAnalysis) -> bool:
        """Save performance analysis"""
        try:
            analysis_dict = convert_to_dict(analysis)
            
            result = self.db.performance_analysis.replace_one(
                {"date": analysis.date},
                analysis_dict,
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving performance analysis: {e}")
            return False
    
    def get_performance_analysis(self, date: str, platform: Optional[str] = None) -> Optional[PerformanceAnalysis]:
        """Get performance analysis for a specific date and platform"""
        try:
            query = {"date": date}
            if platform:
                query["platform"] = platform
                
            doc = self.db.performance_analysis.find_one(query)
            
            if doc:
                # Simplified conversion
                return PerformanceAnalysis(
                    date=doc["date"],
                    platform=doc.get("platform", "twitter"),
                    metrics=doc.get("metrics", {}),
                    engagement_analysis=doc.get("engagement_analysis", {}),
                    top_performing_content=doc.get("top_performing_content", []),
                    activity_effectiveness=doc.get("activity_effectiveness", {}),
                    insights=doc.get("insights", []),
                    recommendations=doc.get("recommendations", []),
                    analysis_timestamp=datetime.fromisoformat(doc["analysis_timestamp"]),
                    strategy_adjustments=doc.get("strategy_adjustments", []),
                    performance_score=doc.get("performance_score", 0.0)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting performance analysis: {e}")
            return None
    
    def get_performance_metrics(self, date: str) -> Optional[Any]:
        """Get performance metrics for a specific date"""
        return self.get_performance_analysis(date)
    
    # Strategy Management Methods
    def save_strategy_template(self, strategy: StrategyTemplate) -> bool:
        """Save a strategy template"""
        try:
            strategy_dict = convert_to_dict(strategy)
            
            # MongoDB requires string keys. Convert any Enum keys to their value strings.
            def _enum_key_dict(d: Dict[str, Any]) -> Dict[str, Any]:
                out = {}
                for k, v in d.items():
                    key = k.value if hasattr(k, 'value') else str(k)
                    out[key] = v
                return out

            if isinstance(strategy_dict.get("activity_distribution"), dict):
                strategy_dict["activity_distribution"] = _enum_key_dict(strategy_dict["activity_distribution"])
            if isinstance(strategy_dict.get("target_metrics"), dict):
                strategy_dict["target_metrics"] = _enum_key_dict(strategy_dict["target_metrics"])
            
            result = self.db.strategy_templates.replace_one(
                {"strategy_name": strategy.strategy_name},
                strategy_dict,
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving strategy template: {e}")
            return False
    
    def get_strategy_template(self, strategy_name: str) -> Optional[StrategyTemplate]:
        """Get a strategy template by name"""
        try:
            doc = self.db.strategy_templates.find_one({"strategy_name": strategy_name})
            
            if doc:
                # Simplified conversion - proper deserialization needed for production
                return StrategyTemplate(
                    strategy_name=doc["strategy_name"],
                    description=doc.get("description", ""),
                    activity_distribution={ActivityType(k): v for k, v in doc.get("activity_distribution", {}).items()},
                    optimal_posting_times=doc.get("optimal_posting_times", []),
                    content_mix=doc.get("content_mix", {}),
                    target_metrics={PerformanceMetric(k): v for k, v in doc.get("target_metrics", {}).items()},
                    primary_goals=doc.get("primary_goals", []),
                    engagement_strategy=doc.get("engagement_strategy", {}),
                    hashtag_strategy=doc.get("hashtag_strategy", []),
                    tone_guidelines=doc.get("tone_guidelines", {}),
                    is_active=doc.get("is_active", True)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting strategy template: {e}")
            return None
    
    def get_all_strategy_templates(self) -> List[StrategyTemplate]:
        """Get all strategy templates"""
        try:
            docs = list(self.db.strategy_templates.find({"is_active": True}))
            
            strategies = []
            for doc in docs:
                try:
                    strategy = StrategyTemplate(
                        strategy_name=doc["strategy_name"],
                        description=doc.get("description", ""),
                        activity_distribution={ActivityType(k): v for k, v in doc.get("activity_distribution", {}).items()},
                        optimal_posting_times=doc.get("optimal_posting_times", []),
                        content_mix=doc.get("content_mix", {}),
                        target_metrics={PerformanceMetric(k): v for k, v in doc.get("target_metrics", {}).items()},
                        primary_goals=doc.get("primary_goals", []),
                        engagement_strategy=doc.get("engagement_strategy", {}),
                        hashtag_strategy=doc.get("hashtag_strategy", []),
                        tone_guidelines=doc.get("tone_guidelines", {}),
                        is_active=doc.get("is_active", True)
                    )
                    strategies.append(strategy)
                except Exception as e:
                    logger.warning(f"Error converting strategy document: {e}")
                    continue
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting strategy templates: {e}")
            return []
    
    # Optimization Rules Methods
    def save_optimization_rule(self, rule: OptimizationRule) -> bool:
        """Save an optimization rule"""
        try:
            rule_dict = convert_to_dict(rule)
            
            result = self.db.optimization_rules.replace_one(
                {"rule_id": rule.rule_id},
                rule_dict,
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving optimization rule: {e}")
            return False
    
    def get_active_optimization_rules(self) -> List[OptimizationRule]:
        """Get all active optimization rules"""
        try:
            docs = list(self.db.optimization_rules.find(
                {"is_active": True}
            ).sort("priority", DESCENDING))
            
            rules = []
            for doc in docs:
                try:
                    rule = OptimizationRule(
                        rule_id=doc["rule_id"],
                        name=doc["name"],
                        description=doc.get("description", ""),
                        condition=doc.get("condition", ""),
                        action=doc.get("action", ""),
                        parameters=doc.get("parameters", {}),
                        is_active=doc.get("is_active", True),
                        priority=doc.get("priority", 1),
                        success_count=doc.get("success_count", 0),
                        failure_count=doc.get("failure_count", 0),
                        last_applied=datetime.fromisoformat(doc["last_applied"]) if doc.get("last_applied") else None
                    )
                    rules.append(rule)
                except Exception as e:
                    logger.warning(f"Error converting rule document: {e}")
                    continue
            
            return rules
            
        except Exception as e:
            logger.error(f"Error getting optimization rules: {e}")
            return []
    
    # Engagement Session Methods
    def save_engagement_session(self, session: EngagementSession) -> bool:
        """Save an engagement session"""
        try:
            session_dict = convert_to_dict(session)
            
            result = self.db.engagement_sessions.replace_one(
                {"session_id": session.session_id},
                session_dict,
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving engagement session: {e}")
            return False
    
    def get_recent_engagement_sessions(self, hours: int = 24) -> List[EngagementSession]:
        """Get recent engagement sessions within specified hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            docs = list(self.db.engagement_sessions.find(
                {"start_time": {"$gte": cutoff_time.isoformat()}}
            ).sort("start_time", DESCENDING))
            
            sessions = []
            for doc in docs:
                try:
                    session = EngagementSession(
                        session_id=doc["session_id"],
                        start_time=datetime.fromisoformat(doc["start_time"]),
                        end_time=datetime.fromisoformat(doc["end_time"]) if doc.get("end_time") else None,
                        activity_type=ActivityType(doc["activity_type"]),
                        accounts_engaged=doc.get("accounts_engaged", []),
                        interactions_made=doc.get("interactions_made", {}),
                        topics_engaged=doc.get("topics_engaged", []),
                        engagement_quality_score=doc.get("engagement_quality_score", 0.0),
                        session_notes=doc.get("session_notes", "")
                    )
                    sessions.append(session)
                except Exception as e:
                    logger.warning(f"Error converting session document: {e}")
                    continue
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting engagement sessions: {e}")
            return []
    
    # Data Analysis Methods
    def get_metrics_trend(self, metric_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get trend data for a specific metric over time"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "date": {
                            "$gte": start_date.strftime("%Y-%m-%d"),
                            "$lte": end_date.strftime("%Y-%m-%d")
                        }
                    }
                },
                {
                    "$project": {
                        "date": 1,
                        "metric_value": f"$metrics.{metric_name}"
                    }
                },
                {
                    "$sort": {"date": 1}
                }
            ]
            
            results = list(self.db.performance_analysis.aggregate(pipeline))
            return results
            
        except Exception as e:
            logger.error(f"Error getting metrics trend: {e}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to maintain database performance"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")
            
            # Clean up old schedule slots
            result1 = self.db.schedule_slots.delete_many({"date": {"$lt": cutoff_str}})
            
            # Clean up old performance analyses
            result2 = self.db.performance_analysis.delete_many({"date": {"$lt": cutoff_str}})
            
            # Clean up old engagement sessions
            result3 = self.db.engagement_sessions.delete_many(
                {"start_time": {"$lt": cutoff_date.isoformat()}}
            )
            
            logger.info(f"Cleaned up old data: {result1.deleted_count + result2.deleted_count + result3.deleted_count} documents removed")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def ensure_default_data(self):
        """Ensure default strategy and optimization rules exist"""
        try:
            # Check if any strategies exist
            strategy_count = self.db.strategy_templates.count_documents({})
            
            if strategy_count == 0:
                # Create default strategy
                default_strategy = create_default_strategy()
                self.save_strategy_template(default_strategy)
                logger.info("Created default strategy template")
            
            # Check if any optimization rules exist
            rule_count = self.db.optimization_rules.count_documents({})
            
            if rule_count == 0:
                # Create default optimization rules
                default_rules = [
                    OptimizationRule(
                        rule_id="low_engagement_boost",
                        name="Low Engagement Boost",
                        description="Increase activity when engagement is low",
                        condition="engagement_rate < 0.02",
                        action="increase_posting_frequency",
                        parameters={"boost_factor": 1.2},
                        priority=3
                    ),
                    OptimizationRule(
                        rule_id="peak_time_optimization",
                        name="Peak Time Optimization",
                        description="Focus on high-performing time slots",
                        condition="best_performing_hours_identified",
                        action="shift_posting_times",
                        parameters={"time_shift_hours": [1, -1, 2, -2]},
                        priority=2
                    )
                ]
                
                for rule in default_rules:
                    self.save_optimization_rule(rule)
                
                logger.info("Created default optimization rules")
            
        except Exception as e:
            logger.error(f"Error ensuring default data: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            
            collections = [
                "daily_schedules", "schedule_slots", "tweet_performance",
                "engagement_sessions", "performance_analysis", "strategy_templates",
                "optimization_rules"
            ]
            
            for collection_name in collections:
                count = self.db[collection_name].count_documents({})
                stats[collection_name] = count
            
            # Get database size
            db_stats = self.db.command("dbStats")
            stats["database_size_mb"] = round(db_stats.get("dataSize", 0) / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    # Account analytics methods
    def save_account_analytics(self, analytics: AccountAnalytics) -> bool:
        """Save account-level analytics (aggregated over a time range like 7D/30D/90D)"""
        try:
            doc = convert_to_dict(analytics)
            self.db.account_analytics.replace_one(
                {"date": analytics.date, "time_range": analytics.time_range},
                doc,
                upsert=True
            )
            logger.info(f"Saved account analytics for {analytics.date} [{analytics.time_range}]")
            return True
        except Exception as e:
            logger.error(f"Error saving account analytics: {e}")
            return False

    def get_account_analytics(self, date: str, time_range: str = "7D") -> Optional[AccountAnalytics]:
        """Get account analytics for a specific date and time range"""
        try:
            doc = self.db.account_analytics.find_one({"date": date, "time_range": time_range})
            if doc:
                return AccountAnalytics(
                    date=doc["date"],
                    time_range=doc.get("time_range", "7D"),
                    verified_followers=doc.get("verified_followers", 0),
                    total_followers=doc.get("total_followers", 0),
                    impressions=doc.get("impressions", 0),
                    engagements=doc.get("engagements", 0),
                    engagement_rate=doc.get("engagement_rate", 0.0),
                    profile_visits=doc.get("profile_visits", 0),
                    replies=doc.get("replies", 0),
                    likes=doc.get("likes", 0),
                    reposts=doc.get("reposts", 0),
                    bookmarks=doc.get("bookmarks", 0),
                    shares=doc.get("shares", 0),
                    follows=doc.get("follows", 0),
                    unfollows=doc.get("unfollows", 0),
                    posts_count=doc.get("posts_count", 0),
                    replies_count=doc.get("replies_count", 0),
                )
            return None
        except Exception as e:
            logger.error(f"Error getting account analytics: {e}")
            return None

    def get_recent_account_analytics(self, time_range: str = "7D", limit: int = 2, platform: Optional[str] = None) -> List[AccountAnalytics]:
        """Get recent account analytics entries for the given time range, sorted by date desc"""
        try:
            query = {"time_range": time_range}
            if platform:
                query["platform"] = platform
            
            docs = list(self.db.account_analytics.find(query).sort("date", DESCENDING).limit(limit))
            records = []
            for doc in docs:
                try:
                    records.append(AccountAnalytics(
                        date=doc["date"],
                        time_range=doc.get("time_range", "7D"),
                        platform=doc.get("platform", "twitter"),
                        verified_followers=doc.get("verified_followers", 0),
                        total_followers=doc.get("total_followers", 0),
                        impressions=doc.get("impressions", 0),
                        engagements=doc.get("engagements", 0),
                        engagement_rate=doc.get("engagement_rate", 0.0),
                        profile_visits=doc.get("profile_visits", 0),
                        likes=doc.get("likes", 0),
                        reposts=doc.get("reposts", 0),
                        bookmarks=doc.get("bookmarks", 0),
                        shares=doc.get("shares", 0),
                        follows=doc.get("follows", 0),
                        unfollows=doc.get("unfollows", 0),
                        posts_count=doc.get("posts_count", 0),
                        replies_count=doc.get("replies_count", 0),
                    ))
                except Exception as e:
                    logger.warning(f"Error converting account analytics document: {e}")
                    continue
            return records
        except Exception as e:
            logger.error(f"Error getting recent account analytics: {e}")
            return []

    # Additional methods for dashboard support
    def get_activities_by_date(self, date) -> List[Dict[str, Any]]:
        """Get activities for a specific date (for dashboard)"""
        try:
            # Convert date to string if it's a date object
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%Y-%m-%d')
            else:
                date_str = str(date)
            
            # Get schedule slots for the date
            slots = self.get_schedule_slots(date_str)
            
            # Convert to dictionary format expected by dashboard
            activities = []
            for slot in slots:
                activities.append({
                    'activity_type': slot.activity_type.value,
                    'start_time': slot.start_time,
                    'end_time': slot.end_time,
                    'status': slot.status.value,
                    'priority': slot.priority
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting activities by date: {e}")
            return []
    
    def get_recent_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent engagement sessions (for dashboard)"""
        try:
            sessions = self.get_recent_engagement_sessions(hours=24)
            
            # Convert to dictionary format and limit results
            session_data = []
            for session in sessions[:limit]:
                session_data.append({
                    'session_id': session.session_id,
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat() if session.end_time else None,
                    'activity_type': session.activity_type.value,
                    'accounts_engaged': len(session.accounts_engaged),
                    'engagement_quality_score': session.engagement_quality_score
                })
            
            return session_data
            
        except Exception as e:
            logger.error(f"Error getting recent sessions: {e}")
            return []
    
    def get_recent_analyses(self, limit: int = 10, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent performance analyses (for dashboard)"""
        try:
            # Get recent analyses from the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            query = {
                "analysis_timestamp": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }
            
            if platform:
                query["platform"] = platform
            
            docs = list(self.db.performance_analysis.find(query)
                       .sort("analysis_timestamp", DESCENDING)
                       .limit(limit))
            
            analyses = []
            for doc in docs:
                analyses.append({
                    'date': doc.get('date'),
                    'platform': doc.get('platform', 'twitter'),
                    'performance_score': doc.get('performance_score', 0),
                    'analysis_timestamp': doc.get('analysis_timestamp'),
                    'insights': doc.get('insights', []),
                    'recommendations': doc.get('recommendations', [])
                })
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error getting recent analyses: {e}")
            return []

    # --- SaaS / Multi-Tenant User Management ---

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a user by ID"""
        try:
            return self.db.users.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def save_credential(self, user_id: str, platform: str, credential_data: Dict[str, Any]):
        """Save or update platform credentials for a user"""
        try:
            # Update specific platform credential in the 'credentials' map
            update_query = {
                "$set": {
                    f"credentials.{platform}": credential_data,
                    "updated_at": datetime.now().isoformat()
                },
                "$setOnInsert": {
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat()
                }
            }
            
            self.db.users.update_one(
                {"user_id": user_id},
                update_query,
                upsert=True
            )
            logger.info(f"Saved {platform} credentials for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving credential for {user_id}: {e}")
            return False

    # --- Strategy Template Management ---

    def get_all_strategy_templates(self) -> List[Any]:
        """Get all strategy templates from database"""
        try:
            from data_models import StrategyTemplate, ActivityType
            
            templates = []
            cursor = self.db.strategy_templates.find({})
            
            for doc in cursor:
                # Convert back to StrategyTemplate object
                activity_dist = {}
                raw_dist = doc.get("activity_distribution", {})
                
                for k, v in raw_dist.items():
                    try:
                        # Try to convert string key to ActivityType enum
                        enum_key = ActivityType(k)
                        activity_dist[enum_key] = v
                    except ValueError:
                        # Keep as string if not a valid enum
                        activity_dist[k] = v
                
                template = StrategyTemplate(
                    strategy_name=doc.get("strategy_name", doc.get("name", "Default Strategy")),
                    description=doc.get("description", ""),
                    activity_distribution=activity_dist,
                    optimal_posting_times=doc.get("optimal_posting_times", []),
                    is_active=doc.get("is_active", True),
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at")
                )
                templates.append(template)
            
            return templates
            
        except Exception as e:
            logger.error(f"Error getting strategy templates: {e}")
            return []

    def save_strategy_template(self, strategy) -> bool:
        """Save or update a strategy template"""
        try:
            from data_models import convert_to_dict
            
            # Convert activity_distribution enum keys to strings
            dist = {}
            if strategy.activity_distribution:
                for k, v in strategy.activity_distribution.items():
                    key_str = k.value if hasattr(k, 'value') else str(k)
                    dist[key_str] = v
            
            doc = {
                "strategy_name": strategy.strategy_name,
                "description": strategy.description,
                "activity_distribution": dist,
                "optimal_posting_times": strategy.optimal_posting_times,
                "is_active": strategy.is_active,
                "updated_at": datetime.now().isoformat()
            }
            
            # Upsert by strategy_name
            result = self.db.strategy_templates.update_one(
                {"strategy_name": strategy.strategy_name},
                {
                    "$set": doc,
                    "$setOnInsert": {"created_at": datetime.now().isoformat()}
                },
                upsert=True
            )
            
            logger.info(f"Saved strategy template: {strategy.strategy_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving strategy template: {e}")
            return False
