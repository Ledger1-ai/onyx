#!/usr/bin/env python3
"""
Schedule Manager for Intelligent Twitter Agent
=============================================
Manages daily schedules, time slot allocation, and dynamic adjustments.
"""

import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Tuple
import json
import random
from uuid import uuid4

from data_models import (
    ScheduleSlot, DailySchedule, ActivityType, SlotStatus, StrategyTemplate,
    PerformanceAnalysis, OptimizationRule, create_default_strategy, validate_schedule_slot
)
from database_manager import DatabaseManager, generate_slot_id

logger = logging.getLogger(__name__)

class ScheduleManager:
    """Manages scheduling for the intelligent Twitter agent"""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize schedule manager"""
        self.db = db_manager
        self.slot_duration_minutes = 15  # Each slot is 15 minutes
        self.slots_per_hour = 4
        self.slots_per_day = 24 * self.slots_per_hour  # 96 slots per day
        
        # Default activity configuration
        self.default_activity_configs = self._get_default_activity_configs()
        
        # Performance review time (midnight for 30 minutes)
        self.performance_review_start = time(0, 0)  # 00:00
        self.performance_review_duration = 30  # minutes
        
        logger.info("Schedule Manager initialized")
    
    def set_twitter_premium_status(self, is_premium: bool):
        """Update the premium status for Twitter to enable/disable analytics tasks."""
        self.has_twitter_premium = is_premium
        logger.info(f"Updated Twitter Premium status to: {is_premium}")

    def _get_default_activity_configs(self) -> Dict[ActivityType, Dict[str, Any]]:
        """Get default configurations for each activity type"""
        return {
            ActivityType.TWEET: {
                "max_daily_tweets": 5,
                "min_interval_hours": 2,
                "optimal_times": ["09:00", "12:00", "15:00", "18:00", "21:00"],
                "priority": 4
            },
            ActivityType.IMAGE_TWEET: {
                "max_daily_tweets": 2,
                "min_interval_hours": 4,
                "optimal_times": ["11:00", "16:00", "20:00"],
                "priority": 4,
                "content_type": "image",
                "generation_time": 30  # minutes needed for generation
            },
            ActivityType.VIDEO_TWEET: {
                "max_daily_tweets": 1,
                "min_interval_hours": 6,
                "optimal_times": ["12:00", "18:00"],
                "priority": 5,
                "content_type": "video",
                "generation_time": 45  # minutes needed for generation
            },
            ActivityType.THREAD: {
                "max_daily_threads": 1,
                "min_interval_hours": 8,
                "optimal_times": ["10:00", "15:00", "19:00"],
                "priority": 5,
                "content_type": "thread",
                "generation_time": 20,  # minutes needed for planning and writing
                "thread_length": "3-5",  # typical thread length
                "topic_focus": "educational"
            },
            ActivityType.SCROLL_ENGAGE: {
                "session_duration": 15,  # minutes
                "max_daily_sessions": 15,  # Increased from 8 to 15
                "engagement_goals": {"likes": 10, "replies": 3, "retweets": 2},
                "priority": 3
            },
            ActivityType.SEARCH_ENGAGE: {
                "session_duration": 15,  # minutes
                "max_daily_sessions": 10,
                "search_defaults": {"search_type": "latest", "max_tweets": 5, "engagement_type": "mixed"},
                "priority": 3
            },
            ActivityType.REPLY: {
                "max_replies_per_session": 5,
                "response_quality_threshold": 0.7,
                "max_daily_replies": 15,
                "priority": 3
            },
            # ActivityType.AUTO_REPLY: {
            #     "auto_reply_threshold": 0.8,
            #     "max_auto_replies_per_hour": 3,
            #     "keywords_focus": ["AI", "programming", "tech"],
            #     "priority": 2
            # },
            # ActivityType.CONTENT_CREATION: {
            #     "session_duration": 30,
            #     "daily_creation_blocks": 2,
            #     "content_types": ["thread", "image_post", "educational"],
            #     "priority": 4
            # },
            ActivityType.RADAR_DISCOVERY: {
                "session_duration": 20,
                "daily_discovery_sessions": 3,
                "focus_areas": ["trending_topics", "competitor_analysis", "industry_news"],
                "priority": 2
            },
            # ActivityType.ANALYTICS_CHECK: {
            #     "session_duration": 10,
            #     "daily_checks": 3,
            #     "metrics_focus": ["engagement", "growth", "reach"],
            #     "priority": 1
            # },
            # ActivityType.MONITOR: {
            #     "continuous": True,
            #     "alert_thresholds": {"mentions": 5, "dm_responses": 3},
            #     "priority": 1
            # },
            # ActivityType.PERFORMANCE_ANALYSIS: {
            #     "session_duration": 30,
            #     "daily_analysis": 1,
            #     "analysis_depth": "comprehensive",
            #     "priority": 5
            # },
            #     "review_scope": "full_strategy",
            #     "priority": 5
            # }
            ActivityType.LINKEDIN_POST: {
                "max_daily_posts": 1,
                "min_interval_hours": 24,
                "optimal_times": ["08:00", "10:00", "12:00"], 
                "priority": 4,
                "content_type": "text_professional",
                "generation_time": 20
            },
            ActivityType.LINKEDIN_IMAGE_POST: {
                "max_daily_posts": 1,
                "min_interval_hours": 24,
                "optimal_times": ["09:00", "13:00"], 
                "priority": 4,
                "content_type": "image",
                "generation_time": 30
            },
            ActivityType.LINKEDIN_VIDEO_POST: {
                "max_daily_posts": 1,
                "min_interval_hours": 48,
                "optimal_times": ["12:00", "17:00"], 
                "priority": 5,
                "content_type": "video",
                "generation_time": 45
            },
            ActivityType.LINKEDIN_THREAD: {
                "max_daily_posts": 1,
                "min_interval_hours": 72, # Articles less frequent
                "optimal_times": ["10:00"], 
                "priority": 5,
                "content_type": "article",
                "generation_time": 60
            },
            ActivityType.LINKEDIN_ENGAGE: {
                "session_duration": 15,
                "max_daily_sessions": 3,
                "engagement_goals": {"likes": 5, "comments": 2},
                "priority": 3,
                "optimal_times": ["08:30", "12:30", "17:30"]
            },
            ActivityType.LINKEDIN_SEARCH_ENGAGE: {
                "session_duration": 15,
                "max_daily_sessions": 2,
                "priority": 3,
                "optimal_times": ["11:00", "15:00"]
            },
            ActivityType.LINKEDIN_CONNECT: {
                "max_daily_connections": 5,
                "priority": 2,
                "optimal_times": ["09:00", "17:00"]
            },
            ActivityType.LINKEDIN_REPLY: {
                "max_daily_replies": 10,
                "priority": 3,
                "optimal_times": ["10:00", "14:00"]
            },
            ActivityType.LINKEDIN_CONTENT_CREATION: {
                "daily_sessions": 1,
                "priority": 3,
                "optimal_times": ["16:00"]
            },
            ActivityType.LINKEDIN_RADAR_DISCOVERY: {
                "daily_sessions": 1,
                "priority": 2,
                "optimal_times": ["08:00"]
            },
            ActivityType.LINKEDIN_MONITOR: {
                "daily_sessions": 3,
                "priority": 2,
                "optimal_times": ["08:15", "12:15", "17:15"]
            },
            ActivityType.LINKEDIN_ANALYTICS: {
                "daily_sessions": 1,
                "priority": 2,
                "optimal_times": ["08:00"]
            },
            ActivityType.LINKEDIN_STRATEGY: {
                "daily_sessions": 1,
                "priority": 5,
                "optimal_times": ["07:30"]
            },
            # --- META (FACEBOOK/INSTAGRAM) CONFIGS ---
            ActivityType.FACEBOOK_POST: {
                "max_daily_posts": 2,
                "min_interval_hours": 4,
                "optimal_times": ["09:00", "13:00", "15:00"],
                "priority": 4,
                "content_type": "text_image",
                "generation_time": 20
            },
            ActivityType.FACEBOOK_STORY: {
                "max_daily_posts": 3,
                "min_interval_hours": 3,
                "optimal_times": ["10:00", "14:00", "18:00"],
                "priority": 3,
                "content_type": "story",
                "generation_time": 15
            },
            ActivityType.FACEBOOK_ENGAGE: {
                "session_duration": 15,
                "max_daily_sessions": 2,
                "engagement_goals": {"reactions": 10, "comments": 3},
                "priority": 3,
                "optimal_times": ["08:30", "19:00"]
            },
            ActivityType.INSTAGRAM_POST: {
                "max_daily_posts": 1,
                "min_interval_hours": 8,
                "optimal_times": ["11:00", "19:00"],
                "content_type": "image",
                "priority": 4,
                "generation_time": 25
            },
            ActivityType.INSTAGRAM_STORY: {
                "max_daily_posts": 4,
                "min_interval_hours": 2,
                "optimal_times": ["09:00", "12:00", "15:00", "18:00"],
                "priority": 3,
                "content_type": "story",
                "generation_time": 15
            },
            ActivityType.INSTAGRAM_REEL: {
                "max_daily_posts": 1,
                "min_interval_hours": 24,
                "optimal_times": ["12:00", "18:00"],
                "priority": 5,
                "content_type": "video",
                "generation_time": 45
            },
            ActivityType.INSTAGRAM_ENGAGE: {
                "session_duration": 15,
                "max_daily_sessions": 4,
                "priority": 3,
                "optimal_times": ["08:00", "12:00", "17:00", "21:00"]
            }
        }
    
    def create_daily_schedule(self, date: str, strategy: Optional[StrategyTemplate] = None, disabled_activity_types: List[str] = None) -> DailySchedule:
        """Create a comprehensive daily schedule for the specified date"""
        try:
            # First, check if a schedule already exists for this date
            existing_schedule = self.db.get_daily_schedule(date)
            if existing_schedule:
                logger.info(f"Schedule for {date} already exists. Returning existing schedule.")
                return existing_schedule
            
            # Check if slots already exist for this date
            existing_slots = self.db.get_schedule_slots(date)
            if existing_slots:
                logger.info(f"Found {len(existing_slots)} existing slots for {date}. Skipping schedule creation.")
                # Create a schedule object from existing slots
                return DailySchedule(
                    date=date,
                    slots=existing_slots,
                    strategy_focus="Existing",
                    daily_goals=self._extract_goals_from_slots(existing_slots),
                    performance_targets={"engagement_rate": 0.03, "follower_growth": 5.0}
                )
            
            # Use provided strategy or get default
            if not strategy:
                strategy = self._get_active_strategy()
            
            # Create base schedule structure
            schedule = DailySchedule(
                date=date,
                strategy_focus=strategy.strategy_name if strategy else "Default",
                daily_goals=self._generate_daily_goals(strategy),
                performance_targets=self._generate_performance_targets(strategy)
            )
            
            # Generate time slots
            slots = self._generate_time_slots(date, strategy, disabled_activity_types=disabled_activity_types)
            
            # Let AI schedule freely - no optimization constraints
            schedule.slots = slots
            schedule.total_activities = len([s for s in slots if s.activity_type != ActivityType.MONITOR])
            
            # Save to database
            if self.db.save_daily_schedule(schedule):
                # Save individual slots
                for slot in slots:
                    self.db.save_schedule_slot(slot)
                
                logger.info(f"Created daily schedule for {date} with {len(slots)} slots")
                return schedule
            else:
                logger.error(f"Failed to save daily schedule for {date}")
                return schedule
            
        except Exception as e:
            logger.error(f"Error creating daily schedule: {e}")
            # Return basic schedule
            return DailySchedule(date=date, strategy_focus="Emergency", daily_goals={}, performance_targets={})

    def regenerate_daily_schedule_for_platform(self, date: str, platform: str, strategy: Optional[StrategyTemplate] = None) -> Optional[DailySchedule]:
        """Regenerate tasks for a specific platform while preserving others."""
        try:
            logger.info(f"🔄 Regenerating schedule for {platform} on {date}")
            
            # 1. Get existing slots
            existing_slots = self.db.get_schedule_slots(date)
            
            # 2. Filter slots
            preserved_slots = []
            for slot in existing_slots:
                # Helper to determine platform (basic heuristic)
                act_type = slot.activity_type.value.lower() if hasattr(slot.activity_type, 'value') else str(slot.activity_type).lower()
                
                is_linkedin = 'linkedin_' in act_type
                is_twitter = not is_linkedin and act_type != 'linkedin'
                
                if platform == 'twitter':
                    if is_linkedin:
                        preserved_slots.append(slot)
                elif platform == 'linkedin':
                    if is_twitter:
                        preserved_slots.append(slot)
            
            logger.info(f"Preserving {len(preserved_slots)} slots from other platforms")
            
            # 3. Clear all slots for the day to avoid ID conflicts/duplicates
            # We access the raw db collection to delete many
            if hasattr(self.db, 'db') and self.db.db is not None:
                self.db.db.schedule_slots.delete_many({"date": date})
            else:
                logger.warning("Could not access raw DB to clear slots, continuing (risk of duplicates)")

            # 4. Generate new slots (passing preserved as existing)
            if not strategy:
                strategy = self._get_active_strategy()
                
            # This will generate full day slots including our preserved ones + new ones for the target platform
            new_slots = self._generate_time_slots(date, strategy, existing_slots=preserved_slots)
            
            # 5. Create and save new schedule
            schedule = DailySchedule(
                date=date,
                strategy_focus=strategy.strategy_name if strategy else "regen_" + platform,
                daily_goals=self._generate_daily_goals(strategy),
                performance_targets=self._generate_performance_targets(strategy)
            )
            schedule.slots = new_slots
            schedule.total_activities = len([s for s in new_slots if s.activity_type != ActivityType.MONITOR])
            
            # Save to database
            if self.db.save_daily_schedule(schedule):
                for slot in new_slots:
                    self.db.save_schedule_slot(slot)
                logger.info(f"✅ Successfully regenerated schedule with {len(new_slots)} slots")
                return schedule
            
            return None
            
        except Exception as e:
            logger.error(f"Error regenerating schedule for {platform}: {e}", exc_info=True)
            return None
    
    def _extract_goals_from_slots(self, slots: List[ScheduleSlot]) -> Dict[str, Any]:
        """Extract daily goals from existing slots"""
        goals = {}
        activity_counts = {}
        
        for slot in slots:
            activity_type = slot.activity_type
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
        
        # Convert counts to goal names
        goals["tweets"] = activity_counts.get(ActivityType.TWEET, 0)
        goals["image_tweets"] = activity_counts.get(ActivityType.IMAGE_TWEET, 0)
        goals["video_tweets"] = activity_counts.get(ActivityType.VIDEO_TWEET, 0)
        goals["threads"] = activity_counts.get(ActivityType.THREAD, 0)
        goals["engagement_sessions"] = activity_counts.get(ActivityType.SCROLL_ENGAGE, 0)
        goals["replies"] = activity_counts.get(ActivityType.REPLY, 0) * 3
        goals["auto_replies"] = activity_counts.get(ActivityType.AUTO_REPLY, 0) * 2
        goals["content_creation_sessions"] = activity_counts.get(ActivityType.CONTENT_CREATION, 0)
        goals["radar_discovery_sessions"] = activity_counts.get(ActivityType.RADAR_DISCOVERY, 0)
        goals["analytics_checks"] = activity_counts.get(ActivityType.ANALYTICS_CHECK, 0)
        goals["monitor_sessions"] = activity_counts.get(ActivityType.MONITOR, 0)
        goals["performance_analysis"] = activity_counts.get(ActivityType.PERFORMANCE_ANALYSIS, 0)
        goals["performance_analysis"] = activity_counts.get(ActivityType.PERFORMANCE_ANALYSIS, 0)
        goals["strategy_review"] = activity_counts.get(ActivityType.STRATEGY_REVIEW, 0)
        goals["linkedin_posts"] = activity_counts.get(ActivityType.LINKEDIN_POST, 0)
        goals["linkedin_posts"] = activity_counts.get(ActivityType.LINKEDIN_POST, 0) + activity_counts.get(ActivityType.LINKEDIN_IMAGE_POST, 0) + activity_counts.get(ActivityType.LINKEDIN_VIDEO_POST, 0) + activity_counts.get(ActivityType.LINKEDIN_THREAD, 0)
        goals["linkedin_engagement_sessions"] = activity_counts.get(ActivityType.LINKEDIN_ENGAGE, 0) + activity_counts.get(ActivityType.LINKEDIN_SEARCH_ENGAGE, 0)
        goals["linkedin_connections"] = activity_counts.get(ActivityType.LINKEDIN_CONNECT, 0)
        goals["linkedin_replies"] = activity_counts.get(ActivityType.LINKEDIN_REPLY, 0)
        goals["linkedin_monitor"] = activity_counts.get(ActivityType.LINKEDIN_MONITOR, 0)
        goals["linkedin_analytics"] = activity_counts.get(ActivityType.LINKEDIN_ANALYTICS, 0)
        goals["linkedin_strategy"] = activity_counts.get(ActivityType.LINKEDIN_STRATEGY, 0)
        
        goals["facebook_posts"] = activity_counts.get(ActivityType.FACEBOOK_POST, 0) + activity_counts.get(ActivityType.FACEBOOK_STORY, 0)
        goals["facebook_engagement"] = activity_counts.get(ActivityType.FACEBOOK_ENGAGE, 0)
        goals["instagram_posts"] = activity_counts.get(ActivityType.INSTAGRAM_POST, 0) + activity_counts.get(ActivityType.INSTAGRAM_STORY, 0) + activity_counts.get(ActivityType.INSTAGRAM_REEL, 0)
        goals["instagram_engagement"] = activity_counts.get(ActivityType.INSTAGRAM_ENGAGE, 0)
        
        return goals
    
    def _get_active_strategy(self) -> Optional[StrategyTemplate]:
        """Get the currently active strategy"""
        try:
            strategies = self.db.get_all_strategy_templates()
            active_strategies = [s for s in strategies if s.is_active]
            
            if active_strategies:
                return active_strategies[0]  # Return first active strategy
            else:
                # Create and save default strategy
                default_strategy = create_default_strategy()
                self.db.save_strategy_template(default_strategy)
                return default_strategy
            
        except Exception as e:
            logger.error(f"Error getting active strategy: {e}")
            return create_default_strategy()
    
    def _generate_daily_goals(self, strategy: Optional[StrategyTemplate]) -> Dict[str, Any]:
        """Generate daily goals based on strategy"""
        if not strategy:
            return {
                "tweets": 3,
                "image_tweets": 2,
                "video_tweets": 1,
                "threads": 1,
                "engagement_sessions": 4,
                "replies": 10,
                "auto_replies": 8,
                "content_creation": 1,
                "radar_discovery": 2,
                "analytics_checks": 3,
                "monitor_sessions": 4,
                "performance_analysis": 1,
                "strategy_review": 1
            }
        
        goals = {}
        
        # Calculate goals based on activity distribution
        total_slots_available = 80  # Approximate non-sleep slots
        
        for activity_type, percentage in strategy.activity_distribution.items():
            slots_for_activity = int(total_slots_available * percentage)
            
            if activity_type == ActivityType.TWEET:
                goals["tweets"] = min(slots_for_activity, 8)  # Max 8 tweets per day
            elif activity_type == ActivityType.IMAGE_TWEET:
                goals["image_tweets"] = min(slots_for_activity, 3)  # Max 3 image tweets per day
            elif activity_type == ActivityType.VIDEO_TWEET:
                goals["video_tweets"] = min(slots_for_activity, 2)  # Max 2 video tweets per day
            elif activity_type == ActivityType.THREAD:
                goals["threads"] = min(slots_for_activity, 1)  # Max 1 thread per day
            elif activity_type == ActivityType.SCROLL_ENGAGE:
                goals["engagement_sessions"] = slots_for_activity
            elif activity_type == ActivityType.REPLY:
                goals["replies"] = slots_for_activity * 3  # 3 replies per slot
            elif activity_type == ActivityType.AUTO_REPLY:
                goals["auto_replies"] = slots_for_activity * 2  # 2 auto replies per slot
            elif activity_type == ActivityType.CONTENT_CREATION:
                goals["content_creation_sessions"] = slots_for_activity
            elif activity_type == ActivityType.RADAR_DISCOVERY:
                goals["radar_discovery_sessions"] = slots_for_activity
            elif activity_type == ActivityType.ANALYTICS_CHECK:
                goals["analytics_checks"] = slots_for_activity
            elif activity_type == ActivityType.MONITOR:
                goals["monitor_sessions"] = slots_for_activity
            elif activity_type == ActivityType.PERFORMANCE_ANALYSIS:
                goals["performance_analysis"] = slots_for_activity
            elif activity_type == ActivityType.STRATEGY_REVIEW:
                goals["strategy_review"] = slots_for_activity
            elif activity_type == ActivityType.LINKEDIN_POST:
                goals["linkedin_posts"] = min(slots_for_activity, 1)
            elif activity_type == ActivityType.LINKEDIN_ENGAGE:
                goals["linkedin_engagement_sessions"] = slots_for_activity
            elif activity_type == ActivityType.LINKEDIN_CONNECT:
                goals["linkedin_connections"] = slots_for_activity
            elif activity_type == ActivityType.LINKEDIN_REPLY:
                goals["linkedin_replies"] = slots_for_activity
            elif activity_type == ActivityType.LINKEDIN_MONITOR:
                goals["linkedin_monitor"] = slots_for_activity
            elif activity_type == ActivityType.LINKEDIN_ANALYTICS:
                goals["linkedin_analytics"] = 1
            elif activity_type == ActivityType.LINKEDIN_STRATEGY:
                goals["linkedin_strategy"] = 1
            elif activity_type == ActivityType.FACEBOOK_POST:
                goals["facebook_posts"] = min(slots_for_activity, 2)
            elif activity_type == ActivityType.FACEBOOK_ENGAGE:
                goals["facebook_engagement"] = slots_for_activity
            elif activity_type == ActivityType.INSTAGRAM_POST:
                goals["instagram_posts"] = min(slots_for_activity, 1)
            elif activity_type == ActivityType.INSTAGRAM_ENGAGE:
                goals["instagram_engagement"] = slots_for_activity
        
        # Add engagement targets
        for metric, target in strategy.target_metrics.items():
            goals[metric.value] = target
        
        return goals
    
    def _generate_performance_targets(self, strategy: Optional[StrategyTemplate]) -> Dict[str, float]:
        """Generate performance targets based on strategy"""
        if not strategy:
            return {
                "engagement_rate": 0.03,
                "follower_growth": 5.0,
                "tweet_impressions": 500.0
            }
        
        targets = {}
        for metric, target in strategy.target_metrics.items():
            targets[metric.value] = target
        
        return targets
    
    def _generate_time_slots(self, date: str, strategy: Optional[StrategyTemplate], existing_slots: List[ScheduleSlot] = None, disabled_activity_types: List[str] = None) -> List[ScheduleSlot]:
        """Generate time slots with AI autonomy - let the AI decide what to do when"""
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            today_date = datetime.now().date()

            # Helper to round to next 15-minute boundary
            def _next_boundary(dt: datetime) -> datetime:
                minute_block = (dt.minute // self.slot_duration_minutes + 1) * self.slot_duration_minutes
                if minute_block == 60:
                    dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                else:
                    dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=minute_block)
                return dt

            # Determine start and end times for the day
            if target_date == today_date:
                # Start at the next boundary after now
                day_start = _next_boundary(datetime.now())
            else:
                day_start = datetime.combine(target_date, datetime.min.time())
            
            # End the day at 23:45 to prevent slots from crossing midnight
            day_end = datetime.combine(target_date, time(23, 45))

            # Generate slots at 15-minute intervals - AI decides what to do
            slots: List[ScheduleSlot] = []
            
            # If we have existing slots, add them to our list
            if existing_slots:
                slots.extend(existing_slots)
                # Ensure we don't start before end of any relevant existing slot?
                # Actually, we loop through all times and check if occupied.
            
            current_time = day_start
            
            # All available activity types for AI to choose from
            all_activities = [
                ActivityType.TWEET,
                ActivityType.IMAGE_TWEET,
                ActivityType.VIDEO_TWEET,
                ActivityType.THREAD,
                ActivityType.SCROLL_ENGAGE,
                ActivityType.SEARCH_ENGAGE,
                ActivityType.REPLY,
                # ActivityType.AUTO_REPLY,
                ActivityType.CONTENT_CREATION,
                ActivityType.RADAR_DISCOVERY,
                ActivityType.LINKEDIN_POST,
                # ActivityType.LINKEDIN_POST, # Duplicate
                ActivityType.LINKEDIN_IMAGE_POST,
                ActivityType.LINKEDIN_VIDEO_POST,
                ActivityType.LINKEDIN_THREAD,
                ActivityType.LINKEDIN_ENGAGE,
                ActivityType.LINKEDIN_SEARCH_ENGAGE,
                ActivityType.LINKEDIN_CONNECT,
                ActivityType.LINKEDIN_REPLY,
                ActivityType.LINKEDIN_CONTENT_CREATION,
                ActivityType.LINKEDIN_RADAR_DISCOVERY,
                ActivityType.LINKEDIN_MONITOR,
                ActivityType.LINKEDIN_ANALYTICS,
                ActivityType.LINKEDIN_STRATEGY,
                # ActivityType.ANALYTICS_CHECK,
                # ActivityType.MONITOR,
                ActivityType.LINKEDIN_STRATEGY,
                # --- META ---
                ActivityType.FACEBOOK_POST,
                ActivityType.FACEBOOK_STORY,
                ActivityType.FACEBOOK_ENGAGE,
                ActivityType.INSTAGRAM_POST,
                ActivityType.INSTAGRAM_STORY,
                ActivityType.INSTAGRAM_REEL,
                ActivityType.INSTAGRAM_ENGAGE,
                # ---
                ActivityType.PERFORMANCE_ANALYSIS, # Enabled for Premium users
                # ActivityType.ANALYTICS_CHECK,
                # ActivityType.MONITOR,
                # ActivityType.STRATEGY_REVIEW
                # ActivityType.STRATEGY_REVIEW
            ]
            
            # Filter disabled activities
            if disabled_activity_types:
                initial_count = len(all_activities)
                all_activities = [a for a in all_activities if a.value not in disabled_activity_types]
                logger.info(f"DEBUG: Filtering disabled tasks: {disabled_activity_types}")
                logger.info(f"DEBUG: Activities reduced from {initial_count} to {len(all_activities)}")
                logger.info(f"DEBUG: Remaining activities: {[a.value for a in all_activities]}")
                
                if not all_activities:
                    logger.warning("All activities disabled! Reverting to ActivityType.TWEET fallback.")
                    all_activities = [ActivityType.TWEET]
            
            # Helper to check if time is occupied
            def is_occupied(t: datetime) -> bool:
                for s in slots:
                    # Check overlap. existing slots are 15 mins by default but maybe longer?
                    # Assuming basic 15 min grid for simplicity for now
                    # Or check s.start_time <= t < s.end_time
                    if s.start_time <= t < s.end_time:
                        return True
                return False

            # Generate slots for each 15-minute interval
            while current_time < day_end:
                # specific check for occupied
                if is_occupied(current_time):
                    current_time += timedelta(minutes=self.slot_duration_minutes)
                    continue

                # AI autonomously selects activity for this slot
                activity_type = self._ai_select_activity(current_time, slots, all_activities, strategy)
                
                if activity_type:
                    slot = ScheduleSlot(
                        slot_id=generate_slot_id(),
                        start_time=current_time,
                        end_time=current_time + timedelta(minutes=self.slot_duration_minutes),
                        activity_type=activity_type,
                        activity_config=self._get_activity_config(activity_type, strategy),
                        priority=self._get_activity_priority(activity_type, current_time),
                        is_flexible=self._is_activity_flexible(activity_type),
                        status=SlotStatus.SCHEDULED
                    )
                    
                    if validate_schedule_slot(slot):
                        slots.append(slot)
                
                current_time += timedelta(minutes=self.slot_duration_minutes)
            
            return slots
            
        except Exception as e:
            logger.error(f"Error generating time slots: {e}")
            return []
    
    def _ai_select_activity(self, slot_time: datetime, existing_slots: List[ScheduleSlot], 
                           available_activities: List[ActivityType], strategy: Optional[StrategyTemplate]) -> Optional[ActivityType]:
        """AI autonomously selects activity for this time slot"""
        hour = slot_time.hour
        
        # Count recent activities for variety
        recent_activities = {}
        for slot in existing_slots[-8:]:  # Look at last 8 slots (2 hours)
            activity = slot.activity_type
            recent_activities[activity] = recent_activities.get(activity, 0) + 1
        
        # AI decision factors (the AI can weigh these however it wants)
        activity_weights = {}
        
        for activity in available_activities:
            weight = 1.0  # Base weight
            
            # AI reasoning for each activity type
            if activity == ActivityType.TWEET:
                # AI decides: tweets are good throughout day, but especially peak hours
                if 12 <= hour <= 17 or 19 <= hour <= 21:
                    weight *= 1.4
                # Avoid too many recent tweets
                if recent_activities.get(activity, 0) >= 2:
                    weight *= 0.3
                    
            elif activity == ActivityType.SCROLL_ENGAGE:
                # Engagement is valuable, but avoid back-to-back sessions
                if 10 <= hour <= 22:
                    weight *= 1.2  # reduced bias toward scroll in active hours
                recent_scrolls = recent_activities.get(ActivityType.SCROLL_ENGAGE, 0)
                # Penalize consecutive scroll sessions
                if recent_scrolls >= 2:
                    weight *= 0.5
                elif recent_scrolls == 1:
                    weight *= 0.8
                else:
                    weight *= 1.05  # slight boost only if no recent scroll
                # Hard cap to avoid long streaks of scroll_engage
                if recent_scrolls >= 3:
                    weight *= 0.3
                    
            elif activity == ActivityType.CONTENT_CREATION:
                # AI decides: creative work better in focused times
                if 8 <= hour <= 11 or 14 <= hour <= 17:
                    weight *= 1.5
                elif 22 <= hour or hour <= 6:
                    weight *= 0.3  # Less creative at night/early morning
                    
            elif activity == ActivityType.ANALYTICS_CHECK:
                # AI decides: analytics can happen anytime, but good for breaks
                weight *= 1.0  # Neutral
                # More valuable if we haven't checked recently
                if recent_activities.get(activity, 0) == 0:
                    weight *= 1.3
                    
            elif activity == ActivityType.REPLY:
                # AI decides: replies good during active hours
                if 9 <= hour <= 20:
                    weight *= 1.2

            elif activity == ActivityType.SEARCH_ENGAGE:
                # Prefer search_engage right after scroll_engage to diversify
                recent_scrolls = recent_activities.get(ActivityType.SCROLL_ENGAGE, 0)
                if recent_scrolls >= 1:
                    weight *= 1.5  # strong preference to switch to search after scroll
                else:
                    weight *= 1.1  # mild boost otherwise
                    
            elif activity == ActivityType.AUTO_REPLY:
                # AI decides: auto replies can happen anytime, good filler
                weight *= 1.1
                
            elif activity == ActivityType.IMAGE_TWEET:
                # AI decides: visual content good for engagement times
                if 11 <= hour <= 16 or 18 <= hour <= 21:
                    weight *= 1.3
                # Don't overdo image tweets
                if recent_activities.get(activity, 0) >= 1:
                    weight *= 0.5
                    
            elif activity == ActivityType.VIDEO_TWEET:
                # AI decides: video content for prime time
                if 12 <= hour <= 15 or 18 <= hour <= 20:
                    weight *= 1.5
                else:
                    weight *= 0.7
                # Videos are special, don't overdo
                if recent_activities.get(activity, 0) >= 1:
                    weight *= 0.2
                    
            elif activity == ActivityType.THREAD:
                # AI decides: threads need focus time
                if 9 <= hour <= 12 or 15 <= hour <= 18:
                    weight *= 1.4
                # Threads are substantial, space them out
                if recent_activities.get(activity, 0) >= 1:
                    weight *= 0.3
                    
            elif activity == ActivityType.RADAR_DISCOVERY:
                # AI decides: discovery good for learning, anytime works
                weight *= 1.0
                
            elif activity == ActivityType.MONITOR:
                # AI decides: monitoring is background, can happen anytime
                weight *= 0.9  # Slightly lower priority
                
            elif activity == ActivityType.PERFORMANCE_ANALYSIS:
                # Premium check simplified
                is_premium = getattr(self, 'has_twitter_premium', False)
                if not is_premium:
                    weight = 0.0
                else:
                    if 8 <= hour <= 10 or 16 <= hour <= 18:
                        weight *= 1.3
                    elif hour >= 22 or hour <= 6:
                        weight *= 0.4
                    
            elif activity == ActivityType.STRATEGY_REVIEW:
                # AI decides: strategy review needs deep focus
                if 9 <= hour <= 11 or 15 <= hour <= 17:
                    weight *= 1.5
                else:
                    weight *= 0.6
                # Strategy reviews are rare and important
                if recent_activities.get(activity, 0) >= 1:
                    weight *= 0.1
            
            elif activity == ActivityType.LINKEDIN_POST:
                # LinkedIn posts best during business hours
                if 8 <= hour <= 17:
                    if hour in [8, 9, 10, 12, 13, 16]:
                        weight *= 1.6
                    else:
                        weight *= 1.3
                else:
                    weight *= 0.1 # Very low priority outside business hours
                
                # Only 1 post per day usually
                if recent_activities.get(activity, 0) >= 1:
                    weight *= 0.05
                    
            elif activity == ActivityType.LINKEDIN_ENGAGE:
                # Engagement good during business hours + morning/evening commute
                if 7 <= hour <= 9 or 12 <= hour <= 13 or 17 <= hour <= 19:
                    weight *= 1.4
                elif 9 <= hour <= 17:
                    weight *= 1.1
                else:
                    weight *= 0.2
                
                # Space out sessions
                if recent_activities.get(activity, 0) >= 1:
                    weight *= 0.4

            elif activity == ActivityType.LINKEDIN_CONNECT:
                # Connections good during business hours
                if 9 <= hour <= 17:
                    weight *= 1.2
                else:
                    weight *= 0.3
                
                # Limit connections
                if recent_activities.get(activity, 0) >= 1:
                    weight *= 0.2

            elif activity == ActivityType.LINKEDIN_REPLY:
                # Replies good during business hours
                if 9 <= hour <= 17:
                    weight *= 1.3
                else:
                    weight *= 0.3

            elif activity == ActivityType.LINKEDIN_MONITOR:
                # Monitor anytime
                weight *= 0.9

            elif activity == ActivityType.LINKEDIN_ANALYTICS:
                # Analytics mostly morning
                if 7 <= hour <= 9:
                    weight *= 1.5
                else:
                    weight *= 0.5
                
                if recent_activities.get(activity, 0) >= 1:
                    weight *= 0.1

            elif activity == ActivityType.LINKEDIN_STRATEGY:
                # Strategy mostly morning
                if 7 <= hour <= 9:
                    weight *= 1.6
                else:
                    weight *= 0.4
                    
                if recent_activities.get(activity, 0) >= 1:
                    weight *= 0.05
            
            # --- META ---
            elif activity == ActivityType.FACEBOOK_POST:
                if 9 <= hour <= 17: weight *= 1.4
                else: weight *= 0.5
                if recent_activities.get(activity, 0) >= 1: weight *= 0.1
                
            elif activity == ActivityType.FACEBOOK_STORY:
                if 8 <= hour <= 20: weight *= 1.2
                if recent_activities.get(activity, 0) >= 1: weight *= 0.8
                
            elif activity == ActivityType.FACEBOOK_ENGAGE:
                if 8 <= hour <= 20: weight *= 1.1
                if recent_activities.get(activity, 0) >= 1: weight *= 0.5

            elif activity == ActivityType.INSTAGRAM_POST:
                if 17 <= hour <= 21: weight *= 1.6 # Evening peak for IG
                elif 11 <= hour <= 13: weight *= 1.4 # Lunch
                else: weight *= 0.8
                if recent_activities.get(activity, 0) >= 1: weight *= 0.05
                
            elif activity == ActivityType.INSTAGRAM_STORY:
                weight *= 1.2 # Stories always good
                if recent_activities.get(activity, 0) >= 2: weight *= 0.4
                
            elif activity == ActivityType.INSTAGRAM_REEL:
                if 18 <= hour <= 22: weight *= 1.8 # Prime Entertainment time
                else: weight *= 0.6
                if recent_activities.get(activity, 0) >= 1: weight *= 0.1

            elif activity == ActivityType.INSTAGRAM_ENGAGE:
                if 8 <= hour <= 22: weight *= 1.3
                if recent_activities.get(activity, 0) >= 2: weight *= 0.3
            
            # Add variety bonus - AI likes mixing things up
            variety_bonus = 1.0
            if recent_activities.get(activity, 0) == 0:
                variety_bonus = 1.4  # Bonus for activities we haven't done recently
            elif recent_activities.get(activity, 0) >= 2:
                variety_bonus = 0.6  # Penalty for repetitive activities
                
            # Add randomness - AI can be spontaneous
            randomness = random.uniform(0.7, 1.3)
            
            final_weight = weight * variety_bonus * randomness
            activity_weights[activity] = final_weight
        
        # AI selects based on weighted preferences
        if activity_weights:
            # Sort by weight and pick the top choice
            sorted_activities = sorted(activity_weights.items(), key=lambda x: x[1], reverse=True)
            return sorted_activities[0][0]
        
        # Fallback: pick randomly if no weights calculated
        return random.choice(available_activities) if available_activities else None
    
    def _get_activity_config(self, activity_type: ActivityType, strategy: Optional[StrategyTemplate]) -> Dict[str, Any]:
        """Get configuration for a specific activity"""
        base_config = self.default_activity_configs.get(activity_type, {}).copy()
        
        # Add strategy-specific configuration
        if strategy:
            if activity_type == ActivityType.TWEET and strategy.hashtag_strategy:
                base_config["hashtags"] = strategy.hashtag_strategy[:3]  # Top 3 hashtags
            
            if activity_type == ActivityType.SCROLL_ENGAGE and strategy.engagement_strategy:
                base_config.update(strategy.engagement_strategy)
            
            if hasattr(strategy, 'tone_guidelines') and strategy.tone_guidelines:
                base_config["tone"] = strategy.tone_guidelines
        
        return base_config
    
    def _get_activity_priority(self, activity_type: ActivityType, slot_time: datetime) -> int:
        """Determine priority for activity based on type and time"""
        base_priority = self.default_activity_configs.get(activity_type, {}).get("priority", 1)
        
        hour = slot_time.hour
        
        # Boost priority for optimal times
        if activity_type == ActivityType.TWEET:
            optimal_hours = [9, 12, 15, 18, 21]
            if hour in optimal_hours:
                base_priority += 1
        
        if activity_type == ActivityType.SCROLL_ENGAGE:
            # High engagement times
            peak_hours = [12, 13, 18, 19, 20, 21]
            if hour in peak_hours:
                base_priority += 1
        
        return min(base_priority, 5)  # Cap at 5
    
    def _is_activity_flexible(self, activity_type: ActivityType) -> bool:
        """Determine if activity timing is flexible"""
        flexible_activities = [
            ActivityType.SCROLL_ENGAGE,
            ActivityType.REPLY,
            ActivityType.RADAR_DISCOVERY,
            ActivityType.ANALYTICS_CHECK
        ]
        
        return activity_type in flexible_activities
    
    def _optimize_slot_allocation(self, slots: List[ScheduleSlot], strategy: Optional[StrategyTemplate]) -> List[ScheduleSlot]:
        """Optimize slot allocation for better performance"""
        # Sort by priority and time
        slots.sort(key=lambda x: (x.priority, x.start_time), reverse=True)
        
        # Ensure minimum gaps between tweets
        tweet_slots = [s for s in slots if s.activity_type == ActivityType.TWEET]
        tweet_slots.sort(key=lambda x: x.start_time)
        
        # Remove tweets that are too close together (less than 2 hours)
        filtered_tweet_slots = []
        last_tweet_time = None
        
        for tweet_slot in tweet_slots:
            if last_tweet_time is None or (tweet_slot.start_time - last_tweet_time).total_seconds() >= 7200:  # 2 hours
                filtered_tweet_slots.append(tweet_slot)
                last_tweet_time = tweet_slot.start_time
        
        # Remove excess tweet slots
        removed_tweet_ids = {s.slot_id for s in tweet_slots} - {s.slot_id for s in filtered_tweet_slots}
        
        # Filter out removed tweets and replace with engagement activities
        optimized_slots = []
        for slot in slots:
            if slot.slot_id in removed_tweet_ids:
                # Replace with search_engage to avoid excessive scrolling
                slot.activity_type = ActivityType.SEARCH_ENGAGE
                slot.activity_config = self._get_activity_config(ActivityType.SEARCH_ENGAGE, strategy)
                slot.priority = 3
            optimized_slots.append(slot)
        
        return optimized_slots
    
    def _create_performance_review_slot(self, date: str) -> ScheduleSlot:
        """Create performance review slot for end of day (23:30-00:30 window only)"""
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        
        # Performance review only within 30 minutes of midnight (23:30-00:30)
        # Default to 23:45 but ensure it's within the allowed window
        review_time = date_obj.replace(hour=23, minute=45, second=0, microsecond=0)
        
        # Validate timing is within 30 minutes of midnight
        midnight = date_obj.replace(hour=23, minute=30, second=0, microsecond=0)
        midnight_end = (date_obj + timedelta(days=1)).replace(hour=0, minute=30, second=0, microsecond=0)
        
        # If current time restriction applies, adjust timing
        now = datetime.now()
        if now.date() == date_obj.date():
            # If it's the same day, check if we're within the allowed window
            if now.hour == 23 and now.minute >= 30:
                # We're in the 23:30-23:59 window, use current time + 5 minutes
                review_time = now.replace(second=0, microsecond=0) + timedelta(minutes=5)
            elif now.hour == 0 and now.minute <= 30:
                # We're in the 00:00-00:30 window, use current time + 5 minutes  
                review_time = now.replace(second=0, microsecond=0) + timedelta(minutes=5)
            elif now.hour < 23 or (now.hour == 23 and now.minute < 30):
                # Too early, schedule for 23:30
                review_time = date_obj.replace(hour=23, minute=30, second=0, microsecond=0)
            else:
                # Too late, skip for today (return None handled by caller)
                review_time = None
        
        if review_time is None:
            return None
        
        return ScheduleSlot(
            slot_id=generate_slot_id(),
            start_time=review_time,
            end_time=review_time + timedelta(minutes=self.performance_review_duration),
            activity_type=ActivityType.PERFORMANCE_ANALYSIS,
            activity_config={
                "analysis_type": "daily_review",
                "metrics_focus": ["engagement", "growth", "content_performance"],
                "generate_insights": True,
                "update_strategy": True
            },
            priority=5,
            is_flexible=False,
            status=SlotStatus.SCHEDULED
        )
    
    def get_current_activity(self) -> Optional[ScheduleSlot]:
        """Get the activity that should be running now"""
        try:
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            
            # Get today's slots
            slots = self.db.get_schedule_slots(current_date)
            
            # Find slot that contains current time
            for slot in slots:
                if slot.start_time <= now <= slot.end_time and slot.status == SlotStatus.SCHEDULED:
                    return slot
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current activity: {e}")
            return None
    
    def get_next_activity(self) -> Optional[ScheduleSlot]:
        """Get the next scheduled activity"""
        try:
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            
            # Get today's slots
            slots = self.db.get_schedule_slots(current_date, status="scheduled")
            
            # Find next slot after current time
            future_slots = [s for s in slots if s.start_time > now]
            future_slots.sort(key=lambda x: x.start_time)
            
            return future_slots[0] if future_slots else None
            
        except Exception as e:
            logger.error(f"Error getting next activity: {e}")
            return None
    
    def mark_activity_started(self, slot_id: str) -> bool:
        """Mark an activity as started"""
        try:
            performance_data = {
                "started_at": datetime.now().isoformat(),
                "execution_logs": []
            }
            
            return self.db.update_slot_status(slot_id, SlotStatus.IN_PROGRESS.value, performance_data)
            
        except Exception as e:
            logger.error(f"Error marking activity started: {e}")
            return False
    
    def mark_activity_completed(self, slot_id: str, performance_data: Optional[Dict] = None) -> bool:
        """Mark an activity as completed"""
        try:
            completion_data = {
                "completed_at": datetime.now().isoformat(),
                "status": "success"
            }
            
            if performance_data:
                completion_data.update(performance_data)
            
            return self.db.update_slot_status(slot_id, SlotStatus.COMPLETED.value, completion_data)
            
        except Exception as e:
            logger.error(f"Error marking activity completed: {e}")
            return False
    
    def mark_activity_failed(self, slot_id: str, error_message: str = "") -> bool:
        """Mark an activity as failed"""
        try:
            failure_data = {
                "failed_at": datetime.now().isoformat(),
                "error_message": error_message,
                "status": "failed"
            }
            
            return self.db.update_slot_status(slot_id, SlotStatus.FAILED.value, failure_data)
            
        except Exception as e:
            logger.error(f"Error marking activity failed: {e}")
            return False
    
    def reschedule_activity(self, slot_id: str, new_start_time: datetime, reason: str = "") -> bool:
        """Reschedule an activity to a new time"""
        try:
            # Get the current slot
            slots = self.db.get_schedule_slots(new_start_time.strftime("%Y-%m-%d"))
            target_slot = None
            
            for slot in slots:
                if slot.slot_id == slot_id:
                    target_slot = slot
                    break
            
            if not target_slot:
                logger.error(f"Slot {slot_id} not found")
                return False
            
            # Update timing
            duration = target_slot.end_time - target_slot.start_time
            target_slot.start_time = new_start_time
            target_slot.end_time = new_start_time + duration
            target_slot.updated_at = datetime.now()
            
            # Add reschedule note
            if not target_slot.execution_log:
                target_slot.execution_log = []
            target_slot.execution_log.append(f"Rescheduled at {datetime.now().isoformat()}: {reason}")
            
            # Save updated slot
            return self.db.save_schedule_slot(target_slot)
            
        except Exception as e:
            logger.error(f"Error rescheduling activity: {e}")
            return False
    
    def adjust_schedule_based_on_performance(self, date: str, performance_analysis: PerformanceAnalysis) -> bool:
        """Adjust schedule based on performance analysis"""
        try:
            # Get optimization rules
            rules = self.db.get_active_optimization_rules()
            
            adjustments_made = []
            
            for rule in rules:
                if self._should_apply_rule(rule, performance_analysis):
                    adjustment = self._apply_optimization_rule(rule, date, performance_analysis)
                    if adjustment:
                        adjustments_made.append(adjustment)
            
            # Log adjustments
            if adjustments_made:
                logger.info(f"Applied {len(adjustments_made)} schedule adjustments for {date}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adjusting schedule: {e}")
            return False
    
    def _should_apply_rule(self, rule: OptimizationRule, analysis: PerformanceAnalysis) -> bool:
        """Check if an optimization rule should be applied"""
        try:
            # Simple condition evaluation (in production, use a proper expression evaluator)
            condition = rule.condition.lower()
            
            if "engagement_rate" in condition:
                engagement_rate = analysis.metrics.get("engagement_rate", 0)
                if "< 0.02" in condition and engagement_rate < 0.02:
                    return True
                if "> 0.05" in condition and engagement_rate > 0.05:
                    return True
            
            if "best_performing_hours_identified" in condition:
                return len(analysis.top_performing_content) > 0
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating rule condition: {e}")
            return False
    
    def _apply_optimization_rule(self, rule: OptimizationRule, date: str, analysis: PerformanceAnalysis) -> Optional[str]:
        """Apply an optimization rule"""
        try:
            action = rule.action.lower()
            
            if action == "increase_posting_frequency":
                return self._increase_posting_frequency(date, rule.parameters)
            elif action == "shift_posting_times":
                return self._shift_posting_times(date, rule.parameters, analysis)
            elif action == "boost_engagement_activities":
                return self._boost_engagement_activities(date, rule.parameters)
            
            return None
            
        except Exception as e:
            logger.error(f"Error applying optimization rule: {e}")
            return None
    
    def _increase_posting_frequency(self, date: str, parameters: Dict) -> Optional[str]:
        """Increase posting frequency for the next day"""
        try:
            boost_factor = parameters.get("boost_factor", 1.2)
            tomorrow = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Get tomorrow's schedule
            slots = self.db.get_schedule_slots(tomorrow)
            tweet_slots = [s for s in slots if s.activity_type == ActivityType.TWEET]
            
            # Add more tweet slots by converting some engagement slots
            engagement_slots = [s for s in slots if s.activity_type == ActivityType.SCROLL_ENGAGE]
            additional_tweets = min(2, len(engagement_slots) // 3)  # Convert up to 2 slots
            
            for i in range(additional_tweets):
                slot = engagement_slots[i]
                slot.activity_type = ActivityType.TWEET
                slot.activity_config = self._get_activity_config(ActivityType.TWEET, None)
                slot.priority = 4
                self.db.save_schedule_slot(slot)
            
            return f"Increased tweet frequency by {additional_tweets} tweets for {tomorrow}"
            
        except Exception as e:
            logger.error(f"Error increasing posting frequency: {e}")
            return None
    
    def _shift_posting_times(self, date: str, parameters: Dict, analysis: PerformanceAnalysis) -> Optional[str]:
        """Shift posting times to more optimal hours"""
        try:
            # Analyze top performing content times
            optimal_hours = []
            for content in analysis.top_performing_content:
                if "posting_hour" in content:
                    optimal_hours.append(content["posting_hour"])
            
            if not optimal_hours:
                return None
            
            # Get most common optimal hour
            from collections import Counter
            most_common_hour = Counter(optimal_hours).most_common(1)[0][0]
            
            tomorrow = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            slots = self.db.get_schedule_slots(tomorrow)
            tweet_slots = [s for s in slots if s.activity_type == ActivityType.TWEET]
            
            # Shift one tweet slot to the optimal hour
            if tweet_slots:
                target_slot = tweet_slots[0]
                new_time = target_slot.start_time.replace(hour=most_common_hour, minute=0)
                self.reschedule_activity(target_slot.slot_id, new_time, f"Shifted to optimal hour {most_common_hour}")
                
                return f"Shifted tweet to optimal hour {most_common_hour} for {tomorrow}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error shifting posting times: {e}")
            return None
    
    def _boost_engagement_activities(self, date: str, parameters: Dict) -> Optional[str]:
        """Boost engagement activities for the next day"""
        try:
            tomorrow = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            slots = self.db.get_schedule_slots(tomorrow)
            
            # Find content creation slots and convert some to engagement
            content_slots = [s for s in slots if s.activity_type == ActivityType.CONTENT_CREATION]
            conversion_count = min(1, len(content_slots))
            
            for i in range(conversion_count):
                slot = content_slots[i]
                slot.activity_type = ActivityType.SCROLL_ENGAGE
                slot.activity_config = self._get_activity_config(ActivityType.SCROLL_ENGAGE, None)
                slot.priority = 4  # High priority
                self.db.save_schedule_slot(slot)
            
            return f"Boosted engagement activities by {conversion_count} slots for {tomorrow}"
            
        except Exception as e:
            logger.error(f"Error boosting engagement activities: {e}")
            return None
    
    def get_schedule_summary(self, date: str) -> Dict[str, Any]:
        """Get a summary of the schedule for a specific date"""
        try:
            schedule = self.db.get_daily_schedule(date)
            slots = self.db.get_schedule_slots(date)
            
            if not schedule:
                return {"error": f"No schedule found for {date}"}
            
            # Calculate statistics
            activity_counts = {}
            status_counts = {}
            priority_distribution = {}
            
            for slot in slots:
                # Activity counts
                activity_type = slot.activity_type.value
                activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
                
                # Status counts
                status = slot.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Priority distribution
                priority = slot.priority
                priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
            
            completion_rate = 0
            if slots:
                completed_slots = len([s for s in slots if s.status == SlotStatus.COMPLETED])
                completion_rate = (completed_slots / len(slots)) * 100
            
            return {
                "date": date,
                "strategy_focus": schedule.strategy_focus,
                "total_slots": len(slots),
                "completion_rate": round(completion_rate, 2),
                "activity_distribution": activity_counts,
                "status_distribution": status_counts,
                "priority_distribution": priority_distribution,
                "daily_goals": schedule.daily_goals,
                "performance_targets": schedule.performance_targets
            }
            
        except Exception as e:
            logger.error(f"Error getting schedule summary: {e}")
            return {"error": str(e)}
    
    def get_week_schedule_overview(self, start_date: str) -> Dict[str, Any]:
        """Get an overview of the week's schedule"""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            week_data = {}
            
            for i in range(7):
                current_date = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
                day_summary = self.get_schedule_summary(current_date)
                week_data[current_date] = day_summary
            
            # Calculate week-level statistics
            total_activities = sum(day.get("total_slots", 0) for day in week_data.values())
            avg_completion = sum(day.get("completion_rate", 0) for day in week_data.values()) / 7
            
            return {
                "week_start": start_date,
                "week_end": (start_dt + timedelta(days=6)).strftime("%Y-%m-%d"),
                "daily_schedules": week_data,
                "week_totals": {
                    "total_activities": total_activities,
                    "average_completion_rate": round(avg_completion, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting week overview: {e}")
            return {"error": str(e)}
    
    def create_emergency_schedule(self, date: str) -> DailySchedule:
        """Create a basic emergency schedule when normal scheduling fails"""
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            
            # Create basic slots for essential activities
            essential_slots = []
            
            # Morning analytics check
            morning_time = date_obj.replace(hour=9, minute=0)
            essential_slots.append(ScheduleSlot(
                slot_id=generate_slot_id(),
                start_time=morning_time,
                end_time=morning_time + timedelta(minutes=15),
                activity_type=ActivityType.ANALYTICS_CHECK,
                activity_config={},
                priority=3,
                is_flexible=False
            ))
            
            # Mid-day tweet
            noon_time = date_obj.replace(hour=12, minute=0)
            essential_slots.append(ScheduleSlot(
                slot_id=generate_slot_id(),
                start_time=noon_time,
                end_time=noon_time + timedelta(minutes=15),
                activity_type=ActivityType.TWEET,
                activity_config={"emergency_mode": True},
                priority=5,
                is_flexible=False
            ))
            
            # Evening engagement
            evening_time = date_obj.replace(hour=18, minute=0)
            essential_slots.append(ScheduleSlot(
                slot_id=generate_slot_id(),
                start_time=evening_time,
                end_time=evening_time + timedelta(minutes=30),
                activity_type=ActivityType.SCROLL_ENGAGE,
                activity_config={"emergency_mode": True},
                priority=4,
                is_flexible=True
            ))
            
            schedule = DailySchedule(
                date=date,
                slots=essential_slots,
                strategy_focus="Emergency",
                daily_goals={"tweets": 1, "engagement_sessions": 1},
                performance_targets={"engagement_rate": 0.02}
            )
            
            # Save emergency schedule
            self.db.save_daily_schedule(schedule)
            for slot in essential_slots:
                self.db.save_schedule_slot(slot)
            
            logger.warning(f"Created emergency schedule for {date}")
            return schedule
            
        except Exception as e:
            logger.error(f"Error creating emergency schedule: {e}")
            return DailySchedule(date=date, strategy_focus="Failed", daily_goals={}, performance_targets={})

    def get_or_create_daily_schedule(self, date: str, strategy: Optional[StrategyTemplate] = None, force_recreate: bool = False) -> DailySchedule:
        """Get existing schedule or create new one with option to force recreation"""
        try:
            if force_recreate:
                # Delete existing schedule and slots
                self._delete_schedule_for_date(date)
                logger.info(f"Force recreating schedule for {date}")
            
            return self.create_daily_schedule(date, strategy)
            
        except Exception as e:
            logger.error(f"Error getting or creating daily schedule: {e}")
            return self.create_emergency_schedule(date)

    def _delete_schedule_for_date(self, date: str) -> bool:
        """Delete existing schedule and slots for a specific date"""
        try:
            # Delete existing slots
            existing_slots = self.db.get_schedule_slots(date)
            for slot in existing_slots:
                self.db.delete_schedule_slot(slot.slot_id)
            
            # Delete existing schedule
            self.db.delete_daily_schedule(date)
            
            logger.info(f"Deleted existing schedule and {len(existing_slots)} slots for {date}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting schedule for {date}: {e}")
            return False

    def update_existing_schedule(self, date: str, updates: Dict[str, Any]) -> bool:
        """Update specific aspects of an existing schedule without recreating it"""
        try:
            existing_schedule = self.db.get_daily_schedule(date)
            if not existing_schedule:
                logger.warning(f"No existing schedule found for {date} to update")
                return False
            
            # Update schedule properties
            if "strategy_focus" in updates:
                existing_schedule.strategy_focus = updates["strategy_focus"]
            
            if "daily_goals" in updates:
                existing_schedule.daily_goals.update(updates["daily_goals"])
            
            if "performance_targets" in updates:
                existing_schedule.performance_targets.update(updates["performance_targets"])
            
            # Save updated schedule
            success = self.db.save_daily_schedule(existing_schedule)
            
            if success:
                logger.info(f"Updated schedule for {date}")
            else:
                logger.error(f"Failed to update schedule for {date}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating schedule for {date}: {e}")
            return False

    def _check_slot_conflicts(self, new_slot: ScheduleSlot, existing_slots: List[ScheduleSlot]) -> bool:
        """Check if a new slot conflicts with existing slots"""
        for existing_slot in existing_slots:
            # Check for time overlap
            if (new_slot.start_time < existing_slot.end_time and 
                new_slot.end_time > existing_slot.start_time):
                return True  # Conflict found
        
        return False  # No conflicts

    def add_slot_to_schedule(self, date: str, slot: ScheduleSlot, allow_conflicts: bool = False) -> bool:
        """Add a single slot to an existing schedule with conflict checking"""
        try:
            # Get existing slots for the date
            existing_slots = self.db.get_schedule_slots(date)
            
            # Check for conflicts unless explicitly allowed
            if not allow_conflicts and self._check_slot_conflicts(slot, existing_slots):
                logger.warning(f"Slot conflicts with existing schedule: {slot.start_time} - {slot.end_time}")
                return False
            
            # Validate the slot
            if not validate_schedule_slot(slot):
                logger.error(f"Invalid slot: {slot}")
                return False
            
            # Save the slot
            success = self.db.save_schedule_slot(slot)
            
            if success:
                logger.info(f"Added slot to schedule for {date}: {slot.activity_type.value} at {slot.start_time}")
            else:
                logger.error(f"Failed to save slot for {date}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding slot to schedule: {e}")
            return False
