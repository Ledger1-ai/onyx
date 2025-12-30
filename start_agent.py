#!/usr/bin/env python3
"""
Twitter Super Agent Launcher
Provides an easy interface to start and test the super agent functions
"""

import sys
import argparse
from bot_controller import TwitterSuperAgent
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Twitter Super Agent - Autonomous Twitter Management')
    parser.add_argument('--function', choices=['test', 'reply', 'trending', 'quote', 'content', 'monitor', 'analytics', 'discover'], 
                       help='Run specific function')
    parser.add_argument('--config', default='agent_config.json', help='Configuration file path')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--cycle-hours', type=int, default=4, help='Hours between cycles (default: 4)')
    parser.add_argument('--dry-run', action='store_true', help='Run without actually posting/interacting')
    
    args = parser.parse_args()
    
    print("🚀 Starting Twitter Super Agent...")
    print("━" * 50)
    
    # Initialize agent
    try:
        agent = TwitterSuperAgent(config_file=args.config)
        print(f"✅ Loaded configuration from {args.config}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}")
        return 1
    
    try:
        if args.function:
            print(f"🎯 Running function: {args.function}")
            
            if args.function == "test":
                # Run single cycle for testing
                success = agent.run_autonomous_cycle()
                print("✅ Test cycle completed" if success else "❌ Test cycle failed")
                
            elif args.function == "reply":
                agent.reply_bot_function()
                print("✅ Reply bot function completed")
                
            elif args.function == "trending":
                agent.trending_monitor_function()
                print("✅ Trending monitor function completed")
                
            elif args.function == "quote":
                agent.quote_tweet_function()
                print("✅ Quote tweet function completed")
                
            elif args.function == "content":
                success = agent.content_creation_function()
                print("✅ Content creation completed" if success else "ℹ️ Content creation skipped")
                
            elif args.function == "monitor":
                agent.performance_monitoring_function()
                print("✅ Performance monitoring completed")
                
            elif args.function == "analytics":
                agent.scrape_analytics_data()
                print("✅ Analytics scraping completed")
                
            elif args.function == "discover":
                print("🔍 Running account discovery...")
                discovered = agent.discover_relevant_accounts()
                print(f"✅ Discovered {len(discovered)} relevant accounts")
                
                # Show discovered accounts
                target_accounts = agent.get_dynamic_target_accounts()
                print(f"🎯 Current target accounts: {', '.join(target_accounts)}")
                
        elif args.continuous:
            print(f"🔄 Running continuously (cycles every {args.cycle_hours} hours)")
            print("Press Ctrl+C to stop")
            agent.run_continuous(cycle_interval_hours=args.cycle_hours)
            
        else:
            # Interactive mode
            print("🤖 Interactive Mode")
            print("Available commands:")
            print("  1. Test single cycle")
            print("  2. Reply bot")
            print("  3. Trending monitor")
            print("  4. Quote tweeting")
            print("  5. Content creation")
            print("  6. Performance monitoring")
            print("  7. Analytics scraping")
            print("  8. Account discovery")
            print("  9. Run continuously")
            print("  10. Exit")
            
            while True:
                try:
                    choice = input("\nEnter your choice (1-10): ").strip()
                    
                    if choice == "1":
                        print("🧪 Running test cycle...")
                        agent.run_autonomous_cycle()
                    elif choice == "2":
                        print("💬 Running reply bot...")
                        agent.reply_bot_function()
                    elif choice == "3":
                        print("📈 Running trending monitor...")
                        agent.trending_monitor_function()
                    elif choice == "4":
                        print("🔄 Running quote tweeting...")
                        agent.quote_tweet_function()
                    elif choice == "5":
                        print("✍️ Running content creation...")
                        agent.content_creation_function()
                    elif choice == "6":
                        print("📊 Running performance monitoring...")
                        agent.performance_monitoring_function()
                    elif choice == "7":
                        print("📈 Scraping analytics...")
                        agent.scrape_analytics_data()
                    elif choice == "8":
                        print("🔍 Running account discovery...")
                        discovered = agent.discover_relevant_accounts()
                        print(f"✅ Discovered {len(discovered)} relevant accounts")
                        target_accounts = agent.get_dynamic_target_accounts()
                        print(f"🎯 Current target accounts: {', '.join(target_accounts)}")
                    elif choice == "9":
                        print("🔄 Starting continuous mode...")
                        print("Press Ctrl+C to stop")
                        agent.run_continuous()
                    elif choice == "10":
                        print("👋 Goodbye!")
                        break
                    else:
                        print("❌ Invalid choice. Please enter 1-10.")
                        
                except KeyboardInterrupt:
                    print("\n👋 Stopping...")
                    break
    
    except KeyboardInterrupt:
        print("\n👋 Super Agent shutting down...")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1
    finally:
        try:
            agent.close()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 