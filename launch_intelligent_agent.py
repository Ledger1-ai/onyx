#!/usr/bin/env python3
"""
Intelligent Twitter Agent Launcher
=================================
Launch script for running the intelligent Twitter agent in different modes.
Now supports full browser-based automation without database dependencies.
"""

import sys
import argparse
import asyncio
import logging
from intelligent_agent import IntelligentTwitterAgent
from selenium_scraper import TwitterScraper

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('agent_launcher.log'),
            logging.StreamHandler()
        ]
    )

async def run_interactive(headless=False, use_persistent_profile=True):
    """Run agent in interactive mode"""
    agent = IntelligentTwitterAgent(headless=headless, use_persistent_profile=use_persistent_profile)
    try:
        from intelligent_agent import interactive_mode_with_agent
        await interactive_mode_with_agent(agent)
    finally:
        agent.shutdown()

async def run_autonomous(hours=1, mode="hybrid", headless=False, use_persistent_profile=True):
    """Run agent autonomously for specified hours"""
    agent = IntelligentTwitterAgent(headless=headless, use_persistent_profile=use_persistent_profile)
    print(f"🤖 Starting autonomous mode ({mode}) for {hours} hours...")
    
    try:
        # Set operation mode
        await agent.process_command(f"set operation mode to {mode} with adaptive intensity")
        
        # Get initial analytics
        await agent.process_command("check analytics for last 7 days")
        
        # Start with account discovery if needed
        if mode in ["discovery", "hybrid"]:
            await agent.process_command("discover accounts for ['industrial automation', 'robotics', 'IoT'] keywords")
        
        # Monitor notifications and engage
        await agent.process_command("monitor notifications with auto respond enabled")
        
        # Run primary activities based on mode
        if mode == "content_creation":
            await agent.process_command("compose tweet about industrial automation democratizing manufacturing")
            await asyncio.sleep(300)  # Wait 5 minutes
            await agent.process_command("compose tweet about community empowerment through technology")
        
        elif mode == "engagement":
            await agent.process_command("search twitter for 'industrial automation' latest")
            await asyncio.sleep(60)
            await agent.process_command("search twitter for 'robotics manufacturing' people")
        
        elif mode == "analytics":
            await agent.process_command("use radar tool for technology deep search")
            await asyncio.sleep(120)
            await agent.process_command("analyze performance with comprehensive depth")
        
        elif mode == "hybrid":
            # Balanced approach
            tasks = [
                "compose tweet about democratizing automation technology",
                "discover accounts for ['automation', 'manufacturing'] keywords", 
                "check analytics for last 1day",
                "search twitter for 'industrial IoT' latest",
                "analyze performance with detailed depth"
            ]
            
            for task in tasks:
                await agent.process_command(task)
                await asyncio.sleep(180)  # 3 minutes between tasks
        
        # Final status check
        await agent.process_command("get session status")
        
        print(f"✅ Autonomous mode completed after approximately {hours} hours")
        
    except KeyboardInterrupt:
        print("\n🛑 Autonomous mode interrupted by user")
    finally:
        agent.shutdown()

async def run_discovery_session():
    """Run a focused account discovery session"""
    agent = IntelligentTwitterAgent()
    
    print("🔍 Starting focused account discovery session...")
    
    discovery_keywords = [
        "industrial automation",
        "robotics manufacturing", 
        "supply chain IoT",
        "smart manufacturing",
        "industrial AI",
        "automation technology"
    ]
    
    try:
        await agent.process_command("set operation mode to discovery with high intensity")
        
        for keywords in [discovery_keywords[i:i+2] for i in range(0, len(discovery_keywords), 2)]:
            await agent.process_command(f"discover accounts for {keywords} with max 15 accounts")
            await asyncio.sleep(120)
        
        await agent.process_command("analyze performance with detailed depth")
        
    finally:
        agent.shutdown()

async def run_engagement_spree():
    """Run a focused engagement session"""
    agent = IntelligentTwitterAgent()
    
    print("💬 Starting engagement spree session...")
    
    try:
        await agent.process_command("set operation mode to engagement with high intensity")
        
        # Check notifications first
        await agent.process_command("monitor notifications with auto respond enabled")
        
        # Search and engage with trending content
        search_terms = [
            "industrial automation trends",
            "manufacturing innovation",
            "automation future",
            "smart factory technology"
        ]
        
        for term in search_terms:
            await agent.process_command(f"search twitter for '{term}' latest")
            await asyncio.sleep(90)
        
        await agent.process_command("get session status")
        
    finally:
        agent.shutdown()

