#!/usr/bin/env python3
"""
Setup Script for Intelligent Twitter Agent Scheduling System
==========================================================
Initializes and configures the complete scheduling and performance tracking system.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import json

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('setup.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python version {sys.version_info.major}.{sys.version_info.minor} is compatible")

def install_dependencies(logger):
    """Install required dependencies"""
    logger.info("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Failed to install dependencies: {e}")
        return False

def check_mongodb_connection(logger, uri="mongodb://localhost:27017/"):
    """Check MongoDB connection"""
    try:
        import pymongo
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # Force connection
        logger.info("✓ MongoDB connection successful")
        return True
    except Exception as e:
        logger.warning(f"⚠ MongoDB connection failed: {e}")
        logger.info("Please ensure MongoDB is installed and running")
        return False

def create_config_file(logger):
    """Create default configuration file"""
    config = {
        "database": {
            "mongodb_uri": "mongodb://localhost:27017/",
            "database_name": "twitter_agent_db"
        },
        "scheduling": {
            "timezone": "UTC",
            "daily_review_time": "00:00",
            "max_activities_per_day": 32,
            "activity_duration_minutes": 15
        },
        "performance": {
            "metrics_retention_days": 90,
            "analysis_frequency_hours": 24,
            "optimization_threshold": 0.1
        },
        "logging": {
            "level": "INFO",
            "log_file": "agent_system.log",
            "max_log_size_mb": 10,
            "backup_count": 5
        },
        "system": {
            "enable_background_monitoring": True,
            "auto_optimization": True,
            "backup_enabled": True,
            "backup_frequency_hours": 24
        }
    }
    
    config_path = "config.json"
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"✓ Configuration file created: {config_path}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create config file: {e}")
        return False

def create_directory_structure(logger):
    """Create necessary directories"""
    directories = [
        "logs",
        "data",
        "backups",
        "reports",
        "temp"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            logger.info(f"✓ Directory created: {directory}")
        except Exception as e:
            logger.error(f"✗ Failed to create directory {directory}: {e}")
            return False
    
    return True

def initialize_database(logger):
    """Initialize database with default data"""
    try:
        from database_manager import DatabaseManager
        from data_models import create_default_strategy
        
        db = DatabaseManager()
        
        # Initialize database
        if not db.initialize_database():
            logger.error("✗ Failed to initialize database")
            return False
        
        # Create default strategy
        default_strategy = create_default_strategy()
        if db.save_strategy_template(default_strategy):
            logger.info("✓ Default strategy created")
        else:
            logger.warning("⚠ Failed to create default strategy")
        
        logger.info("✓ Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False

def create_sample_schedule(logger):
    """Create a sample schedule for today"""
    try:
        from schedule_manager import ScheduleManager
        from database_manager import DatabaseManager
        
        db = DatabaseManager()
        scheduler = ScheduleManager(db)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Generate schedule for today
        success = scheduler.generate_daily_schedule(today)
        
        if success:
            schedule = scheduler.get_daily_schedule(today)
            logger.info(f"✓ Sample schedule created with {len(schedule)} activities")
            return True
        else:
            logger.warning("⚠ Failed to create sample schedule")
            return False
            
    except Exception as e:
        logger.error(f"✗ Sample schedule creation failed: {e}")
        return False

def test_system_integration(logger):
    """Test basic system integration"""
    try:
        from agent_integration import create_agent_integration
        
        # Create integration instance
        integration = create_agent_integration()
        
        # Test basic functionality
        next_activity = integration.get_next_activity()
        if next_activity:
            logger.info(f"✓ System integration test passed - Next activity: {next_activity.activity_type.value}")
        else:
            logger.info("✓ System integration test passed - No activities scheduled")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ System integration test failed: {e}")
        return False

def create_startup_script(logger):
    """Create startup script for the system"""
    startup_script = '''#!/usr/bin/env python3
"""
Startup script for Intelligent Twitter Agent System
"""

import logging
import sys
from agent_integration import start_automated_system

def main():
    """Start the automated system"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/agent_system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Intelligent Twitter Agent System...")
    
    # Start the system
    integration = start_automated_system()
    
    if integration:
        try:
            logger.info("System started successfully. Press Ctrl+C to stop.")
            
            # Keep running
            import time
            while True:
                time.sleep(60)
                
                # Optionally log status
                next_activity = integration.get_next_activity()
                if next_activity:
                    logger.debug(f"Next activity: {next_activity.activity_type.value} at {next_activity.start_time}")
                
        except KeyboardInterrupt:
            logger.info("Shutting down system...")
            integration.stop()
            logger.info("System stopped successfully")
    else:
        logger.error("Failed to start system")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    try:
        with open("start_system.py", 'w') as f:
            f.write(startup_script)
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod("start_system.py", 0o755)
        
        logger.info("✓ Startup script created: start_system.py")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to create startup script: {e}")
        return False

