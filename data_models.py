#!/usr/bin/env python3
"""
Data Models for Intelligent Twitter Agent
=========================================
Comprehensive data structures for scheduling, performance tracking, and analytics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json

# Enums for type safety and consistency
class ActivityType(Enum):
    """Types of activities the agent can perform"""
    TWEET = "tweet"
    IMAGE_TWEET = "image_tweet"
    VIDEO_TWEET = "video_tweet"
    THREAD = "thread"
    SCROLL_ENGAGE = "scroll_engage"
    SEARCH_ENGAGE = "search_engage"
    REPLY = "reply"
    AUTO_REPLY = "auto_reply"
    CONTENT_CREATION = "content_creation"
    RADAR_DISCOVERY = "radar_discovery"
    ANALYTICS_CHECK = "analytics_check"
    MONITOR = "monitor"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    STRATEGY_REVIEW = "strategy_review"
    LINKEDIN_POST = "linkedin_post"
    LINKEDIN_IMAGE_POST = "linkedin_image_post"
    LINKEDIN_VIDEO_POST = "linkedin_video_post"
    LINKEDIN_THREAD = "linkedin_thread"
    LINKEDIN_ENGAGE = "linkedin_engage"
    LINKEDIN_SEARCH_ENGAGE = "linkedin_search_engage"
    LINKEDIN_CONNECT = "linkedin_connect"
    LINKEDIN_REPLY = "linkedin_reply"
    LINKEDIN_CONTENT_CREATION = "linkedin_content_creation"
    LINKEDIN_RADAR_DISCOVERY = "linkedin_radar_discovery"
    LINKEDIN_MONITOR = "linkedin_monitor"
    LINKEDIN_ANALYTICS = "linkedin_analytics"
    LINKEDIN_STRATEGY = "linkedin_strategy"
    FACEBOOK_POST = "facebook_post"
    FACEBOOK_STORY = "facebook_story"
    FACEBOOK_REEL = "facebook_reel"
    FACEBOOK_ENGAGE = "facebook_engage"
    INSTAGRAM_POST = "instagram_post"
    INSTAGRAM_STORY = "instagram_story"
    INSTAGRAM_REEL = "instagram_reel"
    INSTAGRAM_ENGAGE = "instagram_engage"

class AccountType(Enum):
    """Twitter Account Types"""
    UNVERIFIED = "unverified"
    VERIFIED = "verified" # Blue check
    GOLD = "gold" # Organization

@dataclass
class PlatformCredentials:
    """Stores both API tokens and scraped session data for a platform"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    platform_user_id: Optional[str] = None # e.g. Page ID, Twitter ID
    session_cookies: Optional[Dict] = None # For Selenium/Scraper
    is_active: bool = True
    account_type: AccountType = AccountType.UNVERIFIED
    daily_view_count: int = 0
    last_daily_reset: Optional[datetime] = None
    daily_view_limit: int = 500 # Default for unverified

@dataclass
class User:
    """User model for multi-tenant support"""
    user_id: str
    email: str
    name: str = ""
    created_at: datetime = datetime.now()
    # Keyed by platform: 'facebook', 'instagram', 'twitter', 'linkedin'
    credentials: Dict[str, PlatformCredentials] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict) # e.g. {'ui_theme': 'dark'} 
    
    # Legacy support (can be deprecated later)
    tokens: Dict[str, str] = field(default_factory=dict)


class PerformanceMetric(Enum):
    """Performance metrics to track"""
    ENGAGEMENT_RATE = "engagement_rate"
    FOLLOWER_GROWTH = "follower_growth"
    TWEET_IMPRESSIONS = "tweet_impressions"
    REACH = "reach"
    CLICK_THROUGH_RATE = "click_through_rate"
    REPLIES_RATE = "replies_rate"
    RETWEET_RATE = "retweet_rate"
    LIKE_RATE = "like_rate"