async def run_content_creation_session():
    """Run a focused content creation session"""
    agent = IntelligentTwitterAgent()
    
    print("✍️ Starting content creation session...")
    
    content_topics = [
        "The future of industrial automation is about democratizing access to advanced tools",
        "Community-driven manufacturing: how local automation can transform economies",
        "Breaking down barriers: making industrial IoT accessible to all manufacturers",
        "Sustainable automation: technology that empowers communities while protecting the environment"
    ]
    
    try:
        await agent.process_command("set operation mode to content_creation with medium intensity")
        
        for i, topic in enumerate(content_topics):
            await agent.process_command(f"compose tweet about {topic}")
            if i < len(content_topics) - 1:
                await asyncio.sleep(900)  # 15 minutes between posts
        
        await agent.process_command("analyze performance with detailed depth")
        
    finally:
        agent.shutdown()

async def run_analytics_deep_dive():
    """Run comprehensive analytics and radar analysis"""
    agent = IntelligentTwitterAgent()
    
    print("📊 Starting analytics deep dive session...")
    
    try:
        await agent.process_command("set operation mode to analytics with high intensity")
        
        # Check standard analytics
        await agent.process_command("check analytics for last 28days with impressions focus")
        await asyncio.sleep(60)
        
        await agent.process_command("check analytics for last 7days with engagements focus")
        await asyncio.sleep(60)
        
        # Use premium features if available
        await agent.process_command("use radar tool for automation comprehensive search")
        await asyncio.sleep(90)
        
        await agent.process_command("use radar tool for technology deep search")
        await asyncio.sleep(90)
        
        # Comprehensive performance analysis
        await agent.process_command("analyze performance with comprehensive depth and strategy adjustment")
        
    finally:
        agent.shutdown()