def create_example_integration(logger):
    """Create example integration file"""
    example_code = '''#!/usr/bin/env python3
"""
Example Integration with Existing intelligent_agent.py
====================================================
This file shows how to integrate the scheduling system with your existing intelligent_agent.py
"""

import logging
from datetime import datetime
from agent_integration import create_agent_integration, ActivityType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExampleTwitterAgent:
    """Example Twitter agent class (replace with your actual agent)"""
    
    def __init__(self):
        self.name = "Example Agent"
    
    def post_tweet(self, content):
        """Example tweet posting method"""
        logger.info(f"Posting tweet: {content}")
        # Your actual posting logic here
        return True
    
    def engage_with_users(self):
        """Example engagement method"""
        logger.info("Engaging with users...")
        # Your actual engagement logic here
        return {"likes_given": 5, "replies_sent": 2}

def main():
    """Main integration example"""
    
    # Create your agent instance
    twitter_agent = ExampleTwitterAgent()
    
    # Create the scheduling integration
    integration = create_agent_integration(intelligent_agent=twitter_agent)
    
    # Define custom activity callbacks
    def posting_callback(slot):
        """Custom posting activity"""
        logger.info(f"Executing posting activity: {slot.description}")
        
        # Use your agent to post
        success = twitter_agent.post_tweet("Hello from the automated system!")
        
        return {
            "interactions": {"posts_created": 1 if success else 0},
            "quality_score": 0.8 if success else 0.0,
            "notes": "Automated post completed"
        }
    
    def engagement_callback(slot):
        """Custom engagement activity"""
        logger.info(f"Executing engagement activity: {slot.description}")
        
        # Use your agent to engage
        results = twitter_agent.engage_with_users()
        
        return {
            "interactions": results,
            "quality_score": 0.7,
            "notes": "Engagement session completed"
        }
    
    # Register callbacks
    integration.register_activity_callback(ActivityType.POSTING, posting_callback)
    integration.register_activity_callback(ActivityType.ENGAGEMENT, engagement_callback)
    
    # Start the system
    if integration.start():
        logger.info("Integrated system started successfully!")
        
        # Example of manual activity recording
        tweet_data = {
            "tweet_id": "123456789",
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
        
        # Get system status
        summary = integration.get_performance_summary(days=7)
        logger.info(f"Performance summary: {summary}")
        
        # The system will now run automatically in the background
        # You can continue with your other code or keep it running
        
        try:
            import time
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Stopping integrated system...")
            integration.stop()
    else:
        logger.error("Failed to start integrated system")

if __name__ == "__main__":
    main()
'''
    
    try:
        with open("example_integration.py", 'w') as f:
            f.write(example_code)
        
        logger.info("✓ Example integration file created: example_integration.py")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to create example integration: {e}")
        return False

def print_summary(logger, results):
    """Print setup summary"""
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60)
    
    for step, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{step:40} {status}")
    
    print("\n" + "="*60)
    
    if all(results.values()):
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Ensure MongoDB is running")
        print("2. Run: python start_system.py")
        print("3. Check example_integration.py for integration examples")
        print("4. Monitor logs in the logs/ directory")
    else:
        print("⚠ SETUP COMPLETED WITH ISSUES")
        failed_steps = [step for step, success in results.items() if not success]
        print(f"\nFailed steps: {', '.join(failed_steps)}")
        print("Please resolve the issues and run setup again")
    
    print("="*60)

def main():
    """Main setup function"""
    logger = setup_logging()
    logger.info("Starting system setup...")
    
    print("Intelligent Twitter Agent Scheduling System Setup")
    print("=" * 50)
    
    # Setup steps
    results = {}
    
    # Check Python version
    try:
        check_python_version()
        results["Python Version Check"] = True
    except SystemExit:
        results["Python Version Check"] = False
        print_summary(logger, results)
        return
    
    # Install dependencies
    results["Dependency Installation"] = install_dependencies(logger)
    
    # Check MongoDB
    results["MongoDB Connection"] = check_mongodb_connection(logger)
    
    # Create configuration
    results["Configuration File"] = create_config_file(logger)
    
    # Create directories
    results["Directory Structure"] = create_directory_structure(logger)
    
    # Initialize database (only if MongoDB is available)
    if results["MongoDB Connection"]:
        results["Database Initialization"] = initialize_database(logger)
        results["Sample Schedule Creation"] = create_sample_schedule(logger)
    else:
        results["Database Initialization"] = False
        results["Sample Schedule Creation"] = False
    
    # Test system integration
    if results["Dependency Installation"]:
        results["System Integration Test"] = test_system_integration(logger)
    else:
        results["System Integration Test"] = False
    
    # Create startup script
    results["Startup Script"] = create_startup_script(logger)
    
    # Create example integration
    results["Example Integration"] = create_example_integration(logger)
    
    # Print summary
    print_summary(logger, results)
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 