class SlotStatus(Enum):
    """Status of schedule slots"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

# Core data models
@dataclass
class EngagementData:
    """Engagement metrics for tweets and activities"""
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    impressions: int = 0
    clicks: int = 0
    profile_visits: int = 0
    follows: int = 0
    reach: int = 0
    save_rate: float = 0.0
    share_rate: float = 0.0

@dataclass
class ScheduleSlot:
    """Individual 15-minute time slot in the schedule"""
    slot_id: str
    start_time: datetime
    end_time: datetime
    activity_type: ActivityType
    activity_config: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1-5, 5 being highest
    is_flexible: bool = True
    status: SlotStatus = SlotStatus.SCHEDULED
    performance_data: Optional[Dict[str, Any]] = None
    execution_log: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class DailySchedule:
    """Complete daily schedule with all time slots"""
    date: str  # YYYY-MM-DD format
    slots: List[ScheduleSlot] = field(default_factory=list)
    strategy_focus: str = ""
    daily_goals: Dict[str, Any] = field(default_factory=dict)
    performance_targets: Dict[str, float] = field(default_factory=dict)
    completion_rate: float = 0.0
    total_activities: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class TweetPerformance:
    """Performance data for individual tweets"""
    tweet_id: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    engagement_data: EngagementData = field(default_factory=EngagementData)
    timestamp: datetime = field(default_factory=datetime.now)
    platform: str = "twitter"  # twitter, linkedin
    content_type: str = "text"  # text, image, video, poll
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    posting_time: Optional[datetime] = None
    audience_reached: int = 0
    demographics: Dict[str, Any] = field(default_factory=dict)
    sentiment_score: float = 0.0
    virality_score: float = 0.0

@dataclass
class StrategyTemplate:
    """Template for social media strategy"""
    strategy_name: str
    description: str = ""
    activity_distribution: Dict[ActivityType, float] = field(default_factory=dict)
    optimal_posting_times: List[str] = field(default_factory=list)  # ["09:00", "12:00", "15:00"]
    content_mix: Dict[str, float] = field(default_factory=dict)  # {"text": 0.4, "image": 0.4, "video": 0.2}
    target_metrics: Dict[PerformanceMetric, float] = field(default_factory=dict)
    primary_goals: List[str] = field(default_factory=list)
    engagement_strategy: Dict[str, Any] = field(default_factory=dict)
    hashtag_strategy: List[str] = field(default_factory=list)
    tone_guidelines: Dict[str, str] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class OptimizationRule:
    """Rules for optimizing schedules based on performance"""
    rule_id: str
    name: str
    description: str = ""
    condition: str = ""  # Performance condition to trigger this rule
    action: str = ""  # Action to take when condition is met
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    priority: int = 1
    success_count: int = 0
    failure_count: int = 0
    last_applied: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceAnalysis:
    """Daily performance analysis results"""
    date: str
    platform: str = "twitter"  # twitter, linkedin
    metrics: Dict[str, float] = field(default_factory=dict)
    engagement_analysis: Dict[str, Any] = field(default_factory=dict)
    top_performing_content: List[Dict[str, Any]] = field(default_factory=list)
    activity_effectiveness: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    strategy_adjustments: List[str] = field(default_factory=list)
    performance_score: float = 0.0

@dataclass
class TrendAnalysis:
    """Trend analysis over multiple days"""
    period_days: int
    start_date: str
    end_date: str
    trends: Dict[str, Any] = field(default_factory=dict)
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    trend_score: float = 0.0
    predictions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ContentPlan:
    """Content planning and scheduling"""
    plan_id: str
    title: str
    content_type: str = "text"
    topics: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    target_audience: str = ""
    optimal_times: List[str] = field(default_factory=list)
    expected_engagement: float = 0.0
    content_calendar: Dict[str, List[str]] = field(default_factory=dict)  # date -> content items
    status: str = "draft"  # draft, approved, scheduled, published
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class EngagementSession:
    """Record of engagement activities"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    activity_type: ActivityType = ActivityType.SCROLL_ENGAGE
    accounts_engaged: List[str] = field(default_factory=list)
    interactions_made: Dict[str, int] = field(default_factory=dict)  # like, reply, retweet counts
    topics_engaged: List[str] = field(default_factory=list)
    engagement_quality_score: float = 0.0
    session_notes: str = ""

@dataclass
class FollowerAnalytics:
    """Analytics about followers and audience"""
    date: str
    total_followers: int = 0
    new_followers: int = 0
    unfollowers: int = 0
    net_growth: int = 0
    follower_demographics: Dict[str, Any] = field(default_factory=dict)
    engagement_by_follower_segment: Dict[str, float] = field(default_factory=dict)
    top_follower_interests: List[str] = field(default_factory=list)
    follower_growth_rate: float = 0.0

@dataclass
class AccountAnalytics:
    """Account-level analytics from X/Twitter (x.com/i/analytics) or LinkedIn"""
    date: str
    time_range: str = "7D"  # 7D, 2W, 4W, 3M, 1Y
    platform: str = "twitter"  # twitter, linkedin
    verified_followers: int = 0
    total_followers: int = 0
    impressions: int = 0
    engagements: int = 0
    engagement_rate: float = 0.0
    profile_visits: int = 0
    replies: int = 0
    likes: int = 0
    reposts: int = 0
    bookmarks: int = 0
    shares: int = 0
    follows: int = 0
    unfollows: int = 0
    posts_count: int = 0
    replies_count: int = 0

@dataclass
class CompetitorAnalysis:
    """Analysis of competitor performance"""
    competitor_handle: str
    analysis_date: str
    follower_count: int = 0
    avg_engagement_rate: float = 0.0
    posting_frequency: float = 0.0
    top_content_types: List[str] = field(default_factory=list)
    popular_hashtags: List[str] = field(default_factory=list)
    optimal_posting_times: List[str] = field(default_factory=list)
    content_strategy_insights: List[str] = field(default_factory=list)

