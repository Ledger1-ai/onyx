#!/usr/bin/env python3
"""
Dashboard Launcher Script

Launches the Twitter Agent Dashboard with proper setup and configuration.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_socketio
        import flask_cors
        return True
    except ImportError as e:
        print(f"Missing dependencies: {e}")
        print("Installing dashboard dependencies...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "dashboard_requirements.txt"
            ])
            print("Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install dependencies. Please install manually:")
            print("pip install -r dashboard_requirements.txt")
            return False

def main():
    """Main launcher function"""
    import signal
    
    print("🚀 ANUBIS Dashboard Starting...")
    
    # Check if we're in the right directory
    if not Path("dashboard_app.py").exists():
        print("❌ Error: dashboard_app.py not found")
        print("Please run this script from the project root directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Set up minimal logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduced verbosity from INFO to WARNING
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Suppress werkzeug and other verbose loggers
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('selenium').setLevel(logging.ERROR)
    
    try:
        # Import and run the dashboard
        from dashboard_app import TwitterAgentDashboard
        
        # Initialize dashboard
        dashboard = TwitterAgentDashboard()
        
        # Define signal handler
        def handle_shutdown(signum, frame):
            print(f"\n🛑 Shutdown signal received ({signum})...")
            dashboard.stop()
            sys.exit(0)
            
        # Register signal handlers
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        print("📊 Dashboard: http://localhost:5000")
        print("⏹️  Press Ctrl+C to stop")
        print("-" * 30)
        
        # Run the dashboard with minimal output
        dashboard.run(
            host='0.0.0.0',
            port=5000,
            debug=False
        )
        
    except KeyboardInterrupt:
        # This catch is redundant with signal handler but good as backup
        dashboard.stop()
        print("\n🛑 ANUBIS Dashboard stopped")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all project dependencies are installed")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 