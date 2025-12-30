#!/usr/bin/env python3
"""
Twitter Bot CLI - Command Line Interface for controlling the Twitter automation bot
"""

import argparse
import sys
import time
from twitter_bot import TwitterBot
from config import Config, logger
import json

def print_banner():
    """Print bot banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                     TWITTER AUTOMATION BOT                   ║
    ║                                                              ║
    ║  Autonomous Twitter management without API restrictions      ║
    ║  Features: Tweet, Reply, Retweet, Search, Follow            ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def validate_config():
    """Validate configuration before starting"""
    config = Config()
    validation = config.validate()
    
    if not validation['valid']:
        print("❌ Configuration Error!")
        print(f"Missing required fields: {', '.join(validation['missing_fields'])}")
        print("\n📝 Please check your config.env file and ensure all required credentials are set.")
        return False
    
    if validation['warnings']:
        print("⚠️  Configuration Warnings:")
        for warning in validation['warnings']:
            print(f"   - {warning}")
        print()
    
    print("✅ Configuration validated successfully!")
    return True

def run_autonomous_mode():
    """Run the bot in full autonomous mode"""
    print("🤖 Starting Autonomous Mode...")
    print("The bot will run continuously and perform automated actions.")
    print("Press Ctrl+C to stop.\n")
    
    if not validate_config():
        return
    
    bot = TwitterBot()
    try:
        bot.start_autonomous_mode()
    except KeyboardInterrupt:
        print("\n🛑 Stopping autonomous mode...")
        bot.cleanup()
        print("Bot stopped successfully!")

def run_single_tweet(content):
    """Post a single tweet"""
    print(f"📝 Posting tweet: {content}")
    
    if not validate_config():
        return
    
    bot = TwitterBot()
    if bot.initialize():
        if content:
            success = bot.scraper.post_tweet(content)
        else:
            success = bot.autonomous_tweet()
        
        if success:
            print("✅ Tweet posted successfully!")
        else:
            print("❌ Failed to post tweet")
        
        bot.cleanup()
    else:
        print("❌ Failed to initialize bot")

def run_search_engage(keyword, max_results):
    """Search and engage with tweets"""
    print(f"🔍 Searching for '{keyword}' and engaging with {max_results} tweets...")
    
    if not validate_config():
        return
    
    bot = TwitterBot()
    if bot.initialize():
        tweets = bot.scraper.search_tweets(keyword, max_results)
        print(f"Found {len(tweets)} tweets")
        
        if tweets:
            engagement_count = 0
            for i, tweet in enumerate(tweets, 1):
                print(f"\n{i}. @{tweet['username']}: {tweet['text'][:100]}...")
                
                # Ask user what to do
                action = input("Action [l]ike, [r]etweet, [reply], [s]kip, [q]uit: ").lower()
                
                if action == 'q':
                    break
                elif action == 'l':
                    if bot.scraper.like_tweet(tweet['url']):
                        print("  ✅ Liked!")
                        engagement_count += 1
                elif action == 'r':
                    if bot.scraper.retweet(tweet['url']):
                        print("  ✅ Retweeted!")
                        engagement_count += 1
                elif action == 'reply':
                    reply_text = input("  Enter reply: ")
                    if reply_text and bot.scraper.reply_to_tweet(tweet['url'], reply_text):
                        print("  ✅ Reply posted!")
                        engagement_count += 1
                
                time.sleep(1)
            
            print(f"\n📊 Engaged with {engagement_count} tweets")
        
        bot.cleanup()
    else:
        print("❌ Failed to initialize bot")

def show_stats():
    """Show bot activity statistics"""
    print("📊 Bot Activity Statistics")
    print("-" * 40)
    
    bot = TwitterBot()
    stats = bot.get_activity_stats()
    
    for key, value in stats.items():
        formatted_key = key.replace('_', ' ').title()
        print(f"{formatted_key}: {value}")

def follow_user(username):
    """Follow a specific user"""
    print(f"👤 Following @{username}...")
    
    if not validate_config():
        return
    
    bot = TwitterBot()
    if bot.initialize():
        success = bot.scraper.follow_user(username)
        if success:
            print(f"✅ Successfully followed @{username}!")
        else:
            print(f"❌ Failed to follow @{username}")
        
        bot.cleanup()
    else:
        print("❌ Failed to initialize bot")

def get_trending():
    """Get and display trending topics"""
    print("🔥 Getting trending topics...")
    
    if not validate_config():
        return
    
    bot = TwitterBot()
    if bot.initialize():
        trends = bot.scraper.get_trending_topics()
        
        if trends:
            print("\n📈 Current Trending Topics:")
            print("-" * 40)
            for i, trend in enumerate(trends, 1):
                print(f"{i:2d}. {trend['name']}")
        else:
            print("❌ No trending topics found")
        
        bot.cleanup()
    else:
        print("❌ Failed to initialize bot")

def test_login():
    """Test login functionality"""
    print("🔐 Testing login...")
    
    if not validate_config():
        return
    
    bot = TwitterBot()
    if bot.initialize():
        print("✅ Login successful!")
        bot.cleanup()
    else:
        print("❌ Login failed")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Twitter Automation Bot - Control your Twitter presence autonomously",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --autonomous                    # Run in full autonomous mode
  python main.py --tweet "Hello, world!"        # Post a single tweet
  python main.py --search python --max 5        # Search and engage with 5 tweets
  python main.py --follow elonmusk              # Follow a specific user
  python main.py --trending                     # Show trending topics
  python main.py --stats                        # Show activity statistics
  python main.py --test-login                   # Test login functionality
        """
    )
    
    parser.add_argument('--autonomous', action='store_true',
                        help='Run bot in autonomous mode')
    parser.add_argument('--tweet', type=str,
                        help='Post a single tweet with specified content')
    parser.add_argument('--auto-tweet', action='store_true',
                        help='Post an automatically generated tweet')
    parser.add_argument('--search', type=str,
                        help='Search for tweets with specified keyword')
    parser.add_argument('--max', type=int, default=5,
                        help='Maximum number of results for search (default: 5)')
    parser.add_argument('--follow', type=str,
                        help='Follow a specific user')
    parser.add_argument('--trending', action='store_true',
                        help='Show trending topics')
    parser.add_argument('--stats', action='store_true',
                        help='Show bot activity statistics')
    parser.add_argument('--test-login', action='store_true',
                        help='Test login functionality')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Handle arguments
    if args.autonomous:
        run_autonomous_mode()
    elif args.tweet:
        run_single_tweet(args.tweet)
    elif args.auto_tweet:
        run_single_tweet(None)
    elif args.search:
        run_search_engage(args.search, args.max)
    elif args.follow:
        follow_user(args.follow)
    elif args.trending:
        get_trending()
    elif args.stats:
        show_stats()
    elif args.test_login:
        test_login()
    else:
        # Interactive mode
        print("🚀 Welcome to Twitter Bot Interactive Mode!")
        print("\nAvailable commands:")
        print("  1. Run autonomous mode")
        print("  2. Post a tweet")
        print("  3. Search and engage")
        print("  4. Follow user")
        print("  5. Show trending topics")
        print("  6. Show statistics")
        print("  7. Test login")
        print("  0. Exit")
        
        while True:
            try:
                choice = input("\nSelect an option (0-7): ").strip()
                
                if choice == '0':
                    print("👋 Goodbye!")
                    break
                elif choice == '1':
                    run_autonomous_mode()
                elif choice == '2':
                    content = input("Enter tweet content (or press Enter for auto-generated): ").strip()
                    run_single_tweet(content if content else None)
                elif choice == '3':
                    keyword = input("Enter search keyword: ").strip()
                    if keyword:
                        max_results = input("Max results (default 5): ").strip()
                        max_results = int(max_results) if max_results.isdigit() else 5
                        run_search_engage(keyword, max_results)
                elif choice == '4':
                    username = input("Enter username to follow (without @): ").strip()
                    if username:
                        follow_user(username)
                elif choice == '5':
                    get_trending()
                elif choice == '6':
                    show_stats()
                elif choice == '7':
                    test_login()
                else:
                    print("❌ Invalid option. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main() 