@dataclass
class AlertRule:
    """Rules for performance alerts"""
    rule_id: str
    name: str
    metric: str = ""
    condition: str = ""  # >, <, =, etc.
    threshold: float = 0.0
    time_window: int = 24  # hours
    alert_message: str = ""
    notification_channels: List[str] = field(default_factory=list)  # email, slack, etc.
    is_active: bool = True
    last_triggered: Optional[datetime] = None

@dataclass
class StrategyPerformance:
    """Performance tracking for strategies"""
    strategy_name: str
    period_start: str
    period_end: str
    metrics_achieved: Dict[str, float] = field(default_factory=dict)
    metrics_targets: Dict[str, float] = field(default_factory=dict)
    success_rate: float = 0.0
    roi_score: float = 0.0
    effectiveness_rating: str = "unknown"  # excellent, good, fair, poor
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CompanyConfig:
    """Configuration for company identity"""
    name: str = ""
    industry: str = ""
    mission: str = ""
    brand_colors: Dict[str, str] = field(default_factory=dict)
    twitter_username: str = ""
    company_logo_path: str = ""
    values: List[str] = field(default_factory=list)
    focus_areas: List[str] = field(default_factory=list)
    brand_voice: str = ""
    target_audience: str = ""
    key_products: List[str] = field(default_factory=list)
    competitive_advantages: List[str] = field(default_factory=list)
    location: str = ""
    contact_info: Dict[str, str] = field(default_factory=dict)
    business_model: str = ""
    core_philosophy: str = ""
    subsidiaries: List[str] = field(default_factory=list)
    partner_categories: List[str] = field(default_factory=list)

@dataclass
class PersonalityConfig:
    """Configuration for agent personality"""
    tone: str = ""
    engagement_style: str = ""
    communication_style: str = ""
    hashtag_strategy: str = ""
    content_themes: List[str] = field(default_factory=list)
    posting_frequency: str = ""

@dataclass
class SystemIdentity:
    """Master identity configuration for a tenant/user"""
    user_id: str
    company_logo_path: str = ""
    company_config: CompanyConfig = field(default_factory=CompanyConfig)
    personality_config: PersonalityConfig = field(default_factory=PersonalityConfig)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

# Helper functions for data validation and conversion
def validate_schedule_slot(slot: ScheduleSlot) -> bool:
    """Validate a schedule slot"""
    if slot.end_time <= slot.start_time:
        return False
    if slot.priority < 1 or slot.priority > 5:
        return False
    return True

def convert_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert dataclass to dictionary for MongoDB storage"""
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, list):
                result[key] = [convert_to_dict(item) if hasattr(item, '__dict__') else item for item in value]
            elif hasattr(value, '__dict__'):
                result[key] = convert_to_dict(value)
            else:
                result[key] = value
        return result
    return obj

def create_default_strategy() -> StrategyTemplate:
    """Create a default strategy template"""
    return StrategyTemplate(
        strategy_name="Balanced Growth",
        description="A balanced approach focusing on organic growth and engagement",
        activity_distribution={
            ActivityType.TWEET: 0.18,
            ActivityType.SCROLL_ENGAGE: 0.35,
            ActivityType.SEARCH_ENGAGE: 0.15,
            ActivityType.REPLY: 0.18,
            ActivityType.CONTENT_CREATION: 0.10,
            ActivityType.THREAD: 0.02,
            ActivityType.RADAR_DISCOVERY: 0.02
        },
        optimal_posting_times=["09:00", "12:00", "15:00", "18:00", "21:00"],
        content_mix={"text": 0.4, "image": 0.4, "video": 0.2},
        target_metrics={
            PerformanceMetric.ENGAGEMENT_RATE: 0.03,
            PerformanceMetric.FOLLOWER_GROWTH: 10.0,
            PerformanceMetric.TWEET_IMPRESSIONS: 1000.0
        },
        primary_goals=["artificial intelligence", "technology", "innovation", "programming"],
        engagement_strategy={
            "reply_rate": 0.15,
            "like_rate": 0.8,
            "retweet_rate": 0.1,
            "comment_style": "helpful and informative"
        },
        hashtag_strategy=["#AI", "#Tech", "#Innovation", "#Programming", "#MachineLearning"],
        tone_guidelines={
            "style": "professional yet approachable",
            "voice": "knowledgeable and helpful",
            "personality": "curious and engaging"
        }
    )

# Factory functions for common objects
def create_engagement_session(activity_type: ActivityType) -> EngagementSession:
    """Create a new engagement session"""
    from uuid import uuid4
    return EngagementSession(
        session_id=str(uuid4()),
        start_time=datetime.now(),
        activity_type=activity_type
    )

def create_performance_analysis_template(date: str) -> PerformanceAnalysis:
    """Create a template for performance analysis"""
    return PerformanceAnalysis(
        date=date,
        metrics={},
        engagement_analysis={},
        top_performing_content=[],
        activity_effectiveness={},
        insights=[],
        recommendations=[]
    )
