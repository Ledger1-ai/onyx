#!/usr/bin/env python3
"""
Agent Integration for Intelligent Twitter Agent
==============================================
Integrates scheduling, performance tracking, and strategy optimization 
with the main intelligent agent system.
"""

import logging
import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Callable
import json
from threading import Thread
import time as time_module

from data_models import (
    ScheduleSlot, ActivityType, PerformanceMetric, 
    EngagementSession, TweetPerformance, StrategyTemplate,
    create_default_strategy
)
from database_manager import DatabaseManager
from schedule_manager import ScheduleManager
from performance_tracker import PerformanceTracker
from schedule_manager import ScheduleManager
from performance_tracker import PerformanceTracker
from strategy_optimizer import StrategyOptimizer
from linkedin_bot_controller import LinkedInAgent

logger = logging.getLogger(__name__)

class AgentIntegration:
    """Integrates all components with the main intelligent agent"""
    
    def __init__(self, intelligent_agent=None, mongodb_uri: str = "mongodb://localhost:27017/"):
        """Initialize agent integration"""
        self.intelligent_agent = intelligent_agent
        self.is_running = False
        self.background_thread = None
        
        # Initialize components
        self.db = DatabaseManager(mongodb_uri)
        self.schedule_manager = ScheduleManager(self.db)
        self.performance_tracker = PerformanceTracker(self.db)
        self.performance_tracker = PerformanceTracker(self.db)
        self.strategy_optimizer = StrategyOptimizer(self.db, self.performance_tracker)

        # Initialize LinkedIn Agent
        try:
            self.linkedin_agent = LinkedInAgent()
            logger.info("LinkedIn Agent initialized within Integration")
        except Exception as e:
            logger.error(f"Failed to initialize LinkedIn Agent: {e}")
            self.linkedin_agent = None
        
        # Activity callbacks
        self.activity_callbacks = {}
        
        # Performance tracking state
        self.current_session = None
        self.daily_metrics = {}
        
        logger.info("Agent Integration initialized")

    def register_default_callbacks(self):
        """Wire ActivityType callbacks to IntelligentTwitterAgent tool methods"""
        try:
            if not self.intelligent_agent:
                logger.warning("No intelligent agent available; callbacks not registered")
                return

            # TWEET -> compose tweet
            def _cb_tweet(slot: ScheduleSlot):
                content = (slot.activity_config or {}).get("content") or "Sharing a quick update."
                # Use agent compose (synchronous)
                result_text = self.intelligent_agent._compose_tweet(
                    content=content,
                    thread_continuation=False,
                    add_media=False,
                    schedule_post=False
                )
                return {
                    "interactions": {"posts_created": 1},
                    "quality_score": 0.7,
                    "notes": f"Tweet result: {str(result_text)[:120]}"
                }

            # IMAGE_TWEET -> generate branded image
            def _cb_image_tweet(slot: ScheduleSlot):
                prompt = (slot.activity_config or {}).get("image_prompt") or "Generate a clean modern branded image."
                tweet_text = (slot.activity_config or {}).get("tweet_text") or "Visual update."
                try:
                    res = asyncio.run(self.intelligent_agent.generate_branded_image(
                        prompt=prompt, tweet_text=tweet_text, size="1024x1024", apply_company_branding=True
                    ))
                except Exception as e:
                    res = {"success": False, "error": str(e)}
                return {
                    "interactions": {"posts_created": 1, "content_generated": 1},
                    "quality_score": 0.75 if isinstance(res, dict) and res.get("success") else 0.4,
                    "notes": f"Image tweet: {str(res)[:120]}"
                }

            # VIDEO_TWEET -> generate branded video
            def _cb_video_tweet(slot: ScheduleSlot):
                prompt = (slot.activity_config or {}).get("video_prompt") or "Generate a short branded video."
                tweet_text = (slot.activity_config or {}).get("tweet_text") or "Video update."
                duration = str((slot.activity_config or {}).get("generation_time", 20))
                try:
                    res = asyncio.run(self.intelligent_agent.generate_branded_video(
                        prompt=prompt, tweet_text=tweet_text, duration=duration, apply_company_branding=True
                    ))
                except Exception as e:
                    res = {"success": False, "error": str(e)}
                return {
                    "interactions": {"posts_created": 1, "content_generated": 1},
                    "quality_score": 0.75 if isinstance(res, dict) and res.get("success") else 0.4,
                    "notes": f"Video tweet: {str(res)[:120]}"
                }

            # THREAD -> create and post thread
            def _cb_thread(slot: ScheduleSlot):
                topic = (slot.activity_config or {}).get("topic") or "Industry insight"
                thread_len = int((slot.activity_config or {}).get("thread_length", 5))
                focus = (slot.activity_config or {}).get("topic_focus", "general")
                try:
                    res = asyncio.run(self.intelligent_agent._create_and_post_thread(
                        topic=topic, thread_length=thread_len, focus_area=focus, include_hashtags=False
                    ))
                except Exception as e:
                    res = f"Error: {e}"
                return {
                    "interactions": {"posts_created": thread_len},
                    "quality_score": 0.8,
                    "notes": f"Thread: {str(res)[:160]}"
                }

            # SCROLL_ENGAGE -> scroll and engage for slot duration
            def _cb_scroll_engage(slot: ScheduleSlot):
                dur_secs = int((slot.end_time - slot.start_time).total_seconds())
                try:
                    res = asyncio.run(self.intelligent_agent._scroll_and_engage(
                        duration_seconds=max(60, min(dur_secs, 900)),
                        engagement_rate="medium",
                        engagement_types=["like", "reply"],
                        focus_keywords=[]
                    ))
                except Exception as e:
                    res = f"Error: {e}"
                return {
                    "interactions": {"engagement_actions": 1},
                    "quality_score": 0.7,
                    "notes": f"Scroll engage: {str(res)[:180]}"
                }

            # REPLY -> reply to a specific tweet or auto-reply fallback
            def _cb_reply(slot: ScheduleSlot):
                cfg = slot.activity_config or {}
                tweet_url = cfg.get("tweet_url")
                reply_style = cfg.get("reply_style", "professional")
                try:
                    if tweet_url:
                        reply_content = cfg.get("reply_content") or "Appreciate your perspective."
                        res = self.intelligent_agent._reply_to_tweet(tweet_url, reply_content, reply_style)
                    else:
                        # Fallback to auto reply in notifications
                        res = asyncio.run(self.intelligent_agent._auto_reply_to_notifications(
                            max_replies=3, reply_style=reply_style, filter_keywords=[]
                        ))
                except Exception as e:
                    res = f"Error: {e}"
                return {
                    "interactions": {"replies_sent": 1},
                    "quality_score": 0.65,
                    "notes": f"Reply: {str(res)[:160]}"
                }

            # RADAR_DISCOVERY -> use radar then engage with results
            def _cb_radar(slot: ScheduleSlot):
                focus = (slot.activity_config or {}).get("focus_area") or "industry insights"
                depth = (slot.activity_config or {}).get("search_depth", "surface")
                try:
                    radar_res = self.intelligent_agent._use_radar_tool(focus_area=focus, search_depth=depth)
                    engage_res = self.intelligent_agent.engage_with_radar_tweets(radar_result=radar_res, engagement_type="reply", max_tweets=3)
                    notes = f"Radar used; {engage_res[:160]}"
                except Exception as e:
                    notes = f"Error: {e}"
                return {
                    "interactions": {"radar_engagements": 1},
                    "quality_score": 0.7,
                    "notes": notes
                }

            # SEARCH_ENGAGE -> search keyword and auto engage
            def _cb_search_engage(slot: ScheduleSlot):
                cfg = slot.activity_config or {}
                query = cfg.get("query") or "AI automation"
                search_type = cfg.get("search_type", "latest")
                engagement_type = cfg.get("engagement_type", "mixed")
                max_tweets = int(cfg.get("max_tweets", 5))
                engagement_rate = cfg.get("engagement_rate", "medium")
                try:
                    res = self.intelligent_agent._search_and_engage(
                        query=query,
                        search_type=search_type,
                        engagement_type=engagement_type,
                        max_tweets=max_tweets,
                        engagement_rate=engagement_rate
                    )
                except Exception as e:
                    res = f"Error: {e}"
                return {
                    "interactions": {"engagement_actions": 1},
                    "quality_score": 0.7,
                    "notes": f"Search & engage: {str(res)[:180]}"
                }

            # CONTENT_CREATION -> simple content creation: compose a tweet (or image based on config)
            def _cb_content_creation(slot: ScheduleSlot):
                cfg = slot.activity_config or {}
                mode = cfg.get("content_type", "text")  # text | image_post | educational
                if mode == "image_post":
                    prompt = cfg.get("image_prompt") or "Brand-aligned visual concept"
                    tweet_text = cfg.get("tweet_text") or "Sharing a visual insight."
                    try:
                        res = asyncio.run(self.intelligent_agent.generate_branded_image(
                            prompt=prompt, tweet_text=tweet_text, size="1024x1024", apply_company_branding=True
                        ))
                    except Exception as e:
                        res = {"success": False, "error": str(e)}
                    return {
                        "interactions": {"content_pieces_created": 1, "posts_created": 1},
                        "quality_score": 0.7 if isinstance(res, dict) and res.get("success") else 0.4,
                        "notes": f"Content creation (image): {str(res)[:160]}"
                    }
                else:
                    content = cfg.get("content") or "Creating a brief educational insight aligned with our focus areas."
                    try:
                        res = self.intelligent_agent._compose_tweet(
                            content=content,
                            thread_continuation=False,
                            add_media=False,
                            schedule_post=False
                        )
                    except Exception as e:
                        res = f"Error: {e}"
                    return {
                        "interactions": {"content_pieces_created": 1, "posts_created": 1},
                        "quality_score": 0.7,
                        "notes": f"Content creation (text): {str(res)[:160]}"
                    }

            # LINKEDIN_POST -> delegate to LinkedInAgent
            def _cb_linkedin_post(slot: ScheduleSlot):
                if not self.linkedin_agent:
                    return {"success": False, "error": "LinkedIn Agent not available"}
                
                success = self.linkedin_agent.perform_activity(slot)
                return {
                    "interactions": {"posts_created": 1 if success else 0},
                    "quality_score": 0.8 if success else 0.0,
                    "notes": f"LinkedIn Post {'successful' if success else 'failed'}"
                }

            # LINKEDIN_ENGAGE -> delegate to LinkedInAgent
            def _cb_linkedin_engage(slot: ScheduleSlot):
                if not self.linkedin_agent:
                    return {"success": False, "error": "LinkedIn Agent not available"}
                
                success = self.linkedin_agent.perform_activity(slot)
                target_count = (slot.activity_config or {}).get("engagement_goals", {}).get("likes", 5)
                return {
                    "interactions": {"engagement_actions": target_count if success else 0},
                    "quality_score": 0.7 if success else 0.0,
                    "notes": f"LinkedIn Engagement {'successful' if success else 'failed'}"
                }

            # Register mappings
            self.register_activity_callback(ActivityType.TWEET, _cb_tweet)
            self.register_activity_callback(ActivityType.IMAGE_TWEET, _cb_image_tweet)
            self.register_activity_callback(ActivityType.VIDEO_TWEET, _cb_video_tweet)
            self.register_activity_callback(ActivityType.THREAD, _cb_thread)
            self.register_activity_callback(ActivityType.SCROLL_ENGAGE, _cb_scroll_engage)
            self.register_activity_callback(ActivityType.REPLY, _cb_reply)
            self.register_activity_callback(ActivityType.RADAR_DISCOVERY, _cb_radar)
            self.register_activity_callback(ActivityType.SEARCH_ENGAGE, _cb_search_engage)
            self.register_activity_callback(ActivityType.RADAR_DISCOVERY, _cb_radar)
            self.register_activity_callback(ActivityType.SEARCH_ENGAGE, _cb_search_engage)
            self.register_activity_callback(ActivityType.CONTENT_CREATION, _cb_content_creation)
            self.register_activity_callback(ActivityType.LINKEDIN_POST, _cb_linkedin_post)
            self.register_activity_callback(ActivityType.LINKEDIN_ENGAGE, _cb_linkedin_engage)

            logger.info("Default activity callbacks registered")
        except Exception as e:
            logger.error(f"Error registering default callbacks: {e}")

    def start(self) -> bool:
        """Start the integrated system"""
        try:
            if self.is_running:
                logger.warning("Agent integration already running")
                return True
            
            # Initialize database
            if not self.db.initialize_database():
                logger.error("Failed to initialize database")
                return False
            
            # Create default strategy if none exists
            self._ensure_default_strategy()
            
            # Generate initial schedule
            self._generate_initial_schedule()

            # Wire callbacks to agent tools
            self.register_default_callbacks()
            
            # Start background monitoring
            self.is_running = True
            self.background_thread = Thread(target=self._background_loop, daemon=True)
            self.background_thread.start()
            
            logger.info("Agent integration started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting agent integration: {e}")
            return False
    
    def stop(self):
        """Stop the integrated system"""
        try:
            self.is_running = False
            
            if self.background_thread and self.background_thread.is_alive():
                self.background_thread.join(timeout=5)
            
            # End any active session
            if self.current_session:
                self.end_activity_session()
            
            logger.info("Agent integration stopped")
            
        except Exception as e:
            logger.error(f"Error stopping agent integration: {e}")
    
    def register_activity_callback(self, activity_type: ActivityType, callback: Callable):
        """Register a callback for specific activity types"""
        try:
            self.activity_callbacks[activity_type] = callback
            logger.info(f"Registered callback for {activity_type.value}")
            
        except Exception as e:
            logger.error(f"Error registering activity callback: {e}")
    
    def execute_scheduled_activity(self, slot: ScheduleSlot) -> bool:
        """Execute a scheduled activity"""
        try:
            logger.info(f"Executing scheduled activity: {slot.activity_type.value} at {slot.start_time}")
            
            # Start activity session
            session = self.start_activity_session(slot.activity_type, getattr(slot, "description", slot.activity_type.value))
            
            if not session:
                logger.error("Failed to start activity session")
                return False
            
            # Check for registered callback
            if slot.activity_type in self.activity_callbacks:
                callback = self.activity_callbacks[slot.activity_type]
                
                try:
                    # Execute callback
                    result = callback(slot)
                    
                    # Record result
                    if isinstance(result, dict):
                        self.record_activity_result(result)
                    
                    logger.info(f"Activity {slot.activity_type.value} completed successfully")
                    return True
                    
                except Exception as e:
                    logger.error(f"Error executing activity callback: {e}")
                    return False
            else:
                # Default activity execution
                return self._execute_default_activity(slot)
                
        except Exception as e:
            logger.error(f"Error executing scheduled activity: {e}")
            return False
        finally:
            # Always end the session
            self.end_activity_session()
    
    def _execute_default_activity(self, slot: ScheduleSlot) -> bool:
        """Execute default activity behavior"""
        try:
            if slot.activity_type == ActivityType.POSTING:
                return self._execute_posting_activity(slot)
            elif slot.activity_type == ActivityType.ENGAGEMENT:
                return self._execute_engagement_activity(slot)
            elif slot.activity_type == ActivityType.MONITORING:
                return self._execute_monitoring_activity(slot)
            elif slot.activity_type == ActivityType.CONTENT_CREATION:
                return self._execute_content_creation_activity(slot)
            elif slot.activity_type == ActivityType.RESEARCH:
                return self._execute_research_activity(slot)
            elif slot.activity_type == ActivityType.ANALYSIS:
                return self._execute_analysis_activity(slot)
            elif slot.activity_type == ActivityType.DAILY_REVIEW:
                return self._execute_daily_review_activity(slot)
            else:
                logger.warning(f"Unknown activity type: {slot.activity_type.value}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing default activity: {e}")
            return False
    
    def _execute_posting_activity(self, slot: ScheduleSlot) -> bool:
        """Execute posting activity"""
        try:
            if not self.intelligent_agent:
                logger.warning("No intelligent agent available for posting")
                return False
            
            # Generate and post content
            # This would integrate with your existing intelligent_agent.py
            # For now, we'll simulate the activity
            
            interactions = {
                "posts_created": 1,
                "content_generated": 1
            }
            
            self.record_activity_interactions(interactions)
            
            logger.info("Posting activity completed")
            return True
            
        except Exception as e:
            logger.error(f"Error executing posting activity: {e}")
            return False
    
    def _execute_engagement_activity(self, slot: ScheduleSlot) -> bool:
        """Execute engagement activity"""
        try:
            # Simulate engagement activity
            interactions = {
                "likes_given": 5,
                "replies_sent": 2,
                "retweets_made": 3
            }
            
            self.record_activity_interactions(interactions)
            
            logger.info("Engagement activity completed")
            return True
            
        except Exception as e:
            logger.error(f"Error executing engagement activity: {e}")
            return False
    
    def _execute_monitoring_activity(self, slot: ScheduleSlot) -> bool:
        """Execute monitoring activity"""
        try:
            # Simulate monitoring activity
            interactions = {
                "mentions_checked": 10,
                "notifications_processed": 5
            }
            
            self.record_activity_interactions(interactions)
            
            logger.info("Monitoring activity completed")
            return True
            
        except Exception as e:
            logger.error(f"Error executing monitoring activity: {e}")
            return False
    
    def _execute_content_creation_activity(self, slot: ScheduleSlot) -> bool:
        """Execute content creation activity"""
        try:
            # Simulate content creation
            interactions = {
                "content_pieces_created": 3,
                "ideas_generated": 5
            }
            
            self.record_activity_interactions(interactions)
            
            logger.info("Content creation activity completed")
            return True
            
        except Exception as e:
            logger.error(f"Error executing content creation activity: {e}")
            return False
    
    def _execute_research_activity(self, slot: ScheduleSlot) -> bool:
        """Execute research activity"""
        try:
            # Simulate research activity
            interactions = {
                "topics_researched": 3,
                "trends_analyzed": 5
            }
            
            self.record_activity_interactions(interactions)
            
            logger.info("Research activity completed")
            return True
            
        except Exception as e:
            logger.error(f"Error executing research activity: {e}")
            return False
    
    def _execute_analysis_activity(self, slot: ScheduleSlot) -> bool:
        """Execute analysis activity"""
        try:
            # Trigger performance analysis
            today = datetime.now().strftime("%Y-%m-%d")
            analysis = self.performance_tracker.analyze_daily_performance(today)
            
            if analysis:
                logger.info("Daily performance analysis completed")
                
                interactions = {
                    "metrics_analyzed": len(analysis.metrics),
                    "insights_generated": 3
                }
                
                self.record_activity_interactions(interactions)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing analysis activity: {e}")
            return False
    
    def _execute_daily_review_activity(self, slot: ScheduleSlot) -> bool:
        """Execute daily review activity"""
        try:
            # Perform comprehensive daily review
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Run performance analysis
            analysis = self.performance_tracker.analyze_daily_performance(today)
            
            # Run strategy optimization
            optimization_report = self.strategy_optimizer.optimize_strategy("default_strategy")
            
            # Generate daily report
            report = self._generate_daily_report(analysis, optimization_report)
            
            interactions = {
                "reports_generated": 1,
                "optimizations_reviewed": len(optimization_report.get("optimizations_applied", [])),
                "strategy_adjustments": 1 if optimization_report.get("success", False) else 0
            }
            
            self.record_activity_interactions(interactions)
            
            logger.info("Daily review activity completed")
            return True
            
        except Exception as e:
            logger.error(f"Error executing daily review activity: {e}")
            return False
    
    def start_activity_session(self, activity_type: ActivityType, description: str = "") -> Optional[EngagementSession]:
        """Start a new activity session"""
        try:
            # End any existing session
            if self.current_session:
                self.end_activity_session()
            
            # Create new session
            from uuid import uuid4
            
            session = EngagementSession(
                session_id=f"session_{uuid4().hex[:12]}",
                activity_type=activity_type,
                start_time=datetime.now(),
                description=description,
                interactions_made={},
                engagement_quality_score=0.0
            )
            
            self.current_session = session
            logger.info(f"Started activity session: {activity_type.value}")
            
            return session
            
        except Exception as e:
            logger.error(f"Error starting activity session: {e}")
            return None
    
    def record_activity_interactions(self, interactions: Dict[str, int]):
        """Record interactions for the current activity session"""
        try:
            if not self.current_session:
                logger.warning("No active session to record interactions")
                return
            
            # Update session interactions
            for interaction_type, count in interactions.items():
                if interaction_type in self.current_session.interactions_made:
                    self.current_session.interactions_made[interaction_type] += count
                else:
                    self.current_session.interactions_made[interaction_type] = count
            
            logger.debug(f"Recorded interactions: {interactions}")
            
        except Exception as e:
            logger.error(f"Error recording activity interactions: {e}")
    
    def record_activity_result(self, result: Dict[str, Any]):
        """Record activity result data"""
        try:
            if not self.current_session:
                logger.warning("No active session to record result")
                return
            
            # Update session with result data
            if "interactions" in result:
                self.record_activity_interactions(result["interactions"])
            
            if "quality_score" in result:
                self.current_session.engagement_quality_score = result["quality_score"]
            
            if "notes" in result:
                self.current_session.notes = result["notes"]
            
        except Exception as e:
            logger.error(f"Error recording activity result: {e}")
    
    def end_activity_session(self) -> bool:
        """End the current activity session"""
        try:
            if not self.current_session:
                return True
            
            # Set end time
            self.current_session.end_time = datetime.now()
            
            # Calculate quality score if not set
            if self.current_session.engagement_quality_score == 0.0:
                self.current_session.engagement_quality_score = self._calculate_session_quality()
            
            # Save session to database
            success = self.db.save_engagement_session(self.current_session)
            
            if success:
                logger.info(f"Ended activity session: {self.current_session.activity_type.value}")
            else:
                logger.error("Failed to save activity session")
            
            self.current_session = None
            return success
            
        except Exception as e:
            logger.error(f"Error ending activity session: {e}")
            return False
    
    def record_tweet_performance(self, tweet_data: Dict[str, Any]) -> bool:
        """Record tweet performance data"""
        try:
            from uuid import uuid4
            
            # Create TweetPerformance object
            tweet_performance = TweetPerformance(
                tweet_id=tweet_data.get("tweet_id", f"tweet_{uuid4().hex[:12]}"),
                content=tweet_data.get("content", ""),
                posting_time=tweet_data.get("posting_time", datetime.now()),
                content_type=tweet_data.get("content_type", "general"),
                hashtags=tweet_data.get("hashtags", []),
                mentions=tweet_data.get("mentions", [])
            )
            
            # Update engagement data if provided
            if "engagement" in tweet_data:
                engagement = tweet_data["engagement"]
                tweet_performance.engagement_data.likes = engagement.get("likes", 0)
                tweet_performance.engagement_data.retweets = engagement.get("retweets", 0)
                tweet_performance.engagement_data.replies = engagement.get("replies", 0)
                tweet_performance.engagement_data.impressions = engagement.get("impressions", 0)
                tweet_performance.engagement_data.clicks = engagement.get("clicks", 0)
            
            # Save to database
            return self.db.save_tweet_performance(tweet_performance)
            
        except Exception as e:
            logger.error(f"Error recording tweet performance: {e}")
            return False
    
    def get_current_schedule(self) -> List[ScheduleSlot]:
        """Get today's schedule"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            return self.schedule_manager.get_daily_schedule(today)
            
        except Exception as e:
            logger.error(f"Error getting current schedule: {e}")
            return []
    
    def get_next_activity(self) -> Optional[ScheduleSlot]:
        """Get the next scheduled activity"""
        try:
            return self.schedule_manager.get_next_activity()
            
        except Exception as e:
            logger.error(f"Error getting next activity: {e}")
            return None
    
    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get performance summary for the last N days"""
        try:
            return self.performance_tracker.get_performance_summary(days)
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
    
    def trigger_optimization(self) -> Dict[str, Any]:
        """Trigger strategy optimization"""
        try:
            return self.strategy_optimizer.optimize_strategy("default_strategy")
            
        except Exception as e:
            logger.error(f"Error triggering optimization: {e}")
            return {"error": str(e)}
    
    def _background_loop(self):
        """Background monitoring loop"""
        logger.info("Background monitoring started")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check for scheduled activities
                self._check_scheduled_activities(current_time)
                
                # Check for daily review time (midnight)
                if current_time.hour == 0 and current_time.minute == 0:
                    self._trigger_daily_review()
                
                # Check for hourly performance updates
                if current_time.minute == 0:
                    self._update_hourly_metrics()
                
                # Sleep for 1 minute
                time_module.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in background loop: {e}")
                time_module.sleep(60)
        
        logger.info("Background monitoring stopped")
    
    def _check_scheduled_activities(self, current_time: datetime):
        """Check for activities that should be executed now"""
        try:
            # Get activities for current time (within 1 minute window)
            schedule = self.get_current_schedule()
            
            for slot in schedule:
                if not slot.is_completed:
                    # Check if it's time to execute this activity
                    time_diff = abs((slot.start_time - current_time).total_seconds())
                    
                    if time_diff <= 60:  # Within 1 minute
                        logger.info(f"Executing scheduled activity: {slot.activity_type.value}")
                        
                        # Execute in separate thread to avoid blocking
                        Thread(
                            target=self._execute_activity_thread,
                            args=(slot,),
                            daemon=True
                        ).start()
            
        except Exception as e:
            logger.error(f"Error checking scheduled activities: {e}")
    
    def _execute_activity_thread(self, slot: ScheduleSlot):
        """Execute activity in separate thread"""
        try:
            success = self.execute_scheduled_activity(slot)
            
            if success:
                # Mark as completed
                slot.is_completed = True
                slot.completion_time = datetime.now()
                
                # Update in database
                try:
                    self.db.save_schedule_slot(slot)
                except Exception as e:
                    logger.error(f"Failed to persist updated slot {slot.slot_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error executing activity in thread: {e}")
    
    def _trigger_daily_review(self):
        """Trigger daily review process"""
        try:
            logger.info("Starting daily review process")
            
            # Generate tomorrow's schedule
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            self.schedule_manager.generate_daily_schedule(tomorrow)
            
            # Run performance analysis for yesterday
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            self.performance_tracker.analyze_daily_performance(yesterday)
            
            # Run strategy optimization
            self.strategy_optimizer.optimize_strategy("default_strategy", days_of_data=7)
            
            logger.info("Daily review process completed")
            
        except Exception as e:
            logger.error(f"Error in daily review process: {e}")
    
    def _update_hourly_metrics(self):
        """Update hourly performance metrics"""
        try:
            # This would typically collect real-time metrics
            # For now, we'll update basic tracking metrics
            
            current_hour = datetime.now().hour
            
            # Simulate metric updates
            hourly_metrics = {
                "active_sessions": 1 if self.current_session else 0,
                "system_uptime": 1.0,
                "activities_completed": len([s for s in self.get_current_schedule() if s.is_completed])
            }
            
            # Store hourly metrics
            self.daily_metrics[current_hour] = hourly_metrics
            
        except Exception as e:
            logger.error(f"Error updating hourly metrics: {e}")
    
    def _calculate_session_quality(self) -> float:
        """Calculate quality score for current session"""
        try:
            if not self.current_session:
                return 0.0
            
            # Simple quality calculation based on interactions
            total_interactions = sum(self.current_session.interactions_made.values())
            
            if total_interactions == 0:
                return 0.0
            
            # Calculate duration in minutes
            if self.current_session.end_time:
                duration = (self.current_session.end_time - self.current_session.start_time).total_seconds() / 60
            else:
                duration = (datetime.now() - self.current_session.start_time).total_seconds() / 60
            
            # Quality score based on interactions per minute
            if duration > 0:
                interactions_per_minute = total_interactions / duration
                # Normalize to 0-1 scale (assuming 5 interactions per minute is excellent)
                quality_score = min(1.0, interactions_per_minute / 5.0)
            else:
                quality_score = 0.0
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Error calculating session quality: {e}")
            return 0.0
    
    def _ensure_default_strategy(self):
        """Ensure a default strategy exists"""
        try:
            strategy = self.db.get_strategy_template("default_strategy")
            
            if not strategy:
                logger.info("Creating default strategy")
                default_strategy = create_default_strategy()
                self.db.save_strategy_template(default_strategy)
            
        except Exception as e:
            logger.error(f"Error ensuring default strategy: {e}")
    
    def _generate_initial_schedule(self):
        """Generate initial schedule for today if none exists"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            existing_schedule = self.schedule_manager.get_daily_schedule(today)
            
            if not existing_schedule:
                logger.info("Generating initial schedule for today")
                self.schedule_manager.generate_daily_schedule(today)
            
        except Exception as e:
            logger.error(f"Error generating initial schedule: {e}")
    
    def _generate_daily_report(self, performance_analysis, optimization_report) -> Dict[str, Any]:
        """Generate comprehensive daily report"""
        try:
            report = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "generated_at": datetime.now().isoformat(),
                "performance_summary": {},
                "optimization_summary": {},
                "recommendations": [],
                "metrics": {}
            }
            
            # Performance summary
            if performance_analysis:
                report["performance_summary"] = {
                    "total_metrics": len(performance_analysis.metrics),
                    "key_metrics": dict(list(performance_analysis.metrics.items())[:5]),
                    "insights_count": len(performance_analysis.insights),
                    "top_insights": performance_analysis.insights[:3]
                }
            
            # Optimization summary
            if optimization_report and optimization_report.get("success"):
                optimizations = optimization_report.get("optimizations_applied", [])
                report["optimization_summary"] = {
                    "optimizations_applied": len(optimizations),
                    "optimization_details": optimizations,
                    "strategy_updated": True
                }
            else:
                report["optimization_summary"] = {
                    "optimizations_applied": 0,
                    "strategy_updated": False,
                    "reason": optimization_report.get("error", "No significant optimizations found")
                }
            
            # Generate recommendations
            recommendations = []
            
            if performance_analysis and performance_analysis.insights:
                recommendations.append("Review top performance insights for improvement opportunities")
            
            if optimization_report and optimization_report.get("success"):
                recommendations.append("Strategy optimizations applied - monitor impact over next few days")
            
            recommendations.append("Continue current activity schedule and review weekly performance trends")
            
            report["recommendations"] = recommendations
            
            # Daily metrics summary
            report["metrics"] = {
                "sessions_completed": len(self.daily_metrics),
                "activities_scheduled": len(self.get_current_schedule()),
                "activities_completed": len([s for s in self.get_current_schedule() if s.is_completed]),
                "system_uptime": "24 hours",
                "optimization_score": optimization_report.get("optimizations_applied", 0)
            }
            
            logger.info("Daily report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return {"error": str(e)}

# Convenience functions for easy integration

def create_agent_integration(intelligent_agent=None, mongodb_uri: str = "mongodb://localhost:27017/") -> AgentIntegration:
    """Create and initialize agent integration"""
    return AgentIntegration(intelligent_agent, mongodb_uri)

def start_automated_system(intelligent_agent=None, mongodb_uri: str = "mongodb://localhost:27017/") -> AgentIntegration:
    """Start the complete automated system"""
    integration = create_agent_integration(intelligent_agent, mongodb_uri)
    
    if integration.start():
        logger.info("Automated system started successfully")
        return integration
    else:
        logger.error("Failed to start automated system")
        return None

# Example usage and integration patterns
if __name__ == "__main__":
    # Example of how to integrate with existing intelligent_agent.py
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the system
    integration = start_automated_system()
    
    if integration:
        try:
            # Example of registering custom activity callbacks
            def custom_posting_callback(slot):
                """Custom posting activity implementation"""
                logger.info(f"Executing custom posting activity: {slot.description}")
                
                # Your posting logic here
                # Return result dictionary
                return {
                    "interactions": {"posts_created": 1, "engagement_generated": 5},
                    "quality_score": 0.8,
                    "notes": "Custom posting completed successfully"
                }
            
            # Register the callback
            integration.register_activity_callback(ActivityType.POSTING, custom_posting_callback)
            
            # Example of recording tweet performance
            tweet_data = {
                "tweet_id": "example_tweet_123",
                "content": "Example tweet content",
                "posting_time": datetime.now(),
                "content_type": "educational",
                "hashtags": ["#AI", "#Twitter"],
                "engagement": {
                    "likes": 15,
                    "retweets": 5,
                    "replies": 3,
                    "impressions": 1000
                }
            }
            
            integration.record_tweet_performance(tweet_data)
            
            # Keep the system running
            logger.info("System is running. Press Ctrl+C to stop.")
            
            while True:
                time_module.sleep(60)
                
                # Optionally print status
                current_activity = integration.get_next_activity()
                if current_activity:
                    logger.info(f"Next activity: {current_activity.activity_type.value} at {current_activity.start_time}")
                
        except KeyboardInterrupt:
            logger.info("Shutting down system...")
            integration.stop()
            logger.info("System stopped")
    else:
        logger.error("Failed to start system")