async def test_all_tools():
    """Test all available tools systematically"""
    agent = IntelligentTwitterAgent()
    
    test_commands = [
        # Navigation tests
        "navigate to analytics",
        "navigate to radar", 
        "navigate to home",
        
        # Search tests
        "search twitter for 'industrial automation' latest",
        "search twitter for 'robotics' people",
        
        # Discovery tests
        "discover accounts for ['automation'] keywords",
        
        # Analytics tests
        "check analytics for last 7days",
        "use radar tool for technology",
        
        # Performance tests
        "analyze performance with quick depth",
        "get session status",
        
        # Control tests
        "set operation mode to monitoring with low intensity",
        "pause operations for 1 minutes",
        "pause operations for 0 minutes"  # unpause
    ]
    
    print("🧪 Testing all available tools systematically...")
    
    for i, command in enumerate(test_commands):
        print(f"\n[{i+1}/{len(test_commands)}] Testing: {command}")
        try:
            response = await agent.process_command(command)
            print(f"✅ Success: {response[:100]}..." if len(response) > 100 else f"✅ Success: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await asyncio.sleep(3)
    
    agent.shutdown()

async def run_single_command(command):
    """Run a single command and show detailed results"""
    agent = IntelligentTwitterAgent()
    
    try:
        print(f"🎯 Executing: {command}")
        print("=" * 50)
        
        response = await agent.process_command(command)
        print(f"Response:\n{response}")
        
        print("\n" + "=" * 50)
        status = agent.get_status()
        print(f"Final Status:\n{status}")
        
    finally:
        agent.shutdown()

def main():
    """Main launcher with argument parsing"""
    parser = argparse.ArgumentParser(
        description="🤖 Intelligent Twitter Super Agent - Full Selenium Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with persistent login
  python launch_intelligent_agent.py --interactive
  
  # First time setup (manual login)
  python launch_intelligent_agent.py --setup-login
  
  # Clear saved login
  python launch_intelligent_agent.py --clear-login
  
  # Autonomous with persistent profile
  python launch_intelligent_agent.py --autonomous --mode hybrid --hours 2
  
  # Headless mode (no browser window)
  python launch_intelligent_agent.py --interactive --headless
        """
    )
    
    parser.add_argument(
        '--interactive', 
        action='store_true',
        help='Run in interactive mode for manual control'
    )
    
    parser.add_argument(
        '--autonomous',
        action='store_true', 
        help='Run in autonomous mode'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['discovery', 'engagement', 'content_creation', 'monitoring', 'analytics', 'hybrid'],
        default='hybrid',
        help='Autonomous operation mode (default: hybrid)'
    )
    
    parser.add_argument(
        '--hours',
        type=float,
        default=1.0,
        help='Hours to run autonomous mode (default: 1.0)'
    )
    
    parser.add_argument(
        '--discovery',
        action='store_true',
        help='Run focused account discovery session'
    )
    
    parser.add_argument(
        '--engagement',
        action='store_true',
        help='Run engagement spree session'
    )
    
    parser.add_argument(
        '--content-creation',
        action='store_true',
        help='Run content creation session'
    )
    
    parser.add_argument(
        '--analytics',
        action='store_true',
        help='Run analytics deep dive session'
    )
    
    parser.add_argument(
        '--test-tools',
        action='store_true',
        help='Test all available tools systematically'
    )
    
    parser.add_argument(
        '--command',
        type=str,
        help='Execute a single command and exit'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Profile management
    parser.add_argument('--setup-login', action='store_true',
                       help='Setup persistent login (first time only)')
    parser.add_argument('--clear-login', action='store_true',
                       help='Clear saved login credentials')
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode')
    parser.add_argument('--no-persistent-profile', action='store_true',
                       help='Disable persistent profile (login each time)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # Handle profile management commands first (these need their own scraper instance)
    if args.setup_login:
        use_persistent = not args.no_persistent_profile
        scraper = TwitterScraper(headless=args.headless, use_persistent_profile=use_persistent)
        try:
            handle_setup_login(scraper)
        finally:
            scraper.close()
        return
        
    if args.clear_login:
        use_persistent = not args.no_persistent_profile
        scraper = TwitterScraper(headless=args.headless, use_persistent_profile=use_persistent)
        try:
            handle_clear_login(scraper)
        finally:
            scraper.close()
        return
    
    # For all other operations, let IntelligentTwitterAgent handle the scraper
    try:
        # Parse configuration options
        use_persistent = not args.no_persistent_profile
        
        # Determine what to run
        if args.interactive:
            print("🚀 Starting Interactive Mode...")
            asyncio.run(run_interactive(headless=args.headless, use_persistent_profile=use_persistent))
            
        elif args.autonomous:
            print(f"🚀 Starting Autonomous Mode ({args.mode}) for {args.hours} hours...")
            asyncio.run(run_autonomous(args.hours, args.mode, headless=args.headless, use_persistent_profile=use_persistent))
            
        elif args.discovery:
            print("🚀 Starting Discovery Session...")
            asyncio.run(run_discovery_session())
            
        elif args.engagement:
            print("🚀 Starting Engagement Session...")
            asyncio.run(run_engagement_spree())
            
        elif args.content_creation:
            print("🚀 Starting Content Creation Session...")
            asyncio.run(run_content_creation_session())
            
        elif args.analytics:
            print("🚀 Starting Analytics Deep Dive...")
            asyncio.run(run_analytics_deep_dive())
            
        elif args.test_tools:
            print("🚀 Starting Tool Testing...")
            asyncio.run(test_all_tools())
            
        elif args.command:
            print(f"🚀 Executing Single Command...")
            asyncio.run(run_single_command(args.command))
            
        else:
            # Default to interactive mode
            print("🚀 No mode specified, starting Interactive Mode...")
            print("Use --help to see all available options")
            asyncio.run(run_interactive(headless=args.headless, use_persistent_profile=use_persistent))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Launcher error: {e}")

def handle_setup_login(scraper):
    """Handle first-time login setup"""
    print("\n" + "="*60)
    print("🔐 TWITTER LOGIN SETUP")
    print("="*60)
    print("This will open a browser window for you to login to Twitter.")
    print("Your login session will be saved for future use.")
    print("="*60)
    
    if scraper.manual_login_helper():
        print("\n✅ Login setup complete!")
        print("You can now use the agent without logging in each time.")
    else:
        print("\n❌ Login setup failed. Please try again.")

def handle_clear_login(scraper):
    """Handle clearing saved login"""
    print("\n🗑️ Clearing saved login credentials...")
    scraper.clear_profile()
    print("✅ Done! You'll need to login again next time.")

if __name__ == "__main__":
    main() 