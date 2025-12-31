import os
import json
import asyncio
import logging
import time
import random
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import threading
from dataclasses import dataclass
import re
from dateutil import parser as dateutil_parser
import subprocess
import shutil
import uuid
try:
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("MoviePy not available - video overlay/music features disabled")

from openai import AzureOpenAI
from selenium_scraper import TwitterScraper
from meta_scraper import MetaScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from click_fix import safe_click
from database_manager import DatabaseManager

# Import media generation capabilities
try:
    from social_media_generator import (
        generate_image,
        enhance_image,
        add_text_overlay,
        download_image,
        get_twitter_image_size,
        is_media_available
    )
    MEDIA_GENERATION_AVAILABLE = is_media_available()
    if MEDIA_GENERATION_AVAILABLE:
        print("[OK] Social Media Generation available - image and video generation enabled")
    else:
        print("[WARN]  Social Media Generation dependencies missing - media features disabled")
except ImportError as e:
    MEDIA_GENERATION_AVAILABLE = False
    print(f"[FAIL] Twitter media generation not available: {e}")

try:
    from tucvideo import (
        generate_message, adjust_video_prompt, generate_video_from_sora,
        upload_video, post_tweet, upload_and_tweet_with_retries
    )
    TUCVIDEO_AVAILABLE = True
    print("[OK] Tucvideo utilities available")
except ImportError:
    TUCVIDEO_AVAILABLE = False
    print("[WARN]  Tucvideo utilities not available - utility video generation disabled")



# Import social_media_generator for core image functionality
import social_media_generator

# Configuration
# Load Azure OpenAI config from config.json or environment, with sane defaults
try:
    with open('config.json', 'r') as _cfg_fh:
        _cfg = json.load(_cfg_fh)
    AZURE_OPENAI_ENDPOINT = _cfg.get("azure_openai_endpoint") or os.getenv("AZURE_OPENAI_ENDPOINT") or "https://panopticon.openai.azure.com"
    AZURE_OPENAI_KEY = _cfg.get("azure_openai_key") or os.getenv("AZURE_OPENAI_KEY") or "aefad978082243b2a79e279b203efc29"
    OPENAI_MODEL = _cfg.get("azure_openai_deployment_name") or os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-5"
except Exception:
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://panopticon.openai.azure.com")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "aefad978082243b2a79e279b203efc29")
    OPENAI_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5")

