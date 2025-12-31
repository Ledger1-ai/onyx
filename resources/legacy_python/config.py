import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import logging

# Load environment variables
load_dotenv('config.env')  # Try config.env first
load_dotenv()  # Fallback to .env

class Config:
    """Configuration class for the Twitter bot"""
    
    # Twitter API Credentials
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    
    # Twitter Account Credentials (for selenium)
    TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')
    TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
    TWITTER_EMAIL = os.getenv('TWITTER_EMAIL')
    
    # Bot Configuration
    MAX_TWEETS_PER_HOUR = int(os.getenv('MAX_TWEETS_PER_HOUR', 10))
    MAX_REPLIES_PER_HOUR = int(os.getenv('MAX_REPLIES_PER_HOUR', 20))
    MAX_RETWEETS_PER_HOUR = int(os.getenv('MAX_RETWEETS_PER_HOUR', 15))
    
    SEARCH_KEYWORDS = os.getenv('SEARCH_KEYWORDS', 'python,AI,technology').split(',')
    TARGET_HASHTAGS = os.getenv('TARGET_HASHTAGS', '#python,#AI,#tech').split(',')
    
    # Selenium Configuration
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
    IMPLICIT_WAIT = int(os.getenv('IMPLICIT_WAIT', '10'))
    USE_PERSISTENT_PROFILE = os.getenv('USE_PERSISTENT_PROFILE', 'true').lower() == 'true'
    PROFILE_DIRECTORY = os.getenv('PROFILE_DIRECTORY', 'browser_profiles/twitter_automation_profile')
    
    # Login Management
    AUTO_LOGIN_RETRY = int(os.getenv('AUTO_LOGIN_RETRY', '3'))
    LOGIN_TIMEOUT = int(os.getenv('LOGIN_TIMEOUT', '30'))
    
    # Rate limiting
    RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

    # Database Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    
    # Multi-Tenant Configuration
    DEFAULT_USER_ID = os.getenv('DEFAULT_USER_ID', 'admin_user')  # Standard user ID for single-tenant mode
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        validation_result = {
            'valid': True,
            'missing_fields': [],
            'warnings': []
        }
        
        # Check if we have Selenium credentials (required for web scraping)
        selenium_credentials = [cls.TWITTER_USERNAME, cls.TWITTER_PASSWORD]
        if not all(selenium_credentials):
            validation_result['missing_fields'].extend([
                field for field, value in [
                    ('TWITTER_USERNAME', cls.TWITTER_USERNAME),
                    ('TWITTER_PASSWORD', cls.TWITTER_PASSWORD)
                ] if not value
            ])
            validation_result['valid'] = False
        
        # Twitter API credentials are optional (for future use)
        api_credentials = [
            cls.TWITTER_API_KEY, cls.TWITTER_API_SECRET, 
            cls.TWITTER_ACCESS_TOKEN, cls.TWITTER_ACCESS_TOKEN_SECRET
        ]
        
        if not any(api_credentials):
            validation_result['warnings'].append('Twitter API credentials not found - using web scraping mode only')
        elif not all(api_credentials):
            validation_result['warnings'].append('Incomplete Twitter API credentials - some API features disabled')
            
        if not cls.TWITTER_BEARER_TOKEN:
            validation_result['warnings'].append('TWITTER_BEARER_TOKEN missing - some API features may not work')
            
        if not cls.TWITTER_EMAIL:
            validation_result['warnings'].append('TWITTER_EMAIL missing - 2FA authentication may fail')
            
        return validation_result

# Logging configuration
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('twitter_bot.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging() 