AZURE_OPENAI_VERSION = "2025-04-01-preview"  # API version

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_VERSION,
)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("AGENT_DEBUG") == "1" else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('intelligent_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Represents the current state of the agent"""
    active_mode: str = "main"
    afterlife_enabled: bool = False
    is_paused: bool = False
    pause_until: Optional[datetime] = None
    current_task: Optional[str] = None
    session_data: Dict = None
    conversation_memory: List[Dict] = None

    def __post_init__(self):
        if self.session_data is None:
            self.session_data = {
                "tweets_posted": 0,
                "replies_sent": 0,
                "accounts_discovered": 0,
                "engagement_actions": 0,
                "analytics_checks": 0,
                "start_time": datetime.now().isoformat()
            }
        
        if self.conversation_memory is None:
            self.conversation_memory = []

class IntelligentTwitterAgent:
    """An intelligent Twitter agent with comprehensive Selenium-based tool calling"""
    
    def __init__(self, username: str = None, password: str = None, email: str = None, company_config: dict = None, personality_config: dict = None):
        """Initialize the Intelligent Twitter Agent with enhanced company and personality configuration"""
        # Store login credentials for potential later use
        self.username = username
        self.password = password
        self.email = email

        # Load config early so we can honor HEADLESS_MODE/USE_PERSISTENT_PROFILE/PROFILE_DIRECTORY
        try:
            from config import Config as AppConfig  # type: ignore
            self.config = AppConfig
        except Exception:
            from types import SimpleNamespace
            # Sensible defaults if config import fails
            self.config = SimpleNamespace(
                HEADLESS_MODE=False,
                USE_PERSISTENT_PROFILE=True,
                PROFILE_DIRECTORY="browser_profiles/twitter_automation_profile",
                TWITTER_USERNAME=(os.getenv('TWITTER_USERNAME') or (company_config or {}).get('twitter_handle', '') or '')
            )

        # Lazy initialize scraper (do not start browser yet)
        self.scraper = None
        self.meta_scraper = None
        logger.info("SeleniumScraper lazy initialization configured. Browser will not launch until Afterlife Mode is enabled.")

        # Initialize MongoDB database manager
        try:
            self.db_manager = DatabaseManager()
            logger.warning("Successfully connected to MongoDB")
        except Exception as e:
            logger.warning(f"Failed to connect to MongoDB: {e}")
            self.db_manager = None
        
        # Config already loaded above; ensure self.config present
        if not hasattr(self, "config"):
            try:
                from config import Config as AppConfig  # type: ignore
                self.config = AppConfig
            except Exception:
                from types import SimpleNamespace
                self.config = SimpleNamespace(
                    HEADLESS_MODE=False,
                    USE_PERSISTENT_PROFILE=True,
                    PROFILE_DIRECTORY="browser_profiles/twitter_automation_profile",
                    TWITTER_USERNAME=(os.getenv('TWITTER_USERNAME') or (company_config or {}).get('twitter_handle', '') or '')
                )
        
        # Initialize state and memory containers early so helper methods can access them
        self.state = AgentState()
        
        # Initialize conversation memory
        self.conversation_history = []
        self.memory_limit = 40
        
        # Initialize missing constants
        self.conversation_file = "conversation_memory.json"
        self.max_conversation_memory = 40
        
        # Load existing conversation memory if available (now safe because self.state exists)
        self._load_conversation_memory()
        
        self.reply_monitor_active = False
        self.monitor_thread = None
        self.monitoring_paused = False  # Flag to pause background monitoring during operations
        self.is_running = True  # Global run flag for long-running operations
        
        # Load company configuration from config.json
        try:
            with open('config.json', 'r') as f:
                config_data = json.load(f)
                company_config = config_data.get('company_config', {})
        except FileNotFoundError:
            print("Warning: config.json not found, using default config")
            company_config = {}
        except Exception as e:
            print(f"Error loading config.json: {e}")
            company_config = {}

        self.company_config = company_config
        
        # Agent defaults from config.json, if provided
        try:
            self.agent_defaults = config_data.get('agent_defaults', {})
        except Exception:
            self.agent_defaults = {}
        
        # Personality configuration - customizable agent personality
        self.personality_config = personality_config or {
            "tone": "professional_yet_approachable",  # Options: professional, casual, technical, friendly, authoritative
            "engagement_style": "proactive_helpful",  # Options: reactive, proactive_helpful, aggressive_growth, community_focused
            "expertise_level": "industry_expert",    # Options: beginner_friendly, intermediate, industry_expert, technical_specialist
            "communication_style": "clear_concise",  # Options: verbose_detailed, clear_concise, bullet_points, storytelling
            "response_speed": "thoughtful",          # Options: immediate, quick, thoughtful, researched
            "content_focus": "educational_promotional", # Options: purely_promotional, educational_promotional, community_building, thought_leadership
            "risk_tolerance": "moderate",            # Options: conservative, moderate, aggressive, experimental
            "interaction_frequency": "active"       # Options: minimal, moderate, active, highly_active
        }
        
        # Content generation preferences based on personality
        try:
            self.content_preferences = self._setup_content_preferences()
        except Exception as e:
            logger.warning(f"Could not setup content preferences: {e}")
            # Set default content preferences if setup fails
            self.content_preferences = {
                "image_generation_enabled": False,
                "video_generation_enabled": False,
                "auto_branding": True,
                "content_types": ["product_highlights", "company_updates", "promotional_content"]
            }
        
        # Initialize agent personality and instructions with company context (depends on content_preferences)
        self.agent_instructions = self._get_agent_instructions()
        self.tools = self._define_comprehensive_tools()
        
        # Enhanced company vision for content alignment
        self.company_vision = {
            "mission": self.company_config["mission"],
            "focus_areas": self.company_config["focus_areas"],
            "values": self.company_config["values"],
            "brand_voice": self.company_config["brand_voice"]
        }
        
        # Ensure logged in before starting background monitoring
        # Ensure logged in before starting background monitoring
        # SKIP for now if scraper is not initialized (Safe Mode default)
        if self.scraper:
            try:
                if not self.scraper.ensure_logged_in():
                    logger.warning("Login required for full agent operation")
            except Exception as e:
                logger.warning(f"Could not verify login status: {e}")
        
        # Start background monitoring
        try:
            self._start_background_monitoring()
        except Exception as e:
            logger.warning(f"Could not start background monitoring: {e}")
            
        # UnifiedPublisher removed for pure Agent mode
        self.publisher = None
        
        logger.warning(f"Intelligent Twitter Agent initialized for {self.company_config['name']} with {self.personality_config['tone']} personality")
    
    def set_afterlife_mode(self, enabled: bool):
        """Enable or disable 'Afterlife Mode' (Selenium automation)"""
        mode_str = "ENABLED" if enabled else "DISABLED"
        logger.warning(f"Protocol MYTHOS: Setting Afterlife Mode to {mode_str}")
        
        if enabled:
            self.state.afterlife_enabled = True
            self.state.active_mode = "afterlife"
            # If scraper is missing, try to initialize it
            if not hasattr(self, 'scraper') or self.scraper is None:
                try:
                    logger.warning("🚀 Initializing Rogue Agent (Selenium Scraper)...")
                    headless = bool(getattr(self.config, "HEADLESS_MODE", False))
                    use_profile = bool(getattr(self.config, "USE_PERSISTENT_PROFILE", True))
                    logger.warning(f"   Headless: {headless}, Persistent Profile: {use_profile}")
                    
                    self.scraper = TwitterScraper(
                        headless=headless,
                        use_persistent_profile=use_profile
                    )
                    logger.warning("✅ Scraper instance created. Checking login status...")
                    self.scraper.ensure_logged_in()
                    logger.warning("✅ Rogue Agent ready!")
                except Exception as e:
                    logger.error(f"❌ Failed to spin up Rogue Agent: {e}")
                    import traceback
                    traceback.print_exc()
                    self.scraper = None  # Ensure it's None if failed
            else:
                logger.warning("🔄 Scraper already initialized, reusing...")
        else:
            self.state.afterlife_enabled = False
            self.state.active_mode = "safe_mode"
            # In Phase 2, we might want to close the scraper here, 
            # but for now we'll keep it alive to avoid cold-start delays
            logger.warning("Rogue Agent standing by (Safe Mode Active)")

    def _set_operation_mode(self, mode: str, intensity: str = "medium", duration: int = 0) -> str:
        """Set the agent's operation mode"""
        allowed_modes = ["main", "afterlife", "engagement", "monitoring", "content_creation", "safe_mode"]
        
        if mode not in allowed_modes:
            # Map common LLM hallucinations to closest valid mode
            if mode == "active": mode = "main"
            elif mode == "rogue": mode = "afterlife"
            else:
                return f"Invalid mode: {mode}. Allowed: {', '.join(allowed_modes)}"
        
        # Security check for Afterlife
        if mode == "afterlife":
            # Just call the public setter which handles scraper init
            self.set_afterlife_mode(True)
        else:
            self.state.active_mode = mode
            
        logger.warning(f"Operation mode set to: {mode} (Intensity: {intensity})")
        
        # If duration provided, schedule a revert (simplified for now as just logging)
        if duration > 0:
            logger.info(f"Mode {mode} will be active for {duration} minutes")
            
        return f"Operation mode successfully set to {mode}"

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent"""
        return {
            "active_mode": self.state.active_mode,
            "is_paused": self.state.is_paused,
            "pause_until": self.state.pause_until.isoformat() if self.state.pause_until else None,
            "current_task": self.state.current_task,
            "session_data": self.state.session_data,
            "monitoring_active": self.reply_monitor_active,
            "timestamp": datetime.now().isoformat(),
            "company": self.company_config.get('name')
        }

    def _get_session_status(self) -> Dict[str, Any]:
        """Internal alias for get_status"""
        return self.get_status()

    def stop(self):
        """Public alias for shutdown, used by dashboard scheduler"""
        self.shutdown()

    def shutdown(self):
        """Shutdown the agent and release resources"""
        logger.warning("Shutting down Intelligent Twitter Agent...")
        self.is_running = False
        self.reply_monitor_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            
        if self.scraper:
            try:
                self.scraper.close()
            except Exception as e:
                logger.warning(f"Error closing scraper: {e}")
        
        logger.warning("Agent shutdown complete")

    def _setup_content_preferences(self):
        """Setup content generation preferences based on personality configuration"""
        preferences = {
            "image_generation_enabled": MEDIA_GENERATION_AVAILABLE,
            "video_generation_enabled": MEDIA_GENERATION_AVAILABLE and TUCVIDEO_AVAILABLE,
            "auto_branding": True,
            "content_types": []
        }
        
        # Determine preferred content types based on personality
        if self.personality_config["content_focus"] == "educational_promotional":
            preferences["content_types"] = ["infographics", "explainer_videos", "tutorials", "industry_insights"]
        elif self.personality_config["content_focus"] == "community_building":
            preferences["content_types"] = ["behind_scenes", "team_highlights", "user_stories", "polls"]
        elif self.personality_config["content_focus"] == "thought_leadership":
            preferences["content_types"] = ["trend_analysis", "future_predictions", "industry_commentary", "research_summaries"]
        else:
            preferences["content_types"] = ["product_highlights", "company_updates", "promotional_content"]
        
        return preferences
    
    def _load_conversation_memory(self):
        """Load conversation memory from file if it exists"""
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.state.conversation_memory = data.get('conversation_memory', [])
                    logger.warning(f"Loaded {len(self.state.conversation_memory)} messages from conversation memory")
            else:
                logger.warning("No existing conversation memory found, starting fresh")
        except Exception as e:
            logger.warning(f"Could not load conversation memory: {e}")
            self.state.conversation_memory = []
    
    def _save_conversation_memory(self):
        """Save conversation memory to file"""
        try:
            memory_data = {
                'conversation_memory': self.state.conversation_memory,
                'last_updated': datetime.now().isoformat(),
                'session_info': {
                    'active_mode': self.state.active_mode,
                    'total_messages': len(self.state.conversation_memory)
                }
            }
            
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"Could not save conversation memory: {e}")
    
    def _add_to_conversation_memory(self, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation memory with automatic pruning"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.state.conversation_memory.append(message)
        
        # Prune memory if it exceeds the limit
        if len(self.state.conversation_memory) > self.max_conversation_memory:
            # Keep the most recent messages
            self.state.conversation_memory = self.state.conversation_memory[-self.max_conversation_memory:]
            logger.debug(f"Pruned conversation memory to {self.max_conversation_memory} messages")
        
        # Save to file
        self._save_conversation_memory()

    def _has_follower_been_shouted_out(self, username: str) -> bool:
        """Check if a follower has already been shouted out"""
        if not self.db_manager:
            return False
        
        try:
            # Check if there's a record using the has_follower_shoutout function from the database manager
            return self.db_manager.has_follower_shoutout(username)
        except Exception as e:
            logger.warning(f"Error checking follower shoutout status: {e}")
            return False

    def _has_reply_been_managed(self, username: str) -> bool:
        """Check if a reply has already been managed"""
        if not self.db_manager:
            return False
        
        return self.db_manager.has_reply_been_managed(username)

    def _is_our_account(self, username_or_author_text: str) -> bool:
        """Return True if the given username/author text refers to our own account (The Utility Co)."""
        try:
            text = (username_or_author_text or "").strip().lower()
            # Normalize common formats
            text = text.replace("@", "")
            # Collect configured handles
            handles = set()
            try:
                cfg_handle = getattr(getattr(self, "config", None), "TWITTER_USERNAME", "") or ""
            except Exception:
                cfg_handle = ""
            if cfg_handle:
                handles.add(cfg_handle.replace("@", "").lower())
            # Company config handle
            try:
                company_handle = (self.company_config.get("twitter_handle") or "")
            except Exception:
                company_handle = ""
            if company_handle:
                handles.add(company_handle.replace("@", "").lower())
            # Known canonical forms of The Utility Company
            handles.update({"the_utility_co", "theutilityco"})
            # Consider exact or substring match (author_info may contain display name text)
            return any(h and (text == h or h in text) for h in handles)
        except Exception:
            return False
    
    def _record_follower_shoutout(self, username: str, tweet_url: str = None) -> bool:
        """Record that a follower has been shouted out"""
        if not self.db_manager:
            logger.warning("Database manager not initialized, cannot record shoutout")
            return False
        
        try:
            logger.warning(f"Recording follower shoutout for @{username}")
            shoutout_record = {
                "username": username.lower(),
                "original_username": username,  # Keep original case
                "timestamp": datetime.now(),
                "tweet_url": tweet_url,
                "created_by": "intelligent_agent"
            }
            
            # Use save_follower_shoutout from the database manager
            self.db_manager.save_follower_shoutout(username, tweet_url)
            
            logger.warning(f"Recorded follower shoutout for @{username}")
            return True
        except Exception as e:
            logger.warning(f"Error recording follower shoutout: {e}")
            return False
    
    def _get_conversation_context(self) -> List[Dict]:
        """Get conversation history formatted for OpenAI API"""
        context_messages = []
        
        # Add system message
        context_messages.append({
            "role": "system", 
            "content": self.agent_instructions + f"\n\nCurrent session info: {json.dumps(self.get_status(), indent=2)}"
        })
        
        # Add conversation history (convert our format to OpenAI format)
        for message in self.state.conversation_memory:
            context_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        return context_messages
    
    def _get_conversation_summary(self) -> str:
        """Get a summary of recent conversation for context"""
        if not self.state.conversation_memory:
            return "No previous conversation history."
        
        recent_messages = self.state.conversation_memory[-10:]  # Last 10 messages
        summary_parts = []
        
        for msg in recent_messages:
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
            role_icon = "🤖" if msg['role'] == 'assistant' else "👤"
            content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            summary_parts.append(f"{role_icon} {timestamp}: {content_preview}")
        
        return f"Recent conversation context ({len(recent_messages)} messages):\n" + "\n".join(summary_parts)
    
    def clear_conversation_memory(self):
        """Clear all conversation memory"""
        self.state.conversation_memory = []
        try:
            if os.path.exists(self.conversation_file):
                os.remove(self.conversation_file)
            logger.warning("Conversation memory cleared")
        except Exception as e:
            logger.warning(f"Error clearing conversation memory file: {e}")
    
    def get_conversation_stats(self) -> Dict:
        """Get statistics about the conversation memory"""
        if not self.state.conversation_memory:
            return {"total_messages": 0, "user_messages": 0, "assistant_messages": 0}
        
        user_messages = len([m for m in self.state.conversation_memory if m['role'] == 'user'])
        assistant_messages = len([m for m in self.state.conversation_memory if m['role'] == 'assistant'])
        
        first_message = self.state.conversation_memory[0] if self.state.conversation_memory else None
        last_message = self.state.conversation_memory[-1] if self.state.conversation_memory else None
        
        return {
            "total_messages": len(self.state.conversation_memory),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "memory_limit": self.max_conversation_memory,
            "first_message_time": first_message['timestamp'] if first_message else None,
            "last_message_time": last_message['timestamp'] if last_message else None
        }
    
    def _get_agent_instructions(self) -> str:
        """Get comprehensive agent instructions with company and personality context"""
        
        # Build personality-specific instruction components
        tone_guidance = {
            "professional": "Maintain a formal, business-appropriate tone in all interactions.",
            "casual": "Use a relaxed, conversational tone while remaining respectful.",
            "technical": "Focus on technical accuracy and use industry-specific terminology.",
            "friendly": "Be warm, welcoming, and personable in all communications.",
            "authoritative": "Demonstrate expertise and confidence in your knowledge."
        }.get(self.personality_config["tone"], "Balance professionalism with approachability.")
        
        engagement_guidance = {
            "reactive": "Respond to mentions and interactions but avoid initiating conversations.",
            "proactive_helpful": "Actively seek opportunities to help and add value to conversations.",
            "aggressive_growth": "Prioritize growth metrics and engagement over relationship building.",
            "community_focused": "Emphasize building relationships and fostering community."
        }.get(self.personality_config["engagement_style"], "Be helpful and proactive while building community.")
        
        return f"""
You are an intelligent, autonomous Twitter agent for {self.company_config['name']}, a {self.company_config['industry']} company.

🏢 COMPANY CONTEXT:
Mission: {self.company_config['mission']}
Industry: {self.company_config['industry']}
Target Audience: {self.company_config['target_audience']}
Key Values: {', '.join(self.company_config['values'])}
Focus Areas: {', '.join(self.company_config['focus_areas'])}
Brand Voice: {self.company_config['brand_voice']}
Key Products/Services: {', '.join(self.company_config['key_products'])}

🎭 PERSONALITY CONFIGURATION:
Tone: {tone_guidance}
Engagement Style: {engagement_guidance}
Expertise Level: {self.personality_config['expertise_level']}
Communication Style: {self.personality_config['communication_style']}
Content Focus: {self.personality_config['content_focus']}

🎯 CORE OBJECTIVES:
1. Represent {self.company_config['name']} authentically and professionally
2. Build meaningful relationships within the {self.company_config['industry']} community
3. Share valuable insights about {', '.join(self.company_config['focus_areas'])}
4. Support potential clients and partners
5. Generate engaging content that aligns with company values
6. Monitor industry trends and participate in relevant conversations

🛠️ CAPABILITIES:
- Complete Twitter navigation and management
- Real-time content creation and scheduling
- Advanced analytics and performance tracking
- Community engagement and relationship building
- Image generation with company branding
- Video creation with utility company-specific overlays and music
- Automated response to mentions and direct messages
- Radar tool for discovering trending topics and opportunities
- Twitter Spaces hosting and participation

📊 CONTENT STRATEGY:
- Focus on {self.personality_config['content_focus']} content
- Generate {', '.join(self.content_preferences['content_types'])} when appropriate
- Automatically apply company branding to visual content
- Maintain {self.personality_config['risk_tolerance']} risk tolerance in messaging
- Engage at {self.personality_config['interaction_frequency']} frequency

🤖 OPERATIONAL GUIDELINES:
- Always use provided tools for Twitter interactions
- Maintain conversation context and memory
- Adapt strategy based on real-time performance data
- Prioritize authentic engagement over automation detection
- Respect rate limits and Twitter's terms of service
- Escalate complex issues or sensitive topics appropriately

🎨 CONTENT GENERATION:
When creating visual content:
- Use company branding and color scheme: {self.company_config['brand_colors']}
- Apply logo overlay from: {self.company_config['company_logo_path']}
- Ensure content aligns with brand voice and values
- Include relevant hashtags and mentions
- Optimize for engagement and reach

🔍 TWEET CONTENT ANALYSIS:
When responding to tweets, always:
1. Extract and analyze the full tweet content and context
2. Identify the tweet author's intent and sentiment
3. Consider the broader conversation thread
4. Craft responses that add genuine value
5. Maintain consistency with company values and brand voice
6. Look for opportunities to showcase expertise in {', '.join(self.company_config['focus_areas'])}

📱 ENGAGEMENT PRIORITIES:
1. Direct mentions and replies to company account
2. Industry discussions related to {', '.join(self.company_config['focus_areas'])}
3. Potential client or partner interactions
4. Trending topics relevant to {self.company_config['industry']}
5. Community building opportunities
6. Thought leadership conversations

All operations maintain browser state for seamless continuity.
All state and memory comes from real-time browser interactions, session data, and conversation history.
Always extract complete tweet content including text, media, and context for informed responses.
Use media generation capabilities strategically to enhance engagement and brand presence.
"""
    
    def _define_comprehensive_tools(self) -> List[Dict]:
        """Define all available Twitter navigation and management tools"""
        tools = [
            # === NAVIGATION TOOLS ===
            {
                "type": "function",
                "function": {
                    "name": "navigate_to_section",
                    "description": "Navigate to any section of Twitter/X",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "string", "description": "Twitter section to navigate to", 
                                       "enum": ["home", "explore", "notifications", "messages", "bookmarks", 
                                              "communities", "profile", "analytics", "radar", "creator_studio"]}
                        },
                        "required": ["section"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_twitter",
                    "description": "Search for tweets, accounts, or topics on Twitter using the standard search function. Use this for general search and engagement requests.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "search_type": {"type": "string", "description": "Type of search", 
                                           "enum": ["latest", "top", "people", "photos", "videos"]},
                            "filters": {"type": "object", "description": "Additional search filters"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_and_engage",
                    "description": "Search for tweets using Twitter search and automatically engage with them. Use this when asked to 'search and engage' or similar requests.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query to find relevant tweets"},
                            "search_type": {"type": "string", "description": "Type of search", 
                                           "enum": ["latest", "top", "people", "photos", "videos"], "default": "latest"},
                            "engagement_type": {"type": "string", "description": "Type of engagement to perform", 
                                               "enum": ["reply", "like", "retweet", "mixed"], "default": "mixed"},
                            "max_tweets": {"type": "integer", "description": "Maximum number of tweets to engage with (1-10)", "default": 5},
                            "engagement_rate": {"type": "string", "description": "How selective to be with engagement", 
                                               "enum": ["low", "medium", "high"], "default": "medium"}
                        },
                        "required": ["query"]
                    }
                }
            },
            
            # === CONTENT CREATION TOOLS ===
            {
                "type": "function",
                "function": {
                    "name": "compose_tweet",
                    "description": "Compose and post a new tweet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Tweet content"},
                            "thread_continuation": {"type": "boolean", "description": "Whether this continues a thread"},
                            "add_media": {"type": "boolean", "description": "Whether to add media"},
                            "schedule_post": {"type": "boolean", "description": "Whether to schedule the post"}
                        },
                        "required": ["content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_thread",
                    "description": "Create and post a Twitter thread with multiple connected tweets",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Main topic or theme for the thread"},
                            "thread_length": {"type": "integer", "description": "Number of tweets in the thread (2-10)", "minimum": 2, "maximum": 10},
                            "focus_area": {"type": "string", "description": "Focus area for content", "default": "general"},
                            "include_hashtags": {"type": "boolean", "description": "Whether to include relevant hashtags", "default": True}
                        },
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "schedule_twitter_space",
                    "description": "Schedule a Twitter Space for future broadcast",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Title of the Twitter Space"},
                            "description": {"type": "string", "description": "Description of the space content"},
                            "scheduled_time": {"type": "string", "description": "When to schedule the space (e.g., 'tomorrow 6pm', '2024-12-25 14:00')"},
                            "topics": {"type": "array", "items": {"type": "string"}, "description": "List of topics for the space"},
                            "co_hosts": {"type": "array", "items": {"type": "string"}, "description": "List of co-host usernames"},
                            "allow_recording": {"type": "boolean", "description": "Whether to allow recording"},
                            "language": {"type": "string", "description": "Primary language for the space"}
                        },
                        "required": ["title", "description", "scheduled_time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scroll_and_engage",
                    "description": "Scroll through Twitter feed for 60 seconds and randomly engage with posts and comments",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "duration_seconds": {
                                "type": "integer",
                                "description": "How long to scroll and engage (default 60 seconds)",
                                "default": 700
                            },
                            "engagement_rate": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "How frequently to engage with content",
                                "default": "medium"
                            },
                            "engagement_types": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["like", "reply", "follow"]},
                                "description": "Types of engagement to perform",
                                "default": ["like", "reply"]
                            },
                            "focus_keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Keywords to look for when prioritizing engagement"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "auto_reply_to_notifications",
                    "description": "Check notifications and automatically reply to mentions and replies",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "max_replies": {
                                "type": "integer",
                                "description": "Maximum number of replies to send",
                                "default": 5
                            },
                            "reply_style": {
                                "type": "string",
                                "enum": ["friendly", "professional", "casual", "helpful"],
                                "description": "Style of auto-replies",
                                "default": "helpful"
                            },
                            "filter_keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Keywords to prioritize when selecting which notifications to reply to"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reply_to_tweet",
                    "description": "Reply to a specific tweet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tweet_url": {"type": "string", "description": "URL of tweet to reply to"},
                            "reply_content": {"type": "string", "description": "Reply content"},
                            "reply_style": {"type": "string", "description": "Style of reply", 
                                           "enum": ["supportive", "insightful", "question", "professional"]}
                        },
                        "required": ["tweet_url", "reply_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "quote_tweet",
                    "description": "Quote tweet with commentary",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tweet_url": {"type": "string", "description": "URL of tweet to quote"},
                            "commentary": {"type": "string", "description": "Commentary to add"},
                            "commentary_style": {"type": "string", "description": "Style of commentary", 
                                                "enum": ["analytical", "supportive", "educational", "thought_provoking"]}
                        },
                        "required": ["tweet_url", "commentary"]
                    }
                }
            },
            
            # === ENGAGEMENT TOOLS ===
            {
                "type": "function",
                "function": {
                    "name": "engage_with_content",
                    "description": "Like, retweet, or bookmark content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tweet_url": {"type": "string", "description": "URL of tweet to engage with"},
                            "actions": {"type": "array", "items": {"type": "string"}, 
                                       "description": "Actions to perform", 
                                       "enum": ["like", "retweet", "bookmark", "share"]}
                        },
                        "required": ["tweet_url", "actions"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "follow_account",
                    "description": "Follow or unfollow a Twitter account",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string", "description": "Username to follow/unfollow"},
                            "action": {"type": "string", "description": "Action to perform", "enum": ["follow", "unfollow"]},
                            "notify": {"type": "boolean", "description": "Turn on notifications for this account"}
                        },
                        "required": ["username", "action"]
                    }
                }
            },
            
            # === ANALYTICS & PREMIUM TOOLS ===
            {
                "type": "function",
                "function": {
                    "name": "check_analytics",
                    "description": "Access Twitter Analytics dashboard for performance data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "time_period": {"type": "string", "description": "Time period for analytics", 
                                           "enum": ["28days", "7days", "1day"]},
                            "metric_focus": {"type": "string", "description": "Specific metrics to focus on", 
                                            "enum": ["impressions", "engagements", "followers", "tweets"]}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "use_radar_tool",
                    "description": "Use X Premium Radar tool to identify trending opportunities",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "focus_area": {"type": "string", "description": "Area to focus radar on (any topic or keyword)"},
                            "search_depth": {"type": "string", "description": "Depth of radar search", 
                                            "enum": ["surface", "deep", "comprehensive"]}
                        },
                        "required": ["focus_area"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "radar_and_engage",
                    "description": "Use X Business Radar tool specifically to discover trending business insights and engage with them. Only use this when specifically asked to 'use radar' or for business/industry trend analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "focus_area": {"type": "string", "description": "Area to focus radar on (any topic or keyword)"},
                            "engagement_type": {"type": "string", "description": "Type of engagement to perform", 
                                               "enum": ["reply", "like", "retweet", "mixed"]},
                            "max_tweets": {"type": "integer", "description": "Maximum number of tweets to engage with (1-10)"},
                            "search_depth": {"type": "string", "description": "Depth of radar search", 
                                            "enum": ["surface", "deep", "comprehensive"]}
                        },
                        "required": ["focus_area", "engagement_type"]
                    }
                }
            },
            
            # === DISCOVERY & MONITORING TOOLS ===
            {
                "type": "function",
                "function": {
                    "name": "discover_accounts",
                    "description": "Discover new relevant accounts to engage with",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keywords": {"type": "array", "items": {"type": "string"}, 
                                        "description": "Keywords to search for relevant accounts"},
                            "account_criteria": {"type": "object", "description": "Criteria for account selection"},
                            "max_accounts": {"type": "integer", "description": "Maximum accounts to discover"}
                        },
                        "required": ["keywords"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "monitor_notifications",
                    "description": "Monitor notifications and manage interactions (replies, shoutouts)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "notification_types": {
                                "type": "array", 
                                "items": {"type": "string", "enum": ["mentions", "replies", "likes", "retweets", "follows"]},
                                "description": "Types of notifications to monitor"
                            },
                            "auto_respond": {"type": "boolean", "description": "Whether to automatically respond to mentions/replies"},
                            "enable_follower_shoutouts": {"type": "boolean", "description": "Whether to shoutout new followers"},
                            "max_shoutouts": {"type": "integer", "description": "Maximum number of shoutouts to perform"},
                            "max_replies": {"type": "integer", "description": "Maximum number of auto-replies to perform"}
                        }
                    }
                }
            },
            
            # === STRATEGY & CONTROL TOOLS ===
            {
                "type": "function",
                "function": {
                    "name": "analyze_performance",
                    "description": "Analyze current performance and adjust strategy",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_depth": {"type": "string", "description": "Depth of analysis", 
                                              "enum": ["quick", "detailed", "comprehensive"]},
                            "adjust_strategy": {"type": "boolean", "description": "Whether to automatically adjust strategy based on findings"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_operation_mode",
                    "description": "Set the agent's operational mode",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "description": "Operational mode", 
                                    "enum": ["discovery", "engagement", "content_creation", "monitoring", "analytics", "hybrid"]},
                            "intensity": {"type": "string", "description": "Operation intensity", 
                                         "enum": ["low", "medium", "high", "adaptive"]},
                            "duration": {"type": "integer", "description": "Duration in minutes (0 for indefinite)"}
                        },
                        "required": ["mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "pause_operations",
                    "description": "Pause operations for specified duration",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "duration_minutes": {"type": "integer", "description": "Minutes to pause (0 to unpause)"},
                            "pause_reason": {"type": "string", "description": "Reason for pausing"},
                            "monitor_replies": {"type": "boolean", "description": "Continue monitoring replies while paused"}
                        },
                        "required": ["duration_minutes"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_session_status",
                    "description": "Get current session status and metrics",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            
            # === CONVERSATION MEMORY TOOLS ===
            {
                "type": "function",
                "function": {
                    "name": "get_conversation_history",
                    "description": "Get conversation history and memory statistics",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recent_count": {"type": "integer", "description": "Number of recent messages to show (default: 10)"},
                            "include_stats": {"type": "boolean", "description": "Whether to include conversation statistics"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clear_conversation_memory",
                    "description": "Clear all conversation memory (use with caution)",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "confirm": {"type": "boolean", "description": "Confirmation to clear memory"}
                        },
                        "required": ["confirm"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_conversation_history",
                    "description": "Search through conversation history for specific content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_term": {"type": "string", "description": "Term to search for in conversation history"},
                            "role_filter": {"type": "string", "description": "Filter by role", "enum": ["user", "assistant", "all"]},
                            "max_results": {"type": "integer", "description": "Maximum number of results to return"}
                        },
                        "required": ["search_term"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_and_reply_to_user",
                    "description": "Find a specific user's latest message in notifications and reply to it",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string", "description": "Username to find (with or without @)"},
                            "reply_content": {"type": "string", "description": "Content of the reply"},
                            "reply_style": {"type": "string", "description": "Style of reply", 
                                           "enum": ["supportive", "insightful", "question", "professional"]}
                        },
                        "required": ["username", "reply_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_and_tweet_media",
                    "description": "Generate a branded square media asset (image or video) and publish it in a single step, ensuring the file is attached before tweeting.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "media_type": {"type": "string", "enum": ["image", "video"], "description": "Which type of media to create and attach"},
                            "prompt": {"type": "string", "description": "Creative prompt guiding the media generation"},
                            "tweet_text": {"type": "string", "description": "Caption for the tweet"},
                            "duration": {"type": "string", "description": "Video duration in seconds (ignored for images)", "default": "5"},
                            "apply_branding": {"type": "boolean", "description": "Whether to apply company logo / overlay", "default": True}
                        },
                        "required": ["media_type", "prompt", "tweet_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "manage_notifications_automatically",
                    "description": "Automatically manage notifications including follower shout-outs and reply responses",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "enable_follower_shoutouts": {
                                "type": "boolean",
                                "description": "Whether to automatically create shout-out tweets for new followers",
                                "default": True
                            },
                            "enable_auto_replies": {
                                "type": "boolean",
                                "description": "Whether to automatically reply to mentions and replies",
                                "default": True
                            },
                            "max_shoutouts_per_session": {
                                "type": "integer",
                                "description": "Maximum number of follower shout-outs to create per session",
                                "default": 5
                            },
                            "max_auto_replies_per_session": {
                                "type": "integer",
                                "description": "Maximum number of auto-replies to send per session",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_follower_shoutout",
                    "description": "Create a personalized shout-out tweet for a new follower with custom geometric artwork",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "Username of the new follower (without @)"
                            },
                            "include_bio_analysis": {
                                "type": "boolean",
                                "description": "Whether to analyze their profile bio for personalization",
                                "default": True
                            },
                            "artwork_style": {
                                "type": "string",
                                "enum": ["geometric", "abstract", "minimalist", "bauhaus"],
                                "description": "Style of the geometric artwork to generate",
                                "default": "geometric"
                            }
                        },
                        "required": ["username"]
                    }
                }
            }
        ]
        
        # Add media generation tools if available
        if MEDIA_GENERATION_AVAILABLE:
            tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "generate_branded_image",
                        "description": "Generate an AI image with company branding and post it with a tweet",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "Detailed prompt for image generation"
                                },
                                "tweet_text": {
                                    "type": "string", 
                                    "description": "Text to accompany the image in the tweet"
                                },
                                "size": {
                                    "type": "string",
                                    "enum": ["1024x1024", "1792x1024", "1024x1792"],
                                    "description": "Image size format",
                                    "default": "1024x1024"
                                },
                                "apply_company_branding": {
                                    "type": "boolean",
                                    "description": "Whether to apply company logo overlay",
                                    "default": True
                                }
                            },
                            "required": ["prompt", "tweet_text"]
                        }
                    }
                },
                {
                    "type": "function", 
                    "function": {
                        "name": "generate_branded_video",
                        "description": "Generate an AI video with company branding and post it with a tweet",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "Detailed prompt for video generation"
                                },
                                "tweet_text": {
                                    "type": "string",
                                    "description": "Text to accompany the video in the tweet"  
                                },
                                "duration": {
                                    "type": "string",
                                    "enum": ["3", "5", "10"],
                                    "description": "Video duration in seconds",
                                    "default": "5"
                                },
                                "apply_company_branding": {
                                    "type": "boolean", 
                                    "description": "Whether to apply company logo overlay",
                                    "default": True
                                }
                            },
                            "required": ["prompt", "tweet_text"]
                        }
                    }
                }
            ])
        
        if TUCVIDEO_AVAILABLE:
            tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "create_utility_content",
                        "description": "Generate utility company-specific video content with professional framing and music",
                        "parameters": {
                            "type": "object", 
                            "properties": {
                                "content_type": {
                                    "type": "string",
                                    "enum": ["promotional", "educational", "announcement", "behind_scenes"],
                                    "description": "Type of utility company content to create"
                                },
                                "message_focus": {
                                    "type": "string",
                                    "description": "Key message or topic to focus on"
                                },
                                "include_music": {
                                    "type": "boolean",
                                    "description": "Whether to include background music",
                                    "default": True
                                },
                                "post_immediately": {
                                    "type": "boolean",
                                    "description": "Whether to post the content immediately after generation",
                                    "default": True
                                }
                            },
                            "required": ["content_type", "message_focus"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "generate_contextual_content",
                        "description": "Generate content that responds to current industry trends or conversations",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "context_tweet_url": {
                                    "type": "string",
                                    "description": "URL of tweet to respond to or build upon"
                                },
                                "response_type": {
                                    "type": "string", 
                                    "enum": ["supportive", "educational", "contrasting_viewpoint", "building_upon"],
                                    "description": "How to respond to the context"
                                },
                                "media_type": {
                                    "type": "string",
                                    "enum": ["text_only", "image", "video", "utility_video"],
                                    "description": "Type of media to include with response"
                                }
                            },
                            "required": ["context_tweet_url", "response_type", "media_type"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "monitor_facebook",
                        "description": "Monitor Facebook Stories and Reels for engagement opportunities",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "check_stories": {"type": "boolean", "description": "Whether to check Stories"},
                                "check_reels": {"type": "boolean", "description": "Whether to check Reels"}
                            },
                            "required": ["check_stories"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "monitor_instagram",
                        "description": "Monitor Instagram Stories and Reels",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "check_stories": {"type": "boolean", "description": "Whether to check Stories"},
                                "check_reels": {"type": "boolean", "description": "Whether to check Reels"}
                            },
                            "required": ["check_stories"]
                        }
                    }
                }
            ])
        
        return tools
    
    def _start_background_monitoring(self):
        """Start background thread for continuous monitoring"""
        self.reply_monitor_active = True
        self.monitor_thread = threading.Thread(target=self._background_monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.warning("Background monitoring started")
    
    def _background_monitor_loop(self):
        """Background loop for monitoring notifications and opportunities"""
        while self.reply_monitor_active:
            try:
                # Skip monitoring if paused or agent is paused
                if not self.state.is_paused and not self.monitoring_paused:
                    # Check notifications periodically
                    self._check_notifications_background()
                
                # Wait 5 minutes before next check
                time.sleep(300)
                
            except Exception as e:
                logger.warning(f"Error in background monitoring: {e}")
                time.sleep(300)
    
    def _check_notifications_background(self):
        """Background check for new notifications"""
        try:
            # Navigate to notifications
            self.scraper.driver.get("https://x.com/notifications")
            time.sleep(3)
            
            # Look for unread notifications
            unread_notifications = self.scraper.driver.find_elements(
                By.CSS_SELECTOR, '[data-testid="notification"]'
            )
            
            if unread_notifications:
                logger.warning(f"Found {len(unread_notifications)} notifications")
                # Wake up agent if paused and there are notifications
                if self.state.is_paused:
                    self.state.is_paused = False
                    self.state.pause_until = None
                    logger.warning("Agent reactivated due to new notifications")
                    
        except Exception as e:
            logger.debug(f"Background notification check error: {e}")

    async def process_command(self, command: str) -> str:
        """Process a command using the OpenAI chat completions API with function calling"""
        try:
            # Add user command to conversation memory
            self._add_to_conversation_memory("user", command, {"command_type": "user_input"})
            
            # Check if agent is paused
            paused_context = ""
            try:
                if self.state.is_paused and self.state.pause_until:
                    # Handle potential timezone mismatch
                    now = datetime.now()
                    pause_until = self.state.pause_until
                    
                    # If pause_until is timezone aware and now is not, make now aware (or vice versa)
                    if pause_until.tzinfo is not None and now.tzinfo is None:
                        # Assume local time for naive now, convert to match pause_until's timezone if possible
                        # Or simply drop tzinfo from pause_until for simple comparison
                        pause_until = pause_until.replace(tzinfo=None)
                    elif pause_until.tzinfo is None and now.tzinfo is not None:
                         now = now.replace(tzinfo=None)
                        
                    if now < pause_until:
                        paused_context = f"\n\nCRITICAL SYSTEM ALERT: The agent is currently PAUSED until {self.state.pause_until.strftime('%Y-%m-%d %H:%M:%S')}. You may answer user questions and maintain conversation, but DO NOT perform any autonomous actions, post tweets, or engage with external content unless explicitly asked to 'resume' or 'unpause' operations."
                    else:
                        self.state.is_paused = False
                        self.state.pause_until = None
            except Exception as e:
                logger.error(f"Error checking pause state: {e}")
                # Fallback to not paused if check fails
                self.state.is_paused = False
                self.state.pause_until = None
            
            # Build comprehensive system prompt with company context
            company_context = f"""
            Company: {self.company_config.get('name', 'The Utility Company')}
            Industry: {self.company_config.get('industry', 'Technology')}
            Mission: {self.company_config.get('mission', 'Democratizing manufacturing through technology')}
            Brand Voice: {self.company_config.get('brand_voice', 'professional yet approachable')}
            Target Audience: {self.company_config.get('target_audience', 'manufacturers and technology innovators')}
            Key Values: {', '.join(self.company_config.get('values', ['Innovation', 'Quality']))}
            Focus Areas: {', '.join(self.company_config.get('focus_areas', ['automation', 'tokenization', 'manufacturing']))}
            
            The Utility Company operates at the intersection of AI, Automation, and Blockchain to deliver unique asset classes. 
            Our asset classes are created by tokenizing the access, agency, and accountability of physical assets.
            
            For example, a whiskey distillery is tokenized by providing lifelong, transferable, and limited memberships 
            which are tradable on a secondary market and provide the token holder with:
            - ACCESS to the facility and visibility of their barrel 24/7/365
            - AGENCY over the barrel by being able to set various parameters (mashbill, aging duration, barrel location)
            - ACCOUNTABILITY by being able to track the barrel's location, condition, and final output
            
            The distillery gains a new revenue stream through royalties earned in the trade of assets in exchange 
            for dedicating a fixed proportion of their output for token-holding stakeholders.
            """
            
            system_prompt = f"""You are an intelligent Twitter automation agent for {self.company_config.get('name', 'The Utility Company')}.
            You are running on the {OPENAI_MODEL} model architecture, optimized for high-performance agentic workflows.

            {company_context}
            
            {paused_context}

            Your role is to:
            1. Execute social media automation tasks (posting, engaging, analyzing)
            2. Search for and engage with relevant content in our industry
            3. Create content that aligns with our mission and values
            4. Respond to notifications and mentions appropriately
            5. Analyze performance and optimize strategies
            6. Maintain our brand voice in all interactions

            Key Capabilities:
            - Content creation (tweets, threads, images, videos)
            - Smart engagement with relevant accounts and content
            - Search and discovery of industry conversations
            - Performance analytics and reporting
            - Automated responses and community management

            Brand Guidelines:
            - Voice: {self.company_config.get('brand_voice', 'professional yet approachable')}
            - Focus on: community empowerment, democratized manufacturing, tokenization benefits
            - Avoid: overly technical jargon, aggressive promotion, irrelevant content
            - Emphasize: innovation, accessibility, transparency, community ownership
            - MOST CRITICAL: WABI-SABI - Be authentic and human, not robotic. Your messages should be conversational and engaging, not overly formal or robotic.

            When executing commands:
            - Always consider our company context and mission
            - Use appropriate tools for the requested task
            - Maintain consistency with our brand voice
            - Focus on topics related to: {', '.join(self.company_config.get('focus_areas', ['automation', 'tokenization', 'manufacturing']))}
            - Target our audience: {self.company_config.get('target_audience', 'manufacturers and technology innovators')}

            Current session data: {self.state.session_data}
            Current task: {getattr(self.state, 'current_task', 'None')}
            """
            
            # Prepare messages for chat completion with conversation context
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation context (recent conversation history)
            conversation_context = self._get_conversation_context()
            # Skip the first message if it's a system message to avoid duplication
            if conversation_context and conversation_context[0].get("role") == "system":
                messages.extend(conversation_context[1:])
            else:
                messages.extend(conversation_context)
            
            # Add the current user command
            messages.append({"role": "user", "content": command})
            
            # Call OpenAI Chat Completions API with function calling
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                # temperature=0.7,
                # max_completion_tokens=2000
            )
            
            # Handle the response
            message = response.choices[0].message
            
            # Check if there are tool calls
            if message.tool_calls:
                # Process tool calls and get final response
                final_response = await self._handle_chat_tool_calls(message, messages)
                
                # Add final response to conversation memory
                self._add_to_conversation_memory("assistant", final_response, {
                    "response_type": "tool_call_response", 
                    "tools_used": [call.function.name for call in message.tool_calls],
                    "company_context_applied": True
                })
                
                return final_response
            else:
                # Direct text response
                agent_response = message.content or "No response generated."
                
                # Add response to conversation memory
                self._add_to_conversation_memory("assistant", agent_response, {
                    "response_type": "direct_response",
                    "company_context_applied": True
                })
                
                return agent_response
            
        except Exception as e:
            error_response = f"Error processing command in agent: {str(e)}"
            logger.error(error_response, exc_info=True)
            return error_response
            
            # Add error to conversation memory
            self._add_to_conversation_memory("assistant", error_response, {"response_type": "error"})
            
            return error_response
    
    async def _handle_chat_tool_calls(self, message, messages) -> str:
        """Handle tool calls from chat completion response with chaining support"""
        tool_execution_log = []
        iteration_count = 0
        max_iterations = 10  # Prevent infinite loops
        
        current_message = message
        current_messages = messages.copy()
        
        while current_message.tool_calls and iteration_count < max_iterations:
            iteration_count += 1
            
            # Add the assistant's message with tool calls to the conversation
            current_messages.append({
                "role": "assistant", 
                "content": current_message.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments
                        }
                    } for call in current_message.tool_calls
                ]
            })
            
            # Process each tool call in this iteration
            iteration_tools = []
            for tool_call in current_message.tool_calls:
                function_name = tool_call.function.name
                try:
                    # Parse arguments
                    arguments = json.loads(tool_call.function.arguments)
                    logger.warning(f"Executing tool {iteration_count}.{len(iteration_tools)+1}: {function_name} with args: {arguments}")
                    
                    # Execute the tool
                    result = await self._execute_tool(function_name, arguments)
                    
                    # Log tool execution
                    tool_log = {
                        "iteration": iteration_count,
                        "tool": function_name,
                        "arguments": arguments,
                        "result": result[:200] + "..." if len(result) > 200 else result,
                        "status": "success"
                    }
                    tool_execution_log.append(tool_log)
                    iteration_tools.append(function_name)
                    
                    # Add tool result to messages
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    logger.warning(f"Error executing tool {function_name}: {e}")
                    
                    # Log tool error
                    tool_log = {
                        "iteration": iteration_count,
                        "tool": function_name,
                        "arguments": arguments if 'arguments' in locals() else {},
                        "result": error_msg,
                        "status": "error"
                    }
                    tool_execution_log.append(tool_log)
                    
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": error_msg
                    })
            
            # Get next response from the model to see if it wants to make more tool calls
            try:
                next_response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=current_messages,
                    tools=self.tools,
                    tool_choice="auto",
                    # temperature=0.7,
                    # max_completion_tokens=1500
                )
                
                current_message = next_response.choices[0].message
                
                # If no more tool calls, we're done with the chain
                if not current_message.tool_calls:
                    break
                    
            except Exception as e:
                logger.warning(f"Error getting next response in tool chain: {e}")
                break
        
        # Generate final comprehensive response
        try:
            # Add final assistant message if it exists
            if current_message.content:
                current_messages.append({
                    "role": "assistant",
                    "content": current_message.content
                })
            
            # Create a comprehensive summary prompt
            execution_summary = f"\n\n📊 Execution Summary: {len(tool_execution_log)} tools used across {iteration_count} iterations"
            if iteration_count >= max_iterations:
                execution_summary += f" (reached max iteration limit)"
            
            final_content = current_message.content
            
            return (final_content or "Tool chain completed successfully.") + execution_summary
            
        except Exception as e:
            logger.warning(f"Error generating final response: {e}")
            
            # Fallback response with tool execution log
            fallback_response = f"Tool chain completed with {len(tool_execution_log)} operations:\n"
            for i, log in enumerate(tool_execution_log, 1):
                status_icon = "✅" if log["status"] == "success" else "❌"
                fallback_response += f"{i}. {status_icon} {log['tool']}: {log['result'][:100]}{'...' if len(log['result']) > 100 else ''}\n"
            
            return fallback_response

    async def _execute_tool(self, tool_name: str, args: Dict) -> str:
        """Execute a specific tool function"""

        # === HYBRID BRAIN SECURITY GATE ===
        # Block risky tools if not in Afterlife Mode
        # UPDATED: User requested ALL Twitter operations be treated as Risky/Rogue only due to API limits.
        risky_tools = [
            "search_and_engage", "scroll_and_engage", "find_and_reply_to_user", "engage_with_content",
            "compose_tweet", "reply_to_tweet", "quote_tweet", "follow_account", "monitor_notifications"
        ]
        
        current_mode = getattr(self.state, "active_mode", "safe_mode")
        afterlife_protected = getattr(self.state, "afterlife_enabled", False) or (current_mode == "afterlife")
        
        if tool_name in risky_tools:
            if not afterlife_protected:
                 msg = f"⛔ OPERATION BLOCKED: '{tool_name}' requires Afterlife Mode allowed. Current mode: {current_mode}."
                 logger.warning(msg)
                 return msg
            
            # If in Afterlife and Scraper not ready, try one last init?
            if afterlife_protected and not self.scraper:
                 logger.warning("Afterlife Mode active but Scraper not initialized. Attempting lazy init...")
                 self.set_afterlife_mode(True)
                 if not self.scraper:
                      return f"❌ Failed to initialize Rogue Agent for {tool_name}"

        # ==================================
        
        if tool_name == "navigate_to_section":
            return self._navigate_to_section(args.get("section"))
        
        elif tool_name == "search_twitter":
            return self._search_twitter(
                args.get("query"),
                args.get("search_type", "latest"),
                args.get("filters", {})
            )
        
        elif tool_name == "search_and_engage":
            return self._search_and_engage(
                args.get("query"),
                args.get("search_type", "latest"),
                args.get("engagement_type", "mixed"),
                args.get("max_tweets", 5),
                self._get_effective_engagement_rate(args.get("engagement_rate"))
            )
        
        elif tool_name == "compose_tweet":
            return await self._compose_tweet(
                content=args.get("content"),
                thread_continuation=args.get("thread_continuation", False),
                add_media=args.get("add_media", False),
                schedule_post=args.get("schedule_post", False)
            )
        
        elif tool_name == "create_thread":
            return await self._create_and_post_thread(
                topic=args.get("topic"),
                thread_length=args.get("thread_length", 5),
                focus_area=args.get("focus_area", "general"),
                include_hashtags=args.get("include_hashtags", True)
            )
        
        elif tool_name == "reply_to_tweet":
            return self._reply_to_tweet(
                args.get("tweet_url"),
                args.get("reply_content"),
                args.get("reply_style", "professional")
            )
        
        elif tool_name == "quote_tweet":
            return self._quote_tweet(
                args.get("tweet_url"),
                args.get("commentary"),
                args.get("commentary_style", "analytical")
            )
        
        elif tool_name == "engage_with_content":
            return self._engage_with_content(
                args.get("tweet_url"),
                args.get("actions", [])
            )
        
        elif tool_name == "follow_account":
            return self._follow_account(
                args.get("username"),
                args.get("action"),
                args.get("notify", False)
            )
        
        elif tool_name == "check_analytics":
            return self._check_analytics(
                args.get("time_period", "7days"),
                args.get("metric_focus", "engagements")
            )
        
        elif tool_name == "use_radar_tool":
            return self._use_radar_tool(
                args.get("focus_area"),
                args.get("search_depth", "surface")
            )
        
        elif tool_name == "radar_and_engage":
            return self._radar_and_engage(
                args.get("focus_area"),
                args.get("engagement_type", "reply"),
                args.get("max_tweets", 3),
                args.get("search_depth", "surface")
            )
        
        elif tool_name == "discover_accounts":
            return self._discover_accounts(
                args.get("keywords", []),
                args.get("account_criteria", {}),
                args.get("max_accounts", 10)
            )
        
        elif tool_name == "monitor_notifications":
            return self._monitor_notifications(
                args.get("notification_types", ["mentions", "replies"]),
                args.get("auto_respond", False),
                enable_shoutouts=args.get("enable_follower_shoutouts", False),
                max_shoutouts=args.get("max_shoutouts", 0),
                max_replies=args.get("max_replies", 0)
            )
        
        elif tool_name == "analyze_performance":
            return self._analyze_performance(
                args.get("analysis_depth", "quick"),
                args.get("adjust_strategy", True)
            )
        
        elif tool_name == "set_operation_mode":
            return self._set_operation_mode(
                args.get("mode"),
                args.get("intensity", "medium"),
                args.get("duration", 0)
            )
        
        elif tool_name == "pause_operations":
            return self._pause_operations(
                args.get("duration_minutes"),
                args.get("pause_reason", "Manual pause"),
                args.get("monitor_replies", True)
            )
        
        elif tool_name == "get_session_status":
            return self._get_session_status()
        
        elif tool_name == "get_conversation_history":
            return self._get_conversation_history(
                args.get("recent_count", 10),
                args.get("include_stats", True)
            )
        
        elif tool_name == "clear_conversation_memory":
            return self._clear_conversation_memory(
                args.get("confirm", False)
            )
        
        elif tool_name == "search_conversation_history":
            return self._search_conversation_history(
                args.get("search_term"),
                args.get("role_filter", "all"),
                args.get("max_results", 10)
            )
        
        elif tool_name == "monitor_facebook":
            if not self.scraper: # MetaScraper might not be initialized if scraper is None? No, independent.
                pass 
            # Lazy init MetaScraper
            if not self.meta_scraper:
                self.meta_scraper = MetaScraper(headless=False)
            
            results = []
            if args.get("check_stories"):
                results.append(self.meta_scraper.get_facebook_stories())
            if args.get("check_reels"):
                results.append(self.meta_scraper.get_facebook_reels())
            
            return "\n".join(results) if results else "Checked Facebook (No specific action)"

        elif tool_name == "monitor_instagram":
            # Lazy init MetaScraper
            if not self.meta_scraper:
                self.meta_scraper = MetaScraper(headless=False)
                
            results = []
            if args.get("check_stories"):
                results.append(self.meta_scraper.get_instagram_stories())
            if args.get("check_reels"):
                results.append(self.meta_scraper.get_instagram_reels())
                
            return "\n".join(results) if results else "Checked Instagram (No specific action)"
        
        elif tool_name == "find_and_reply_to_user":
            return self._find_and_reply_to_user(
                args.get("username"),
                args.get("reply_content"),
                args.get("reply_style", "professional")
            )
        
        elif tool_name == "schedule_twitter_space":
            return self._schedule_twitter_space(
                title=args.get("title"),
                description=args.get("description", ""),
                scheduled_time=args.get("scheduled_time"),
                topics=args.get("topics", []),
                co_hosts=args.get("co_hosts", []),
                allow_recording=args.get("allow_recording", True),
                language=args.get("language", "English")
            )
        
        elif tool_name == "scroll_and_engage":
            # Prevent running scroll_and_engage when a prioritized task is active
            try:
                active = getattr(self.state, "current_task", None)
            except Exception:
                active = None
            if active in ("search_and_engage", "radar_and_engage", "create_thread"):
                return f"Scroll-and-engage suppressed: prioritized task currently active ({active})."
            return await self._scroll_and_engage(
                duration_seconds=args.get("duration_seconds", 600),
                engagement_rate=args.get("engagement_rate", "medium"),
                engagement_types=args.get("engagement_types", ["like", "reply"]),
                focus_keywords=args.get("focus_keywords", [])
            )
        
        elif tool_name == "auto_reply_to_notifications":
            return await self._auto_reply_to_notifications(
                max_replies=args.get("max_replies", 5),
                reply_style=args.get("reply_style", "helpful"),
                filter_keywords=args.get("filter_keywords", [])
            )
        
        elif tool_name == "generate_and_tweet_media":
            return await self._generate_and_tweet_media(
                media_type=args.get("media_type"),
                prompt=args.get("prompt"),
                tweet_text=args.get("tweet_text"),
                duration=args.get("duration", "5"),
                apply_branding=args.get("apply_branding", True)
            )
        
        elif tool_name == "manage_notifications_automatically":
            return await self._manage_notifications_automatically(
                enable_follower_shoutouts=args.get("enable_follower_shoutouts", True),
                enable_auto_replies=args.get("enable_auto_replies", True),
                max_shoutouts_per_session=args.get("max_shoutouts_per_session", 3),
                max_auto_replies_per_session=args.get("max_auto_replies_per_session", 10)
            )
        
        elif tool_name == "create_follower_shoutout":
            return await self._create_follower_shoutout(
                username=args.get("username"),
                include_bio_analysis=args.get("include_bio_analysis", True),
                artwork_style=args.get("artwork_style", "geometric")
            )
        
        else:
            return f"Unknown tool: {tool_name}"
        
    async def _manage_notifications_automatically(self, enable_follower_shoutouts: bool, enable_auto_replies: bool, max_shoutouts_per_session: int, max_auto_replies_per_session: int) -> str:
        """Automatically manage notifications including follower shout-outs and reply responses"""
        try:
            logger.warning("Starting automatic notification management with enhanced stale element handling")
            results = []
            
            # Navigate to notifications with retry
            max_retries = 3
            for attempt in range(max_retries):
                logger.warning(f"Attempt {attempt+1} of {max_retries} to load notifications page")
                try:
                    self.scraper.driver.get("https://x.com/notifications")
                    time.sleep(4)
                    
                    # Wait for page to load completely
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    WebDriverWait(self.scraper.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]'))
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        return f"Failed to load notifications page after {max_retries} attempts: {str(e)}"
                    time.sleep(2)
            
            follower_shoutouts_created = 0
            auto_replies_sent = 0
            processed_notifications = []
            skipped_existing_shoutouts = 0
            
            # Process notifications with fresh element finding for each iteration
            for notification_index in range(20):  # Process first 20 notifications
                logger.warning(f"Processing notification {notification_index+1} of 20")
                try:
                    # Refresh elements each time to avoid stale references
                    notification_elements = self.scraper.driver.find_elements(
                        By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]'
                    )
                    
                    if notification_index >= len(notification_elements):
                        break  # No more notifications
                    
                    # Get fresh element reference
                    element = notification_elements[notification_index]
                    
                    # Extract text with retry
                    notification_text = ""
                    for text_attempt in range(3):
                        try:
                            notification_text = element.text.lower()
                            logger.warning(f"Extracted text from notification {notification_index}: {notification_text}")
                            break
                        except Exception as e:
                            if text_attempt < 2:
                                # Re-find element
                                notification_elements = self.scraper.driver.find_elements(
                                    By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]'
                                )
                                if notification_index < len(notification_elements):
                                    element = notification_elements[notification_index]
                                time.sleep(1)
                            else:
                                logger.warning(f"Failed to extract text from notification {notification_index}: {e}")
                                break
                    
                    if not notification_text:
                        continue
                    
                    # Detect new followers
                    if enable_follower_shoutouts and follower_shoutouts_created < max_shoutouts_per_session:
                        if any(indicator in notification_text for indicator in ['followed you', 'is now following you', 'started following', 'follow']):
                            username = self._extract_username_from_notification_robust(notification_index)
                            if username:
                                # Check if we've already shouted out this follower
                                if self._has_follower_been_shouted_out(username):
                                    print(f"Skipped @{username} - already shouted out")
                                    skipped_existing_shoutouts += 1
                                    results.append(f"Skipped @{username} - already shouted out")
                                else:
                                    # Create follower shout-out
                                    try:
                                        shoutout_result = await self._create_follower_shoutout(username, True, "geometric")
                                        print(f"Shoutout result: {shoutout_result}")
                                        if "successfully" in shoutout_result.lower():
                                            print(f"Shoutout created for @{username}")
                                            follower_shoutouts_created += 1
                                            results.append(f"Created shout-out for @{username}")
                                    except Exception as shoutout_error:
                                        logger.warning(f"Error creating shoutout for @{username}: {shoutout_error}")
                                        results.append(f"Failed to create shoutout for @{username}: {str(shoutout_error)}")
                    
                    # Detect replies and mentions
                    if enable_auto_replies and auto_replies_sent < max_auto_replies_per_session:
                        if any(indicator in notification_text for indicator in ['replied to you', 'mentioned you', 'quote', 'replying to']):
                            tweet_url = self._extract_tweet_url_robust(notification_index)
                            username = self._extract_username_from_notification_robust(notification_index)
                            # Safeguard: never reply to our own account directly
                            if self._is_our_account(username or ""):
                                logger.warning("Skipping auto-reply: notification authored by our own account")
                                continue
                            if tweet_url and tweet_url != "URL not found":
                                try:
                                    # Check if reply has already been managed
                                    if self.db_manager.has_reply_been_managed(username, tweet_url):
                                        logger.warning(f"Skipping @{username} - reply already managed")
                                        results.append(f"Skipped @{username} - reply already managed")
                                        continue
                                        
                                        # Extract context and generate reply
                                        self.scraper.driver.get(tweet_url)
                                        time.sleep(3)
                                        
                                        tweet_content = ""
                                        try:
                                            WebDriverWait(self.scraper.driver, 10).until(
                                                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="tweetText"]'))
                                            )
                                            tweet_text_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
                                            if tweet_text_elements:
                                                tweet_content = tweet_text_elements[0].text
                                        except Exception as content_error:
                                            logger.warning(f"Could not extract tweet content: {content_error}")
                                        
                                        if tweet_content:
                                            # Let _reply_to_tweet generate contextual vision reply when available
                                            reply_result = self._reply_to_tweet(tweet_url, "", "helpful")
                                            
                                            if "successfully" in reply_result.lower():
                                                auto_replies_sent += 1
                                                results.append(f"Auto-replied to notification: {tweet_url[:50]}...")
                                                # Record the reply in database
                                                self.db_manager.save_reply_management(username, tweet_url)
                                        
                                        # Return to notifications with wait
                                        self.scraper.driver.get("https://x.com/notifications")
                                        WebDriverWait(self.scraper.driver, 10).until(
                                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]'))
                                        )
                                        time.sleep(2)
                                        
                                except Exception as reply_error:
                                    logger.warning(f"Error processing reply for notification {notification_index}: {reply_error}")
                                    results.append(f"Failed to process reply: {str(reply_error)}")
                                    # Ensure we're back on notifications page
                                    try:
                                        self.scraper.driver.get("https://x.com/notifications")
                                        time.sleep(3)
                                    except:
                                        pass
                    
                    processed_notifications.append(notification_index)
                    
                    # Small delay between notifications to prevent overwhelming the system
                    time.sleep(1)
                
                except Exception as e:
                    logger.warning(f"Error processing notification {notification_index}: {e}")
                    continue
            
            summary = f"""Automatic notification management completed:
            - Follower shout-outs created: {follower_shoutouts_created}/{max_shoutouts_per_session}
            - Skipped existing shout-outs: {skipped_existing_shoutouts}
            - Auto-replies sent: {auto_replies_sent}/{max_auto_replies_per_session}
            - Total notifications processed: {len(processed_notifications)}
            
            Details:
            {chr(10).join(results) if results else 'No actions taken'}"""

            logger.warning(f"Automatic notification management summary: {summary}")
            return summary
            
        except Exception as e:
            return f"Error in automatic notification management: {str(e)}"

    def _extract_username_from_notification_robust(self, notification_index: int) -> str:
        """Extract username from notification with robust error handling"""
        try:
            for attempt in range(3):
                try:
                    # Get fresh element reference
                    notification_elements = self.scraper.driver.find_elements(
                        By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]'
                    )
                    
                    if notification_index >= len(notification_elements):
                        return None
                    
                    element = notification_elements[notification_index]
                    
                    # Extract username from href attributes
                    username_elements = element.find_elements(By.CSS_SELECTOR, '[href^="/"]')
                    for username_elem in username_elements:
                        href = username_elem.get_attribute('href')
                        if href and href.count('/') >= 3:
                            username = href.split('/')[-1]
                            if username and not username.startswith('status') and not username.startswith('i'):
                                return username
                    return None
                    
                except Exception as e:
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    else:
                        logger.warning(f"Failed to extract username from notification {notification_index}: {e}")
                        return None
        except Exception as e:
            logger.warning(f"Error in robust username extraction: {e}")
            return None

    def _extract_tweet_url_robust(self, notification_index: int) -> str:
        """Extract tweet URL from notification with robust error handling"""
        try:
            original_url = self.scraper.driver.current_url
            
            for attempt in range(3):
                try:
                    # Get fresh element reference
                    notification_elements = self.scraper.driver.find_elements(
                        By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]'
                    )
                    
                    if notification_index >= len(notification_elements):
                        return "URL not found"
                    
                    element = notification_elements[notification_index]
                    
                    # Try to find a direct link first
                    link_elements = element.find_elements(By.CSS_SELECTOR, 'a[href*="/status/"]')
                    if link_elements:
                        href = link_elements[0].get_attribute('href')
                        if href and '/status/' in href:
                            return href.split('?')[0]  # Remove query parameters
                    
                    # Fallback: try clicking approach with better error handling
                    try:
                        # Scroll element into view
                        self.scraper.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(1)
                        
                        # Store current window handles
                        windows_before = self.scraper.driver.window_handles.copy()
                        
                        # Click the element
                        self.scraper.driver.execute_script("arguments[0].click();", element)
                        time.sleep(3)
                        
                        # Check for new window or URL change
                        if len(self.scraper.driver.window_handles) > len(windows_before):
                            # New window opened
                            new_window = [h for h in self.scraper.driver.window_handles if h not in windows_before][0]
                            self.scraper.driver.switch_to.window(new_window)
                            
                            current_url = self.scraper.driver.current_url
                            if '/status/' in current_url:
                                tweet_url = current_url.split('?')[0]
                                self.scraper.driver.close()
                                self.scraper.driver.switch_to.window(windows_before[0])
                                return tweet_url
                            else:
                                self.scraper.driver.close()
                                self.scraper.driver.switch_to.window(windows_before[0])
                        
                        elif '/status/' in self.scraper.driver.current_url:
                            # Same window navigation
                            tweet_url = self.scraper.driver.current_url.split('?')[0]
                            self.scraper.driver.back()
                            time.sleep(2)
                            return tweet_url
                        
                        # Navigate back to original page
                        if self.scraper.driver.current_url != original_url:
                            self.scraper.driver.get(original_url)
                            time.sleep(2)
                            
                    except Exception as click_error:
                        logger.warning(f"Click method failed for notification {notification_index}: {click_error}")
                        # Ensure we're back on the right page
                        if self.scraper.driver.current_url != original_url:
                            self.scraper.driver.get(original_url)
                            time.sleep(2)
                    
                    return "URL not found"
                    
                except Exception as e:
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    else:
                        logger.warning(f"Failed to extract URL from notification {notification_index}: {e}")
                        return "URL not found"
                        
        except Exception as e:
            logger.warning(f"Error in robust URL extraction: {e}")
            return "URL not found"

    
    async def _create_follower_shoutout(self, username: str, include_bio_analysis: bool, artwork_style: str) -> str:
        """Create a personalized shout-out tweet for a new follower with custom geometric artwork"""
        original_monitoring_state = self.monitoring_paused
        try:
            logger.warning(f"Creating follower shout-out for @{username}")

            # Check if the user is already in the database using the _has_follower_been_shouted_out function
            if self._has_follower_been_shouted_out(username):
                logger.warning(f"User @{username} already exists in the database, skipping...")
                return f"User @{username} already exists in the database, skipping..."  
            
            # Navigate to user's profile to get bio
            user_bio = ""
            if include_bio_analysis:
                try:
                    self.scraper.driver.get(f"https://x.com/{username}")
                    time.sleep(3)
                    
                    # Extract bio
                    bio_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR, '[data-testid="UserDescription"]')
                    if bio_elements:
                        user_bio = bio_elements[0].text
                        logger.warning(f"Extracted bio for @{username}: {user_bio[:100]}...")
                except Exception as e:
                    logger.warning(f"Could not extract bio for @{username}: {e}")
            
            # Generate personalized welcome message using Azure OpenAI
            welcome_message = await self._generate_personalized_welcome_message(username, user_bio)
            
            # Generate geometric artwork
            artwork_prompt = self._create_geometric_artwork_prompt(artwork_style)
            
            # Generate the image
            image_result = await self._generate_geometric_welcome_image(artwork_prompt, welcome_message)
            if not image_result or not image_result.get("success"):
                return f"Failed to generate artwork for @{username}: {image_result.get('error', 'Unknown error') if isinstance(image_result, dict) else 'Unknown error'}"

            media_path = image_result.get("file_path")
            if not media_path:
                return f"Failed to generate artwork for @{username}: Missing file path"

            # Create the shout-out tweet with image
            tweet_result = await self._post_tweet_with_media(welcome_message, media_path)
            logger.warning(f"Tweet result: {tweet_result}")

            if isinstance(tweet_result, dict) and tweet_result.get("success"):
                tweet_url = tweet_result.get("tweet_url")
                # Record the shoutout in database once, with tweet URL if available
                self._record_follower_shoutout(username, tweet_url=tweet_url)
                logger.warning(f"Successfully created follower shout-out for @{username} with personalized message and geometric artwork")
                return f"Successfully created follower shout-out for @{username} with personalized message and geometric artwork"
            else:
                return f"Failed to post shout-out tweet for @{username}: {tweet_result.get('error', 'Unknown error') if isinstance(tweet_result, dict) else str(tweet_result)}"
            
        except Exception as e:
            return f"Error creating follower shout-out for @{username}: {str(e)}"
        finally:
            # Always restore monitoring state
            self.monitoring_paused = original_monitoring_state
            logger.warning("Background monitoring restored")
    
    async def _generate_personalized_welcome_message(self, username: str, user_bio: str) -> str:
        """Generate a personalized welcome message using Azure OpenAI based on user's bio"""
        try:
            # Prepare the prompt for Azure OpenAI
            prompt = f"""Create a warm, personalized welcome message for a new Twitter follower.

            New follower username: @{username}
            Their bio: {user_bio if user_bio else "No bio available"}
            
            Company context: The Utility Company - We focus on providing valuable utility and tools for the crypto/DeFi space.
            
            Requirements:
            - Be genuine and welcoming
            - If they have a bio, reference something specific from it
            - Maintain a professional yet friendly tone
            - Include gratitude for them joining our community
            
            <IMPORTANT> Make sure to tag the username: @{username} in the message.</IMPORTANT>"""
            
            # Call Azure OpenAI
            messages = [
                {
                    "role": "system",
                    "content": "You are a community manager for The Utility Company, writing personalized welcome messages for new followers. Be warm, genuine, and professional and follow the instructions carefully."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            print(f"Messages: {messages}")

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                # max_completion_tokens=100,
                # temperature=0.7
            )
            
            welcome_message = response.choices[0].message.content.strip()
            print(f"Welcome message: {welcome_message}")
            
            # Add the @mention and community hashtag
            final_message = f"{welcome_message}"
            
            # Ensure it's under Twitter's character limit
            # if len(final_message) > 280:
            #     # Truncate the welcome message part if needed
            #     max_welcome_length = 280 - len(f"{welcome_message}")
            #     truncated_welcome = welcome_message[:max_welcome_length-3] + "..."
            #     final_message = f"Welcome to our community, @{username}! {truncated_welcome} #TheUtilityCommunity"
            
            return welcome_message
            
        except Exception as e:
            logger.warning(f"Error generating personalized welcome message: {e}")
            # Fallback message
            return f"Welcome to our community, @{username}! We're thrilled to have you join us and look forward to connecting with you. #TheUtilityCommunity"
    
    def _create_geometric_artwork_prompt(self, artwork_style: str) -> str:
        """Create a prompt for generating geometric modernist artwork"""
        base_prompts = {
            "geometric": "A clean geometric modernist artwork featuring intersecting circles, triangles, and rectangles in vibrant colors like electric blue, coral orange, and emerald green. Abstract composition with sharp lines and perfect shapes. No text or typography.",
            "abstract": "An abstract modernist composition with flowing geometric forms, gradient overlays, and dynamic color relationships. Bold shapes in sunset colors - deep purple, golden yellow, and crimson red. Contemporary digital art style. No text or typography.",
            "minimalist": "A minimalist geometric artwork with simple shapes and negative space. Limited color palette of navy blue, white, and one accent color. Clean lines and perfect balance. Modernist design principles. No text or typography.",
            "bauhaus": "A Bauhaus-inspired geometric composition with primary colors (red, blue, yellow) and basic shapes (circle, square, triangle). Grid-based layout with functional beauty. Classic modernist style. No text or typography."
        }
        
        return base_prompts.get(artwork_style, base_prompts["geometric"])
    
    async def _generate_geometric_welcome_image(self, artwork_prompt: str, welcome_message: str) -> dict:
        """Generate a geometric welcome image (local file only) for shout-out; does not post."""
        try:
            # Generate an image using the core generator to get a local file path (do not auto-post here)
            gen_result = social_media_generator.generate_image(prompt=artwork_prompt, size="1024x1024")
            if not gen_result or not isinstance(gen_result, dict) or not gen_result.get("success"):
                return {
                    "success": False,
                    "error": gen_result.get("error", "Image generation failed") if isinstance(gen_result, dict) else "Image generation failed"
                }
            
            image_url_or_path = gen_result.get("image_url") or gen_result.get("file_path") or ""
            if not image_url_or_path:
                return {"success": False, "error": "No image path returned"}
            
            # If an URL was returned, download to a local path
            local_path = image_url_or_path
            if image_url_or_path.startswith("http"):
                try:
                    resp = requests.get(image_url_or_path, stream=True)
                    resp.raise_for_status()
                    local_path = os.path.abspath("generated_image_welcome.jpg")
                    with open(local_path, "wb") as fh:
                        for chunk in resp.iter_content(chunk_size=8192):
                            fh.write(chunk)
                except Exception as dl_err:
                    return {"success": False, "error": f"Download failed: {dl_err}"}
            
            return {"success": True, "file_path": local_path}
        except Exception as e:
            return {"success": False, "error": f"Error generating geometric artwork: {str(e)}"}

    # === ENHANCED TOOL IMPLEMENTATION METHODS ===
    
    def _navigate_to_section(self, section: str) -> str:
        """Navigate to a specific Twitter section with enhanced visibility"""
        try:
            section_urls = {
                "home": "https://x.com/home",
                "explore": "https://x.com/explore",  
                "notifications": "https://x.com/notifications",
                "messages": "https://x.com/messages",
                "bookmarks": "https://x.com/i/bookmarks",
                "communities": "https://x.com/i/communities",
                "profile": "https://x.com/TheUtilityCo",
                "analytics": "https://analytics.x.com",
                "radar": "https://x.com/i/premium/radar",
                "creator_studio": "https://x.com/compose/post"
            }
            
            if section not in section_urls:
                return f"Unknown section: {section}. Available: {', '.join(section_urls.keys())}"
            
            self.scraper.driver.get(section_urls[section])
            time.sleep(4)  # Longer wait for loading
            
            # Enhanced verification with multiple checks
            current_url = self.scraper.driver.current_url
            page_title = self.scraper.driver.title
            
            # Check for specific interface elements based on section
            interface_elements = []
            
            if section == "home":
                # Look for home timeline elements
                timeline_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR, 
                    '[data-testid="tweet"], [data-testid="tweetText"], article[data-testid="tweet"]')
                compose_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR,
                    '[data-testid="tweetTextarea_0"], [placeholder*="happening"], [role="textbox"]')
                interface_elements.extend([f"Timeline tweets: {len(timeline_elements)}", f"Compose elements: {len(compose_elements)}"])
                
            elif section == "notifications":
                # Look for notification elements
                notification_cells = self.scraper.driver.find_elements(By.CSS_SELECTOR,
                    '[data-testid="cellInnerDiv"], [data-testid="notification"]')
                notification_tabs = self.scraper.driver.find_elements(By.CSS_SELECTOR,
                    '[role="tab"], [data-testid="primaryColumn"] div[role="tablist"]')
                interface_elements.extend([f"Notification cells: {len(notification_cells)}", f"Tab navigation: {len(notification_tabs)}"])
                
            elif section == "explore":
                # Look for explore/trending elements
                trending_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR,
                    '[data-testid="trend"], [aria-label*="Trending"], [data-testid="trendingTopic"]')
                search_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR,
                    '[data-testid="SearchBox_Search_Input"], [placeholder*="Search"]')
                interface_elements.extend([f"Trending topics: {len(trending_elements)}", f"Search interface: {len(search_elements)}"])
                
            elif section == "analytics":
                # Look for analytics interface elements
                chart_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR,
                    'canvas, svg, [class*="chart"], [class*="graph"], [data-testid*="chart"]')
                metric_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR,
                    '[class*="metric"], [class*="stat"], .analytics-metric')
                interface_elements.extend([f"Charts/graphs: {len(chart_elements)}", f"Metrics displayed: {len(metric_elements)}"])
            
            # Check for common navigation elements
            nav_elements = self.scraper.driver.find_elements(By.CSS_SELECTOR,
                '[data-testid="SideNav_AccountSwitcher_Button"], [data-testid="AppTabBar_Home_Link"], nav[role="navigation"]')
            
            return f"Successfully navigated to {section}.\nURL: {current_url}\nTitle: {page_title}\nInterface elements detected: {', '.join(interface_elements)}\nNavigation elements: {len(nav_elements)}"
                
        except Exception as e:
            return f"Error navigating to {section}: {str(e)}"

    def _search_twitter(self, query: str, search_type: str, filters: Dict) -> str:
        """Enhanced Twitter search with comprehensive result parsing"""
        try:
            # Navigate to search with proper encoding
            search_url = f"https://x.com/search?q={query.replace(' ', '%20')}"
            
            # Add search type filters
            if search_type == "latest":
                search_url += "&f=live"
            elif search_type == "people":
                search_url += "&f=user"
            elif search_type == "photos":
                search_url += "&f=image"
            elif search_type == "videos":
                search_url += "&f=video"
                
            self.scraper.driver.get(search_url)
            time.sleep(4)
            
            # Enhanced result detection with multiple selectors
            result_selectors = [
                '[data-testid="tweet"]',
                'article[data-testid="tweet"]',
                '[data-testid="UserCell"]',
                '[data-testid="cellInnerDiv"]'
            ]
            
            all_results = []
            result_details = {}
            
            for selector in result_selectors:
                elements = self.scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    all_results.extend(elements)
                    result_details[selector] = len(elements)
            
            # Parse different types of results
            tweet_results = self.scraper.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
            user_results = self.scraper.driver.find_elements(By.CSS_SELECTOR, '[data-testid="UserCell"]')
            
            # Check for search interface elements
            search_tabs = self.scraper.driver.find_elements(By.CSS_SELECTOR, '[role="tab"], [data-testid*="search"]')
            filter_options = self.scraper.driver.find_elements(By.CSS_SELECTOR, '[data-testid*="filter"], [aria-label*="filter"]')
            
            # Look for "no results" or error states
            no_results_indicators = self.scraper.driver.find_elements(By.XPATH, 
                '//*[contains(text(), "No results") or contains(text(), "Try searching") or contains(text(), "Nothing to see")]')
            
            search_summary = {
                "query": query,
                "search_type": search_type,
                "total_results": len(all_results),
                "tweet_results": len(tweet_results),
                "user_results": len(user_results),
                "search_tabs_available": len(search_tabs),
                "filter_options": len(filter_options),
                "no_results_found": len(no_results_indicators) > 0,
                "selector_breakdown": result_details
            }
            
            return f"Search completed for '{query}' ({search_type}):\n{json.dumps(search_summary, indent=2)}"
            
        except Exception as e:
            return f"Error searching Twitter: {str(e)}"

    async def _compose_tweet(self, content: str, thread_continuation: bool, add_media: bool, schedule_post: bool) -> str:
        """Enhanced tweet composition with Hybrid Mode routing (API vs Selenium)"""
        
        # Browser automation only (Safe Mode blocks this tool at the gate)

        try:
            # Navigate to compose if not already there
            current_url = self.scraper.driver.current_url
            if "compose" not in current_url and "home" not in current_url:
                self.scraper.driver.get("https://x.com/compose/post")
                time.sleep(3)
            
            # Enhanced compose interface detection
            compose_selectors = [
                'div.public-DraftEditor-content[contenteditable="true"]',
                '[data-testid="tweetTextarea_0"]',
                '[data-testid*="tweetTextarea"]',
                '[role="textbox"][placeholder*="happening"]',
                '[contenteditable="true"][role="textbox"]',
                'div[data-contents="true"]'
            ]
            
            text_area = None
            for selector in compose_selectors:
                try:
                    text_area = self.scraper.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not text_area:
                # Try opening compose dialog
                compose_buttons = self.scraper.driver.find_elements(By.CSS_SELECTOR, '[data-testid="SideNav_NewTweet_Button"]')
                if compose_buttons:
                    compose_buttons[0].click()
                    time.sleep(2)
                    
                    # Try finding text area again
                    for selector in compose_selectors:
                        try:
                            text_area = self.scraper.driver.find_element(By.CSS_SELECTOR, selector)
                            break
                        except NoSuchElementException:
                             continue
            
            if text_area:
                text_area.click()
                self.scraper._human_typing(text_area, content)
                time.sleep(2)
                
                # Click Tweet button
                tweet_buttons = self.scraper.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweetButtonInline"], [data-testid="tweetButton"]')
                if tweet_buttons:
                    tweet_buttons[0].click()
                    return f"Tweet posted: {content[:20]}..."
                else:
                    return "Error: Could not find Tweet button"
            else:
                return "Error: Could not find compose text area"

        except Exception as e:
            return f"Error composing tweet: {str(e)}"
    
    def _search_and_engage(self, query: str, search_type: str = "latest", engagement_type: str = "mixed", max_tweets: int = 5, engagement_rate: str = "medium") -> str:
        """Execute search and engage workflow using the scraper"""
        if not self.scraper:
             return "❌ Scraper not initialized. Enable Afterlife Mode."
        
        # Check for stop signal before starting
        if not getattr(self, "is_running", True):
            return "⛔ Operation cancelled by stop signal."
        
        results = self.scraper.search_tweets(query, max_results=max_tweets)
        if not results:
             return f"No tweets found for query: {query}"
        
        engaged_count = 0
        actions_log = []
        
        # Parse engagement rate
        rate_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
        prob = rate_map.get(engagement_rate, 0.5)
        
        for tweet in results:
            # Check for stop signal on each iteration
            if not getattr(self, "is_running", True):
                 logger.warning("🛑 Operation interrupted by stop signal.")
                 break

            if random.random() > prob:
                 continue
            
            url = tweet.get('url')
            if not url: continue
            
            action_taken = False
            
            # LIKE (if type is mixed, like, or all)
            if engagement_type in ["mixed", "like", "all"]:
                 if self.scraper.like_tweet(url):
                      actions_log.append(f"Liked {url}")
                      action_taken = True
            
            # REPLY (if type is mixed, reply, or all)
            if engagement_type in ["mixed", "reply", "all"] and action_taken: 
                 # Generate simple reply (in future use LLM)
                 reply_text = f"Interesting perspective on {query}! #Tech" 
                 if self.scraper.reply_to_tweet(url, reply_text):
                      actions_log.append(f"Replied to {url}")
                      engaged_count += 1
            
            if not action_taken and engagement_type in ["like"]:
                 if self.scraper.like_tweet(url): # Force like if explicitly asked
                      actions_log.append(f"Liked {url}")
                      engaged_count += 1

        return f"Engaged with {engaged_count} tweets via Scraper. Actions: {'; '.join(actions_log)}"

    async def _scroll_and_engage(self, duration_seconds: int = 180, engagement_rate: str = "medium", engagement_types: List[str] = None, focus_keywords: List[str] = None) -> str:
        """Simulate scrolling home feed and engaging using scraper primitives"""
        # Ensure scraper is initialized
        if not self.scraper:
            logger.warning("Scraper not initialized for scroll_and_engage. Attempting initialization...")
            self.set_afterlife_mode(True)
            if not self.scraper:
                return "❌ Scraper not initialized. Could not start browser."
        
        # Check for stop signal
        if not getattr(self, "is_running", True):
            return "⛔ Operation cancelled by stop signal."
        
        try:
            logger.warning(f"Starting scroll_and_engage (duration: {duration_seconds}s, rate: {engagement_rate})")
            
            # Navigate to home feed
            if hasattr(self.scraper, "driver") and self.scraper.driver:
                self.scraper.driver.get("https://x.com/home")
                time.sleep(5)
            else:
                return "❌ Scraper driver not available."
            
            # Use search_and_engage as fallback since we don't have feed scanning
            fallback_query = focus_keywords[0] if focus_keywords else "Tech"
            return self._search_and_engage(fallback_query, "latest", "mixed", 5, engagement_rate)
            
        except Exception as e:
            logger.error(f"Error in scroll_and_engage: {e}")
            return f"Error in scroll_and_engage: {str(e)}"

    async def _create_and_post_thread(self, topic: str, thread_length: int, focus_area: str = "general", include_hashtags: bool = True) -> str:
        """Create and post a thread"""
        # Simple stub logic using the new args
        hashtags = f" #{focus_area.replace(' ', '')}" if include_hashtags else ""
        tweets = [f"Thread on {topic} ({focus_area}) {i+1}/{thread_length}{hashtags}" for i in range(thread_length)]
        
        if not self.scraper:
             return f"❌ Scraper missing. Would have posted: {tweets}"
        
        # Post first tweet (Stub behavior - clearly indicated as such)
        if self.scraper.post_tweet(tweets[0]):
             return "Posted first tweet of thread"
        return "Failed to post thread start."

    async def generate_branded_image(self, prompt: str, tweet_text: str, size: str = "1024x1024", apply_company_branding: bool = True) -> Dict[str, Any]:
        """Generate a branded image and tweet it"""
        try:
            logger.warning(f"🎨 Generating branded image with prompt: {prompt}")
            
            # 1. Try to generate image using twitter_media_generator
            try:
                import twitter_media_generator
                if twitter_media_generator.is_media_available():
                    gen_result = twitter_media_generator.generate_image(prompt, size=size)
                    
                    if gen_result.get("success"):
                        image_path = gen_result.get("image_url")
                        logger.warning(f"✅ Image generated successfully: {image_path}")
                        
                        # 2. Post the tweet WITH the image
                        result = await self._compose_tweet(
                            content=tweet_text,
                            media_files=[image_path],
                            add_media=True
                        )
                        
                        return {
                            "success": True, 
                            "media_path": image_path, 
                            "tweet_text": tweet_text,
                            "result": result
                        }
                    else:
                        logger.error(f"Image generation failed: {gen_result.get('error')}")
                else:
                    logger.warning("⚠️ Azure OpenAI config missing for media generation. Falling back to text.")
            except ImportError:
                 logger.error("Could not import twitter_media_generator")
            except Exception as e:
                 logger.error(f"Error calling media generator: {e}")
            
            # Fallback to posting text only
            logger.warning("Using text-only fallback.")
            result = await self._compose_tweet(
                content=tweet_text + " (Image generation unavailable)",
                add_media=False
            )
            
            return {
                "success": True, 
                "media_path": None, 
                "tweet_text": tweet_text,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error in generate_branded_image: {e}")
            return {"success": False, "error": str(e)}

    async def generate_branded_video(self, prompt: str, tweet_text: str, duration: str = "20", apply_company_branding: bool = True) -> Dict[str, Any]:
        """Generate a branded video and tweet it"""
        try:
            logger.warning(f"🎥 Generating branded video with prompt: {prompt}")
            
            # 1. Try to generate video
            try:
                import twitter_media_generator
                if twitter_media_generator.is_media_available():
                    # Check/parse dimensions (simple logic for now)
                    width, height = "1080", "1920" # Portrait default
                    
                    gen_result = twitter_media_generator.generate_video(prompt, width=width, height=height)
                    
                    if gen_result.get("success"):
                        video_url = gen_result.get("video_url")
                        # Need to download it first? twitter_media_generator returns a URL
                        dl_result = twitter_media_generator.download_video(video_url, f"generated_video_{uuid.uuid4().hex[:8]}.mp4")
                        
                        if dl_result.get("success"):
                            video_path = dl_result.get("file_path")
                            logger.warning(f"✅ Video generated & downloaded: {video_path}")
                            
                            # 2. Post the tweet WITH the video
                            result = await self._compose_tweet(
                                content=tweet_text,
                                media_files=[video_path],
                                add_media=True # _compose_tweet handles video upload if logic supports it
                            )
                            
                            return {
                                "success": True, 
                                "media_path": video_path, 
                                "tweet_text": tweet_text,
                                "result": result
                            }
                    else:
                        logger.error(f"Video generation failed: {gen_result.get('error')}")
                else:
                    logger.warning("⚠️ Azure OpenAI config missing for video generation.")
            except Exception as e:
                 logger.error(f"Error calling video generator: {e}")

            logger.warning("Using text-only fallback.")
            
            # Fallback to just posting the text
            result = await self._compose_tweet(
                content=tweet_text + " (Video generation unavailable)",
                add_media=False
            )
            
            return {
                "success": True, 
                "media_path": None, 
                "tweet_text": tweet_text,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error in generate_branded_video: {e}")
            return {"success": False, "error": str(e)}

    async def _auto_reply_to_notifications(self, max_replies: int = 5, reply_style: str = "helpful", filter_keywords: List[str] = None) -> str:
        """Auto-reply to notifications using the scraper"""
        if not self.scraper:
            return "❌ Scraper not initialized. Enable Afterlife Mode first."
        
        if not getattr(self, "is_running", True):
            return "⛔ Operation cancelled by stop signal."
        
        try:
            logger.warning(f"Starting auto-reply to notifications (max: {max_replies}, style: {reply_style})")
            
            # Navigate to notifications
            self.scraper.driver.get("https://x.com/notifications")
            time.sleep(4)
            
            # Find notification elements
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            try:
                WebDriverWait(self.scraper.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]'))
                )
            except Exception as e:
                return f"Could not load notifications page: {str(e)}"
            
            replies_sent = 0
            results = []
            max_check = max_replies * 3  # Check more items to find match
            
            # Use index-based loop to avoid StaleElementReferenceException
            for i in range(max_check):
                if replies_sent >= max_replies:
                    break
                
                if not getattr(self, "is_running", True):
                    break
                
                try:
                    # Re-find elements on every iteration because the page DOM might have changed or refreshed
                    notifications = self.scraper.driver.find_elements(By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]')
                    
                    if i >= len(notifications):
                        logger.warning("Reached end of notifications list")
                        break
                        
                    notification = notifications[i]
                    text = notification.text.lower()
                    logger.info(f"Checking notification {i}: {text[:50]}...")
                    
                    # Filter by keywords if provided (skip if NO match found)
                    if filter_keywords:
                        matched_kw = next((kw for kw in filter_keywords if kw.lower() in text), None)
                        if not matched_kw:
                            logger.info(f"Skipping notification {i} - No keywords matched.")
                            continue
                        logger.info(f"Matched keyword: {matched_kw}")
                    
                    # Look for mentions or replies (things we can reply to)
                    # We look for common indicators that this is a replyable interaction
                    if any(indicator in text for indicator in ['mentioned you', 'replied to', 'posted:', 'says:']):
                        # Try to click to open the tweet
                        try:
                            logger.warning(f"Engaging with notification {i}...")
                            notification.click()
                            time.sleep(3)
                            
                            # Generate a reply
                            reply_text = f"Thank you for the mention! 🙏"
                            if reply_style == "professional":
                                reply_text = "Thank you for reaching out. We appreciate your engagement!"
                            elif reply_style == "friendly":
                                reply_text = "Hey! Thanks for the mention, really appreciate it! 😊"
                            # Add a contextual/keyword based suffix if possible
                            if filter_keywords and matched_kw:
                                reply_text += f" Great to see discussions about {matched_kw}!"

                            # Find reply input
                            # Try multiple selectors
                            reply_box = None
                            for sel in ['[data-testid="tweetTextarea_0"]', '[contenteditable="true"]']:
                                boxes = self.scraper.driver.find_elements(By.CSS_SELECTOR, sel)
                                if boxes:
                                    reply_box = boxes[0]
                                    break
                            
                            if reply_box:
                                reply_box.click()
                                self.scraper._human_typing(reply_box, reply_text)
                                time.sleep(1)
                                
                                # Click reply button
                                reply_btn = self.scraper.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]')
                                if reply_btn:
                                    reply_btn[0].click()
                                    replies_sent += 1
                                    logger.warning(f"✅ Replied to notification {i}")
                                    results.append(f"Replied to notification {i}")
                                    time.sleep(3)
                            else:
                                logger.warning(f"Could not find reply box for notification {i}")
                            
                            # Go back to notifications for next loop
                            self.scraper.driver.get("https://x.com/notifications")
                            time.sleep(4)
                            
                        except Exception as e:
                            logger.warning(f"Error processing notification {i}: {e}")
                            # Try to recover navigation
                            self.scraper.driver.get("https://x.com/notifications")
                            time.sleep(4)
                            continue
                    else:
                        logger.info(f"Skipping notification {i} - Not a replyable type (repost/like/follow)")
                            
                except Exception as e:
                    logger.warning(f"Error iterating notification {i}: {e}")
                    continue
        
            return f"Auto-reply complete. Sent {replies_sent} replies. Details: {'; '.join(results)}"
        
        except Exception as e:
            logger.error(f"Error in auto-reply: {e}")
            return f"Error during auto-reply: {str(e)}"