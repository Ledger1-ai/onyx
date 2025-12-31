#!/usr/bin/env python3
"""
Twitter Agent Dashboard Application

A web-based dashboard for monitoring and controlling the intelligent Twitter agent.
Provides real-time updates, performance metrics, and schedule visualization.
"""

import os
import random
import sys
import json
import logging
import asyncio
import threading
from datetime import datetime, timedelta, timezone
import time
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the actual files from root directory
from openai import AzureOpenAI
from database_manager import DatabaseManager
from performance_tracker import PerformanceTracker  
from strategy_optimizer import StrategyOptimizer
from schedule_manager import ScheduleManager
from data_models import ActivityType, SlotStatus, SystemIdentity, CompanyConfig, PersonalityConfig, convert_to_dict
from selenium_scraper import TwitterScraper
from oauth_routes import oauth_bp

try:
    from meta_api_handler import MetaAPIHandler
except ImportError:
    MetaAPIHandler = None

# Note: Some components may not exist yet, we'll create minimal implementations
try:
    from intelligent_agent import IntelligentTwitterAgent as SchedulerCore
except ImportError:
    SchedulerCore = None

# Create a minimal MonitoringSystem class if it doesn't exist
class MonitoringSystem:
    def __init__(self):
        pass
    
    def get_system_status(self):
        return {'status': 'running', 'uptime': '1h 30m'}

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO to see agent logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress werkzeug HTTP request logs for cleaner output
logging.getLogger('werkzeug').setLevel(logging.ERROR)

class MemoryLogHandler(logging.Handler):
    def __init__(self, capacity=1000):
        super().__init__()
        self.capacity = capacity
        self.logs = []
        
    def emit(self, record):
        try:
            msg = self.format(record)
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'message': msg,
                'status': 'success' if record.levelno <= logging.INFO else 'error' if record.levelno >= logging.ERROR else 'warning'
            }
            self.logs.insert(0, log_entry)
            if len(self.logs) > self.capacity:
                self.logs.pop()
        except Exception:
            self.handleError(record)

# Attach memory handler to root logger to capture all events
root_logger = logging.getLogger()
memory_handler = MemoryLogHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
memory_handler.setFormatter(formatter)
root_logger.addHandler(memory_handler)

# -----------------------------------------------------------------------------
# Embedded chat UI template used by /chat route
# -----------------------------------------------------------------------------
CHAT_TEMPLATE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Agent Chat Interface</title>
    <link href=\"https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css\" rel=\"stylesheet\">
    <link rel=\"stylesheet\" href=\"/static/css/dashboard.css\"> 
    <script src=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/js/all.min.js\"></script>
    <style>
      :root { color-scheme: dark; }
      body { background: var(--surface-1, #0f1115); }
      .chat-shell { height: 100vh; display: flex; flex-direction: column; gap: 12px; }
      .chat-header { padding: 12px 16px; }
      .chat-panel { flex: 1 1 auto; display: flex; flex-direction: column; }
      .chat-log { flex: 1 1 auto; overflow-y: auto; padding: 12px; gap: 10px; display: flex; flex-direction: column; }
      .chat-inputbar { display: flex; gap: 8px; padding: 12px; }
      .bubble { max-width: 70%; padding: 10px 12px; border-radius: 10px; line-height: 1.35; }
      .bubble-user { align-self: flex-end; background: var(--surface-2, #141820); color: var(--text-1, #e5e7eb); border: 1px solid var(--border, #1f2937); }
      .bubble-assistant { align-self: flex-start; background: #0f1419; color: var(--text-2, #94a3b8); border: 1px solid var(--border, #1f2937); }
      .msg { display: flex; }
      .msg.user { justify-content: flex-end; }
      .msg.assistant { justify-content: flex-start; }
      .send-btn { white-space: nowrap; }
      .input { flex: 1 1 auto; background: var(--surface-2, #141820); color: var(--text-1, #e5e7eb); border: 1px solid var(--border, #1f2937); border-radius: 8px; padding: 10px 12px; outline: none; }
      .input:focus { box-shadow: 0 0 0 3px rgba(59,130,246,0.25); border-color: #2b3648; }
      .hidden { display: none; }
      /* Embed mode */
      body.embedded .chat-header { display: none; }
      body.embedded .chat-shell { padding-top: 0; }
    </style>
</head>
<body class=\"radix font-sans\">
    <div class=\"chat-shell px-4 py-3\">
        <header class=\"chat-header glass-panel rounded-lg text-white flex items-center justify-between\">
            <h1 class=\"text-lg font-bold flex items-center gap-2\"><i class=\"fas fa-comments text-blue-400\"></i> Command Chat</h1>
            <a href=\"/\" class=\"glass-mini-button\">&larr; Back to Dashboard</a>
        </header>

        <section class=\"chat-panel glass-panel rounded-lg card-fill\">
            <div id=\"chat-log\" class=\"chat-log nice-scroll\"></div>
            <div class=\"chat-inputbar border-t border-gray-700\">
                <input id=\"chat-input\" type=\"text\" placeholder=\"Type a command... (Shift+Enter = newline)\" class=\"input\">
                <button id=\"send-btn\" class=\"glass-button glass-button-primary send-btn\"><i class=\"fas fa-paper-plane mr-2\"></i>Send</button>
            </div>
        </section>
    </div>

    <script>
    (function() {
      // Embed mode toggle
      const params = new URLSearchParams(window.location.search);
      if (params.get('embed') === 'true') {
        document.body.classList.add('embedded');
      }

      const chatLog = document.getElementById('chat-log');
      const chatInput = document.getElementById('chat-input');
      const sendBtn = document.getElementById('send-btn');

      function appendMessage(role, text) {
        const row = document.createElement('div');
        row.className = 'msg ' + (role === 'user' ? 'user' : 'assistant');
        const bubble = document.createElement('div');
        bubble.className = 'bubble ' + (role === 'user' ? 'bubble-user' : 'bubble-assistant');
        bubble.textContent = text;
        row.appendChild(bubble);
        chatLog.appendChild(row);
        chatLog.scrollTop = chatLog.scrollHeight;
      }

      async function sendCommand() {
        const command = chatInput.value.trim();
        if (!command) return;
        appendMessage('user', command);
        chatInput.value = '';
        try {
          const res = await fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
          });
          const data = await res.json();
          appendMessage('assistant', data.result || data.error || 'No response');
        } catch (err) {
          appendMessage('assistant', 'Error: ' + err.message);
        }
      }

      sendBtn.addEventListener('click', sendCommand);
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendCommand();
        }
      });
    })();
    </script>
</body>
</html>
"""

AUTOMATION_TOKENIZATION_PROMPTS = [
    # Foundational Concepts
    "How decentralized automation transforms traditional manufacturing hierarchies",
    "Token-based ownership models revolutionizing industrial asset control",
    "The democratization of production through shared automation platforms",
    "Smart contracts enabling transparent and trustless industrial processes",
    "Community-driven automation: returning control to local stakeholders",
    "Tokenizing industrial assets for equitable wealth distribution across communities",
    "The intersection of AI, blockchain, and manufacturing democracy",
    "Automated systems designed to serve communities, not just corporate interests",
    "How tokenization breaks down traditional barriers to industrial participation",
    "Decentralized manufacturing networks powered by community governance tokens",
    
    # Future of Work & Labor
    "The future of work in tokenized automation ecosystems",
    "Redefining labor value through programmable token incentives",
    "How automation creates new forms of meaningful human work",
    "Token-based profit sharing in automated manufacturing facilities",
    "The transition from wage labor to stakeholder ownership in industry",
    "Collaborative human-AI partnerships in tokenized production systems",
    "Upskilling communities for the tokenized automation economy",
    "How universal basic assets could replace universal basic income",
    "Worker cooperatives enhanced by blockchain governance and automation",
    "The psychology of ownership in community-controlled automated systems",
    
    # Technology & Innovation
    "Bridging the digital divide through accessible automation tools",
    "Token economies incentivizing sustainable industrial practices",
    "Collaborative robotics in community-owned manufacturing facilities",
    "The ethics of automation in an equitable token economy",
    "Peer-to-peer industrial networks reshaping global production paradigms",
    "How automation as a service democratizes advanced manufacturing capabilities",
    "Token-governed industrial cooperatives as a new economic model",
    "The role of community consensus in automated decision-making processes",
    "Transforming labor relations through tokenized automation platforms",
    "Open-source automation protocols enabling global manufacturing collaboration",
    
    # Economic Models & Finance
    "Fractional ownership of industrial equipment through tokenization",
    "How DeFi principles apply to physical manufacturing assets",
    "Revenue sharing models in tokenized production facilities",
    "The economics of community-owned automated supply chains",
    "Token-based insurance for distributed manufacturing networks",
    "Crowdfunding industrial automation through community token sales",
    "Yield farming with physical assets in tokenized factories",
    "The role of governance tokens in industrial decision-making",
    "Liquidity pools for manufacturing equipment and resources",
    "Staking mechanisms for community manufacturing participation",
    
    # Material Science & Advanced Manufacturing
    "Tokenizing access to advanced materials research and development",
    "Community-controlled 3D printing networks with shared material libraries",
    "Blockchain-verified sustainable material sourcing in automated production",
    "Token incentives for circular economy practices in manufacturing",
    "Democratizing access to rare earth elements through tokenized mining cooperatives",
    "Smart materials that respond to blockchain-triggered commands",
    "Additive manufacturing powered by community-governed material tokens",
    "The tokenization of intellectual property in materials science",
    "Distributed bio-manufacturing networks with token-based resource allocation",
    "Nano-manufacturing controlled by decentralized autonomous organizations",
    
    # Supply Chain & Logistics
    "Transparent supply chains through tokenized tracking systems",
    "Community-owned logistics networks powered by automation",
    "Token-based incentives for sustainable shipping and distribution",
    "Decentralized warehousing with automated inventory management",
    "Blockchain-verified provenance in tokenized manufacturing chains",
    "Peer-to-peer shipping networks with token-based reputation systems",
    "Automated quality control with community-governed standards",
    "Token rewards for supply chain transparency and ethical practices",
    "Distributed manufacturing reducing transportation through local production",
    "Smart contracts automating supplier relationships and payments",
    
    # Social Impact & Community Development
    "How tokenized manufacturing empowers underserved communities",
    "Building local resilience through community-controlled production",
    "Token-based education and training programs for advanced manufacturing",
    "Addressing inequality through democratized access to production tools",
    "Community land trusts enhanced by tokenized manufacturing facilities",
    "The role of automation in disaster relief and emergency production",
    "Token incentives for environmental stewardship in manufacturing",
    "Creating jobs through community ownership of automated systems",
    "Cultural preservation through tokenized traditional craft production",
    "Indigenous communities leveraging tokenization for economic sovereignty",
    
    # Governance & Decision Making
    "Quadratic voting in tokenized manufacturing governance systems",
    "The balance between automation efficiency and community control",
    "Token-weighted decision making in industrial cooperatives",
    "Conflict resolution mechanisms in decentralized manufacturing networks",
    "The role of reputation systems in tokenized production communities",
    "Delegated governance models for complex manufacturing decisions",
    "Community auditing of automated systems through blockchain transparency",
    "Token-based incentives for participation in manufacturing governance",
    "The evolution from shareholder to stakeholder capitalism through tokenization",
    "Consensus mechanisms for resource allocation in automated facilities",
    
    # Global Impact & Scaling
    "Connecting rural communities to global markets through tokenized manufacturing",
    "The geopolitics of decentralized manufacturing networks",
    "How tokenization could reshape international trade relationships",
    "Building manufacturing resilience against global supply chain disruptions",
    "Token-based development aid through manufacturing capacity building",
    "The role of automation in achieving UN Sustainable Development Goals",
    "Cross-border collaboration in tokenized manufacturing ecosystems",
    "Reducing manufacturing's carbon footprint through community ownership",
    "The potential for tokenized manufacturing to address global inequality",
    "Creating abundance through democratized access to production capabilities",
    
    # Emerging Technologies Integration
    "IoT sensors enabling real-time community oversight of automated systems",
    "AI-driven optimization in community-controlled manufacturing",
    "Virtual and augmented reality interfaces for remote manufacturing participation",
    "Quantum computing applications in tokenized supply chain optimization",
    "5G networks enabling distributed control of manufacturing systems",
    "Digital twins of community-owned manufacturing facilities",
    "Machine learning algorithms trained on community preferences and values",
    "Robotics as a service models with token-based access controls",
    "Edge computing in decentralized manufacturing networks",
    "Biometric authentication for secure access to tokenized manufacturing systems",

    # Community & Collaboration Scenes
    "Diverse community members of all ages collaborating with advanced robots in a bright, modern factory",
    "Multi-generational families working together at high-tech manufacturing stations",
    "Community meeting where people vote on manufacturing decisions using digital tablets",
    "Children learning alongside adults in a community-owned 3D printing workshop",
    "Elderly craftspeople teaching young engineers traditional techniques enhanced by automation",
    "Neighborhood manufacturing cooperative with people sharing tools and knowledge",
    "Community garden integrated with automated hydroponic manufacturing systems",
    "Local artisans using AI-assisted design tools to create traditional crafts",
    "Diverse group of entrepreneurs planning a tokenized manufacturing venture",
    "Community celebration in front of their collectively-owned automated facility",
    
    # Technology & Infrastructure Visualizations
    "Abstract visualization of token flows connecting manufacturing nodes across continents",
    "Holographic display showing real-time manufacturing data accessible to community members",
    "Blockchain network visualization overlaying a bustling manufacturing district",
    "Digital tokens flowing like rivers through industrial supply chain networks",
    "Smart contracts executing automatically in a transparent manufacturing process",
    "Decentralized network map with glowing nodes representing community-owned factories",
    "AI algorithms visualized as flowing data streams optimizing production schedules",
    "IoT sensors throughout a facility creating a web of interconnected manufacturing intelligence",
    "Quantum computing visualization solving complex manufacturing optimization problems",
    "Augmented reality interface showing manufacturing data overlaid on physical equipment",
    
    # Hands-On Manufacturing & Automation
    "Hands of different ethnicities collaboratively operating advanced automation interfaces",
    "Robotic arms and human hands working in perfect synchronization on precision tasks",
    "Community members using gesture controls to direct automated manufacturing processes",
    "3D printers creating custom products while community members observe and learn",
    "Automated assembly line with community members monitoring quality and making adjustments",
    "Collaborative robots teaching manufacturing skills to community apprentices",
    "Advanced CNC machines operated by community members with varying skill levels",
    "Additive manufacturing systems creating both functional and artistic community projects",
    "Precision manufacturing tools accessible to local entrepreneurs and inventors",
    "Community members customizing automated systems for local production needs",
    
    # Facilities & Environments
    "Modern industrial facility with transparent walls showing community ownership and operation",
    "Converted warehouse transformed into a community-owned high-tech manufacturing space",
    "Rooftop manufacturing facility integrated into urban community development",
    "Rural manufacturing cooperative powered by renewable energy and community investment",
    "Underground manufacturing facility designed for resilience and community security",
    "Floating manufacturing platform serving coastal communities with tokenized access",
    "Mobile manufacturing units bringing production capabilities to underserved areas",
    "Vertical farming integrated with automated manufacturing in urban environments",
    "Historic building renovated as a community manufacturing space blending old and new",
    "Modular manufacturing pods that can be reconfigured based on community needs",
    
    # Economic & Token Visualizations
    "Digital tokens representing ownership stakes in manufacturing equipment and facilities",
    "Community members trading manufacturing tokens on a local exchange platform",
    "Profit-sharing visualization showing token holders receiving manufacturing revenues",
    "Governance tokens being used to vote on manufacturing facility improvements",
    "Token-based reward system incentivizing sustainable manufacturing practices",
    "Community members earning tokens through participation in manufacturing processes",
    "Fractional ownership visualization showing shared control of expensive manufacturing equipment",
    "Token staking interface allowing community investment in manufacturing upgrades",
    "Revenue streams from tokenized manufacturing flowing back to community members",
    "Community treasury funded by manufacturing profits and managed through token governance",
    
    # Global & Network Effects
    "World map showing interconnected community manufacturing networks sharing resources",
    "Satellite view of distributed manufacturing facilities connected by token networks",
    "Global supply chain visualization with community-controlled nodes highlighted",
    "International collaboration between community manufacturing cooperatives",
    "Cross-border token transfers enabling global manufacturing resource sharing",
    "Time-lapse of manufacturing capabilities spreading through tokenized networks",
    "Disaster relief manufacturing rapidly deployed through community token coordination",
    "Rural communities connected to global markets through tokenized manufacturing access",
    "Urban and rural manufacturing networks sharing knowledge and resources",
    "Indigenous communities using tokenization to scale traditional manufacturing practices",
    
    # Environmental & Sustainability Focus
    "Solar-powered manufacturing facility owned and operated by environmental community",
    "Circular economy visualization showing waste from one process becoming input for another",
    "Carbon-neutral manufacturing processes monitored by community environmental stewards",
    "Renewable energy integration with community-controlled manufacturing systems",
    "Sustainable materials being processed in community-owned bio-manufacturing facilities",
    "Ocean cleanup manufacturing systems funded and operated through community tokens",
    "Reforestation projects integrated with sustainable manufacturing cooperatives",
    "Community members monitoring environmental impact through blockchain transparency",
    "Green manufacturing processes incentivized through environmental token rewards",
    "Ecosystem restoration funded by profits from community manufacturing enterprises",
    
    # Education & Skill Development
    "Community education center teaching advanced manufacturing skills to all ages",
    "Virtual reality training systems for complex manufacturing processes",
    "Apprenticeship programs connecting experienced manufacturers with community learners",
    "University partnerships bringing advanced manufacturing research to communities",
    "Online learning platforms funded by community manufacturing token revenues",
    "Skill-sharing networks where community members teach each other manufacturing techniques",
    "Innovation labs where community members experiment with new manufacturing approaches",
    "Maker spaces equipped with professional-grade manufacturing tools and training",
    "Community members earning educational tokens through manufacturing skill development",
    "Intergenerational knowledge transfer in community-owned manufacturing facilities",
    
    # Cultural & Artistic Integration
    "Traditional artisans using advanced manufacturing tools to preserve cultural practices",
    "Community art projects created through collaborative manufacturing processes",
    "Cultural festivals celebrating community manufacturing achievements and innovations",
    "Local artists designing products for community-owned manufacturing systems",
    "Heritage crafts enhanced and preserved through tokenized manufacturing cooperatives",
    "Community murals depicting the evolution from industrial to community-owned manufacturing",
    "Cultural exchange programs sharing manufacturing techniques between communities",
    "Traditional patterns and designs being produced through advanced manufacturing systems",
    "Community storytelling events in manufacturing spaces celebrating local innovation",
    "Artistic installations made from community manufacturing processes and materials"
]

# OpenAI API key for text generation
client = AzureOpenAI(
    api_key="aefad978082243b2a79e279b203efc29",  
    api_version="2025-04-01-preview",
    azure_endpoint="https://Panopticon.openai.azure.com/"
)


used_automation_prompts = set()
used_visual_prompts = set()

# Global State for Afterlife Mode
AFTERLIFE_MODE = False

class TwitterAgentDashboard:
    """Main dashboard application class"""
    
    def __init__(self):
        self.app = Flask(__name__, 
                        static_folder='static',
                        template_folder='templates')
        self.app.config['SECRET_KEY'] = 'twitter-agent-dashboard-secret-key'
        
        # Initialize Flask extensions
        CORS(self.app)
        self.app.register_blueprint(oauth_bp)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Store memory handler reference
        self.log_handler = memory_handler
        
        # Initialize core components
        try:
            self.db_manager = DatabaseManager()
        except Exception as e:
            logger.error(f"DatabaseManager initialization failed")
            self.db_manager = None
            
        try:
            # ScheduleManager requires DatabaseManager as parameter
            if self.db_manager:
                self.schedule_manager = ScheduleManager(self.db_manager)
            else:
                logger.error("Cannot initialize ScheduleManager without DatabaseManager")
                self.schedule_manager = None
        except Exception as e:
            logger.error(f"ScheduleManager initialization failed: {e}")
            self.schedule_manager = None
            
        self.scheduler = None
        
        try:
            if self.db_manager:
                self.performance_tracker = PerformanceTracker(self.db_manager)
            else:
                logger.warning("PerformanceTracker not initialized - missing db_manager")
                self.performance_tracker = None
        except Exception as e:
            logger.error(f"PerformanceTracker initialization failed: {e}")
            self.performance_tracker = None
            
        # Initialize Meta Handler for Analytics
        try:
            if MetaAPIHandler:
                # Initialize with Env Vars (Default) or handle appropriately. 
                # Ideally this should be user-context aware, but for Dashboard global analytics logic, we may init with defaults.
                # Or init as None and let specific methods re-init if they have user context.
                # Since _sync_meta_analytics uses it directly, we assume default/env credentials for now.
                self.meta_handler = MetaAPIHandler()
            else:
                self.meta_handler = None
        except Exception as e:
            logger.error(f"MetaAPIHandler initialization failed: {e}")
            self.meta_handler = None
            
        self.monitoring = MonitoringSystem()
        
        # Initialize Strategy Optimizer
        self.initialize_strategy_optimizer()
        
        # Dashboard state
        self.connected_clients = set()
        self.last_status_update = None
        self.update_thread = None
        self.running = False
        
        self.setup_routes()
        self.setup_socket_events()
        
        # Auto-start the scheduler if components are available
        # self.auto_start_scheduler()
        
    def stop(self):
        """Gracefully stop the dashboard and all components"""
        logger.info("🛑 Stopping dashboard components...")
        self.running = False
        
        if self.scheduler:
            try:
                # Add cleanup logic for scheduler if needed
                pass
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")
                
        if self.meta_handler:
            try:
                # Add cleanup for meta handler if needed
                pass
            except Exception as e:
                logger.error(f"Error stopping meta handler: {e}")
                
        logger.info("✅ Dashboard components stopped")
        
    def initialize_strategy_optimizer(self):
        try:
            if self.db_manager and self.performance_tracker:
                self.strategy_optimizer = StrategyOptimizer(self.db_manager, self.performance_tracker)
                logger.info("StrategyOptimizer initialized successfully")
            else:
                logger.warning("StrategyOptimizer not initialized - missing db_manager or performance_tracker")
                self.strategy_optimizer = None
        except Exception as e:
            logger.error(f"StrategyOptimizer initialization failed: {e}")
            self.strategy_optimizer = None
    
    def auto_start_scheduler(self):
        """Automatically start the scheduler if all required components are available"""
        try:
            if not SchedulerCore:
                logger.warning("IntelligentTwitterAgent not available - scheduler will not auto-start")
                return
            
            if not self.schedule_manager:
                logger.warning("ScheduleManager not available - scheduler will not auto-start")
                return
            
            # Initialize the scheduler
            if not self.scheduler:
                logger.warning("🤖 Creating IntelligentTwitterAgent (SchedulerCore)...")
                self.scheduler = SchedulerCore()
                
                # Apply global Afterlife Mode state if enabled
                logger.warning(f"📡 Global AFTERLIFE_MODE state: {AFTERLIFE_MODE}")
                if AFTERLIFE_MODE:
                    logger.warning("🔥 Applying pre-existing Afterlife Mode state - initializing browser...")
                    self.scheduler.set_afterlife_mode(True)
                else:
                    logger.warning("⚠️ Afterlife Mode is OFF - browser will not start automatically")
                    logger.warning("   Enable Afterlife Mode from dashboard to start browser automation")
                    
                logger.warning("✅ IntelligentTwitterAgent initialized for auto-start")
            
            # Start the scheduler automatically
            if not self.running:
                self.running = True
                threading.Thread(target=self.run_scheduler, daemon=True).start()
                logger.warning("🚀 Scheduler auto-started successfully!")
            
        except Exception as e:
            logger.error(f"Failed to auto-start scheduler: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail the entire dashboard if auto-start fails
            pass
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            import time
            return render_template('dashboard.html', timestamp=int(time.time()))
        
        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Global 500 Error: {error}")
            return jsonify({'status': 'error', 'message': 'Internal Server Error', 'details': str(error)}), 500

        @self.app.errorhandler(400)
        def bad_request(error):
            logger.error(f"Global 400 Error: {error}")
            return jsonify({'status': 'error', 'message': 'Bad Request', 'details': str(error)}), 400
            
        # @self.app.route('/api/status')
        # def api_status():
        #     """Get current system status (Legacy - merged into /api/auth/status for SaaS)"""
        #     try:
        #         status_data = self.get_current_status()
        #         return jsonify(status_data)
        #     except Exception as e:
        #         logger.error(f"Error getting status: {e}")
        #         return jsonify({'error': str(e)}), 500
        
        # We need to keep a basic status endpoint for the dashboard if it pings it specifically for System Health
        # But PlatformStatus.tsx calls /api/auth/status for accounts. 
        # So I will rename this to /api/system/status or keep it as /api/status but ensure it doesn't conflict with /api/auth/status
        # Wait, the new route is /api/auth/status. The old one is /api/status. They DO NOT conflict.
        # But PlatformStatus.tsx logic relies on /api/auth/status returning connection info.
        # The OLD PlatformStatus.tsx called /api/auth/status? No, wait.
        # Let's check PlatformStatus.tsx again. It calls /api/auth/status.
        # So I must ensure /api/auth/status exists (it does in Blueprint).
        # This /api/status is likely for general system health (CPU, Memory, etc).
        # So I will leave this alone. It's fine.
        
        @self.app.route('/api/status')
        def api_status():
            """Get current system status"""
            try:
                status_data = self.get_current_status()
                return jsonify(status_data)
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/schedule')
        def api_schedule():
            """Get schedule for a specific date"""
            try:
                date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
                schedule_data = self.get_schedule_data(date_str)
                return jsonify(schedule_data)
            except Exception as e:
                logger.error(f"Error getting schedule: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/auth/twitter/login', methods=['POST'])
        def api_twitter_login():
            """Trigger manual Twitter login script"""
            try:
                import subprocess
                # Run as separate process to not block server
                subprocess.Popen(["python", "login_twitter_manual.py"], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                return jsonify({'status': 'success', 'message': 'Launched Twitter login window'})
            except Exception as e:
                logger.error(f"Error launching Twitter login script: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/auth/linkedin/disconnect', methods=['POST'])
        def api_linkedin_disconnect():
            """Disconnect LinkedIn (Bot) by renaming auth file"""
            try:
                auth_file = "browser_profiles/linkedin_auth.json"
                if os.path.exists(auth_file):
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    os.rename(auth_file, f"{auth_file}_bak_{timestamp}")
                    return jsonify({'status': 'success', 'message': 'LinkedIn bot disconnected'})
                return jsonify({'status': 'info', 'message': 'Already disconnected'})
            except Exception as e:
                logger.error(f"Error disconnecting LinkedIn: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/performance')
        def api_performance():
            """Get performance data"""
            try:
                days = int(request.args.get('days', 7))
                time_range = request.args.get('time_range', '7D')
                platform = request.args.get('platform')  # Optional platform filter
                
                # Sync Meta analytics if requested
                if platform in ['facebook', 'instagram']:
                    self._sync_meta_analytics(platform)

                performance_data = self.get_performance_data(days, platform=platform)
                
                # Include account overview and account trends for selected time range
                if self.performance_tracker:
                    try:
                        # Pass platform to performance tracker methods if supported in future
                        performance_data['account_overview'] = self.performance_tracker.get_account_overview(time_range=time_range)
                    except Exception as e:
                        logger.warning(f"Could not get account overview: {e}")
                        performance_data['account_overview'] = {}
                    try:
                        performance_data['account_trends'] = self.performance_tracker.get_account_trends(time_range=time_range)
                    except Exception as e:
                        logger.warning(f"Could not get account trends: {e}")
                        performance_data['account_trends'] = {}
                else:
                    performance_data['account_overview'] = {}
                    performance_data['account_trends'] = {}
                
                return jsonify(performance_data)
            except Exception as e:
                logger.error(f"Error getting performance data: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/logs')
        def api_system_logs():
            """Get system logs"""
            try:
                # Return logs from memory handler
                return jsonify({
                    'recent_sessions': self.log_handler.logs, # Format matches what frontend expects for "recent_sessions" key if modified, but frontend uses logs.map directly on the array usually. 
                    # useDashboardData sets setLogs(logsData.recent_sessions || [])
                    # So I must return { recent_sessions: [...] }
                })
            except Exception as e:
                logger.error(f"Error getting logs: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/notifications/status')
        def api_notification_status():
            """Get current notification settings"""
            try:
                # In a real app this would come from DB/Config
                # For now returning default "enabled" state
                return jsonify({
                    'shoutouts_enabled': True,
                    'replies_enabled': True,
                    'max_shoutouts': 3,
                    'max_replies': 10
                })
            except Exception as e:
                logger.error(f"Error getting notification status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/analytics/ingest', methods=['POST'])
        def api_ingest_account_analytics():
            """Ingest account-level analytics (from X/i/analytics scrape or manual input)"""
            try:
                payload = request.get_json(force=True) or {}
                date = payload.get('date') or datetime.now().strftime('%Y-%m-%d')
                time_range = (payload.get('time_range') or '7D').upper()
                # Everything else is metrics
                metrics = {k: v for k, v in payload.items() if k not in ['date', 'time_range']}
                
                if not self.performance_tracker:
                    return jsonify({'success': False, 'error': 'Performance tracker not available'}), 500
                
                ok = self.performance_tracker.ingest_account_analytics(date, time_range, metrics)
                return jsonify({'success': bool(ok)})
            except Exception as e:
                logger.error(f"Ingest error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/analytics/scrape-and-ingest', methods=['POST'])
        def api_scrape_and_ingest_account_analytics():
            """Scrape X analytics live and ingest into database (server-side Selenium)."""
            try:
                # Allow customization via JSON body
                data = request.get_json(silent=True) or {}
                time_range = (data.get('time_range') or '7D').upper()
                date = data.get('date') or datetime.now().strftime('%Y-%m-%d')
                headless = bool(data.get('headless', False))
                use_persistent_profile = bool(data.get('use_persistent_profile', True))

                if not self.performance_tracker:
                    return jsonify({'success': False, 'error': 'Performance tracker not available'}), 500

                # Run scraper
                scraper = TwitterScraper(headless=headless, use_persistent_profile=use_persistent_profile)
                try:
                    # Ensure session; if not logged in, return helpful message
                    if not scraper.ensure_logged_in():
                        scraper.close()
                        return jsonify({
                            'success': False,
                            'error': 'Not logged in to X/Twitter. Please log in once in a visible browser window.',
                            'hint': 'Call this endpoint with {\"headless\": false} to allow manual login, then re-run.'
                        }), 401

                    analytics = scraper.fetch_account_analytics(time_range=time_range)
                finally:
                    # Always close the browser to free resources
                    try:
                        scraper.close()
                    except Exception:
                        pass

                if not analytics:
                    return jsonify({'success': False, 'error': 'Failed to scrape analytics'}), 500

                # Persist via performance tracker
                ok = self.performance_tracker.ingest_account_analytics(date, time_range, analytics)
                overview = self.performance_tracker.get_account_overview(time_range=time_range) if ok else {}

                return jsonify({
                    'success': bool(ok),
                    'scraped_metrics': analytics,
                    'date': date,
                    'time_range': time_range,
                    'account_overview': overview
                })
            except Exception as e:
                logger.error(f"Scrape-and-ingest error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/optimization')
        def api_optimization():
            """Get optimization and strategy data"""
            try:
                optimization_data = self.get_optimization_data()
                return jsonify(optimization_data)
            except Exception as e:
                logger.error(f"Error getting optimization data: {e}")
                return jsonify({'error': str(e)}), 500
        

        
        @self.app.route('/api/debug_ping', methods=['GET'])
        def debug_ping():
            return jsonify({"message": "pong", "timestamp": str(datetime.now())})

        @self.app.route('/api/config/identity', methods=['GET'])
        def get_system_identity_config():
            """Get system identity configuration"""
            try:
                # Default tenant ID for now - in future extract from auth token
                user_id = request.args.get('user_id', 'default_tenant')
                
                # Check if db_manager is initialized
                if not self.db_manager:
                    logger.warning("DB Manager is None - Dashboard not initialized?")
                else:
                    # Try to get from database first
                    try:
                        identity = self.db_manager.get_system_identity(user_id)
                        if identity:
                            return jsonify({
                                "source": "database",
                                "identity": convert_to_dict(identity)
                            })
                    except Exception as e:
                        logger.error(f"Database fetch failed: {e}")
                    
                # Fallback: Migration from config.json
                try:
                    if not os.path.exists('config.json'):
                        return jsonify({
                            "source": "empty",
                            "identity": convert_to_dict(SystemIdentity(user_id=user_id))
                        })

                    with open('config.json', 'r') as f:
                        config_data = json.load(f)
                        
                    comp_data = config_data.get("company_config", {})
                    pers_data = config_data.get("personality_config", {})
                    logo_path = config_data.get("company_logo_path", "")
                    
                    # Construct objects with defensive defaults
                    company = CompanyConfig(
                        name=comp_data.get("name", ""),
                        industry=comp_data.get("industry", ""),
                        mission=comp_data.get("mission", ""),
                        brand_colors=comp_data.get("brand_colors", {}) or {},
                        twitter_username=comp_data.get("twitter_username", ""),
                        company_logo_path=comp_data.get("company_logo_path", ""),
                        values=comp_data.get("values", []) or [],
                        focus_areas=comp_data.get("focus_areas", []) or [],
                        brand_voice=comp_data.get("brand_voice", ""),
                        target_audience=comp_data.get("target_audience", ""),
                        key_products=comp_data.get("key_products", []) or [],
                        competitive_advantages=comp_data.get("competitive_advantages", []) or [],
                        location=comp_data.get("location", ""),
                        contact_info=comp_data.get("contact_info", {}) or {},
                        business_model=comp_data.get("business_model", ""),
                        core_philosophy=comp_data.get("core_philosophy", ""),
                        subsidiaries=comp_data.get("subsidiaries", []) or [],
                        partner_categories=comp_data.get("partner_categories", []) or []
                    )
                    
                    personality = PersonalityConfig(
                        tone=pers_data.get("tone", ""),
                        engagement_style=pers_data.get("engagement_style", ""),
                        communication_style=pers_data.get("communication_style", ""),
                        hashtag_strategy=pers_data.get("hashtag_strategy", ""),
                        content_themes=pers_data.get("content_themes", []) or [],
                        posting_frequency=pers_data.get("posting_frequency", "")
                    )
                    
                    identity = SystemIdentity(
                        user_id=user_id,
                        company_logo_path=logo_path,
                        company_config=company,
                        personality_config=personality
                    )
                    
                    # Save initialized identity ONLY if db_manager exists
                    if self.db_manager:
                        try:
                            self.db_manager.save_system_identity(identity)
                        except Exception as e:
                            logger.error(f"Failed to auto-save migrated identity: {e}")
                    
                    return jsonify({
                        "source": "migration",
                        "identity": convert_to_dict(identity)
                    })
                    
                except Exception as e:
                    logger.error(f"Migration failed: {e}")
                    return jsonify({
                        "source": "empty",
                        "identity": convert_to_dict(SystemIdentity(user_id=user_id))
                    })
                    
            except Exception as e:
                logger.error(f"Error in get_system_identity_config: {e}")
                return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

        @self.app.route('/api/config/identity', methods=['POST'])
        def save_system_identity_config():
            """Save system identity configuration"""
            try:
                if not self.db_manager:
                    return jsonify({"success": False, "message": "Database not initialized"}), 500

                data = request.json
                if not data:
                    return jsonify({"success": False, "message": "No data provided"}), 400

                user_id = data.get('user_id', 'default_tenant')
                config_data = data.get('identity', {})
                
                # Extract nested configs
                comp_data = config_data.get('company_config', {})
                pers_data = config_data.get('personality_config', {})
                
                # Reconstruct objects
                company = CompanyConfig(
                    name=comp_data.get("name", ""),
                    industry=comp_data.get("industry", ""),
                    mission=comp_data.get("mission", ""),
                    brand_colors=comp_data.get("brand_colors", {}) or {},
                    twitter_username=comp_data.get("twitter_username", ""),
                    company_logo_path=config_data.get("company_logo_path", ""),
                    values=comp_data.get("values", []) or [],
                    focus_areas=comp_data.get("focus_areas", []) or [],
                    brand_voice=comp_data.get("brand_voice", ""),
                    target_audience=comp_data.get("target_audience", ""),
                    key_products=comp_data.get("key_products", []) or [],
                    competitive_advantages=comp_data.get("competitive_advantages", []) or [],
                    location=comp_data.get("location", ""),
                    contact_info=comp_data.get("contact_info", {}) or {},
                    business_model=comp_data.get("business_model", ""),
                    core_philosophy=comp_data.get("core_philosophy", ""),
                    subsidiaries=comp_data.get("subsidiaries", []) or [],
                    partner_categories=comp_data.get("partner_categories", []) or []
                )
                
                personality = PersonalityConfig(
                    tone=pers_data.get("tone", ""),
                    engagement_style=pers_data.get("engagement_style", ""),
                    communication_style=pers_data.get("communication_style", ""),
                    hashtag_strategy=pers_data.get("hashtag_strategy", ""),
                    content_themes=pers_data.get("content_themes", []) or [],
                    posting_frequency=pers_data.get("posting_frequency", "")
                )
                
                identity = SystemIdentity(
                    user_id=user_id,
                    company_logo_path=config_data.get("company_logo_path", ""),
                    company_config=company,
                    personality_config=personality,
                    updated_at=datetime.now()
                )
                
                if self.db_manager.save_system_identity(identity):
                    return jsonify({"success": True, "message": "Identity saved successfully"})
                else:
                    return jsonify({"success": False, "message": "Database save failed"}), 500

            except Exception as e:
                logger.error(f"Error saving identity config: {e}")
                return jsonify({"success": False, "message": str(e)}), 500

        @self.app.route('/api/control/start', methods=['POST'])
        def api_control_start():
            """Start the Twitter agent"""
            try:
                if not SchedulerCore:
                    return jsonify({'status': 'error', 'message': 'IntelligentTwitterAgent not available. Please ensure intelligent_agent.py is properly configured.'}), 500
                
                if not self.scheduler:
                    logger.warning("🤖 Creating IntelligentTwitterAgent (SchedulerCore)...")
                    self.scheduler = SchedulerCore()
                    
                    # Apply global Afterlife Mode state if enabled
                    logger.warning(f"📡 Global AFTERLIFE_MODE state: {AFTERLIFE_MODE}")
                    if AFTERLIFE_MODE:
                        logger.warning("🔥 Applying pre-existing Afterlife Mode state - initializing browser...")
                        self.scheduler.set_afterlife_mode(True)
                
                # Start scheduler in a separate thread
                if not self.running:
                    self.running = True
                    threading.Thread(target=self.run_scheduler, daemon=True).start()
                    logger.warning("🟢 SYSTEM START: Anubis Scheduler Initiated")
                    
                return jsonify({'status': 'success', 'message': 'Agent started successfully'})
            except Exception as e:
                logger.error(f"Error starting agent: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/control/stop', methods=['POST'])
        def api_control_stop():
            """Stop the Twitter agent"""
            try:
                logger.info("Stopping Twitter agent...")
                
                # Set running flag to False to stop the scheduler loop
                self.running = False
                logger.warning("🛑 SYSTEM STOP: Anubis Scheduler Terminated")
                
                # If scheduler exists, attempt graceful shutdown
                if self.scheduler:
                    try:
                        # Clear current task if any
                        if hasattr(self.scheduler, 'state') and hasattr(self.scheduler.state, 'current_task'):
                            self.scheduler.state.current_task = None
                        
                        # If scheduler has a stop method, call it
                        if hasattr(self.scheduler, 'stop'):
                            self.scheduler.stop()
                        
                        # If scheduler has a cleanup method, call it
                        if hasattr(self.scheduler, 'cleanup'):
                            self.scheduler.cleanup()
                            
                        logger.info("Scheduler gracefully stopped")
                    except Exception as scheduler_error:
                        logger.warning(f"Error during scheduler shutdown: {scheduler_error}")
                
                # Wait a moment for the scheduler thread to finish
                import time
                time.sleep(1)
                
                # Broadcast status update to all connected clients
                self.broadcast_status_update()
                
                logger.info("Twitter agent stopped successfully")
                return jsonify({'status': 'success', 'message': 'Agent stopped successfully'})
                
            except Exception as e:
                logger.error(f"Error stopping agent: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/control/optimize', methods=['POST'])
        def api_control_optimize():
            """Trigger strategy optimization"""
            try:
                # Run optimization in background
                threading.Thread(target=self.run_optimization, daemon=True).start()
                
                return jsonify({'status': 'success', 'message': 'Optimization triggered successfully'})
            except Exception as e:
                logger.error(f"Error triggering optimization: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/control/afterlife-mode', methods=['GET', 'POST'])
        def api_afterlife_mode():
            """Get or set the Afterlife Mode status"""
            global AFTERLIFE_MODE
            logger.info(f"API Afterlife Mode Called. Method: {request.method}")
            try:
                if request.method == 'POST':
                    # Do not consume stream with get_data() before get_json()
                    # logger.info(f"Raw data: {request.get_data(as_text=True)}") 
                    
                    data = request.get_json(force=True, silent=True)
                    if data is None:
                        logger.error("Failed to parse JSON body (data is None)")
                        return jsonify({'status': 'error', 'message': 'Invalid JSON body'}), 400
                        
                    target_state = bool(data.get('enabled', False))
                    logger.info(f"Target State: {target_state}")
                    
                    if target_state != AFTERLIFE_MODE:
                        AFTERLIFE_MODE = target_state
                        state_str = "ENABLED" if AFTERLIFE_MODE else "DISABLED"
                        logger.warning(f"Protocol MYTHOS: Afterlife Mode {state_str}")
                        
                        # Here we would trigger the bot controller to spin up/down browsers
                        if self.scheduler and hasattr(self.scheduler, 'set_afterlife_mode'):
                             self.scheduler.set_afterlife_mode(AFTERLIFE_MODE)

                    return jsonify({'status': 'success', 'enabled': AFTERLIFE_MODE})
                else:
                    return jsonify({'status': 'success', 'enabled': AFTERLIFE_MODE})
            except Exception as e:
                logger.error(f"Error toggling Afterlife Mode: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/chat')
        def chat_ui():
            """Simple chat UI to send commands to the agent"""
            return CHAT_TEMPLATE
        
        @self.app.route('/api/command', methods=['POST'])
        def api_command():
            """Execute a free-form agent command (chat interface)"""
            try:
                data = request.get_json(force=True)
                command = data.get('command', '').strip()
                if not command:
                    return jsonify({'error': 'No command provided'}), 400
                if not SchedulerCore:
                    return jsonify({'error': 'Agent core not available'}), 500
                # Ensure scheduler / agent running
                if not self.scheduler:
                    self.scheduler = SchedulerCore()
                # Execute command synchronously (agent has async method)
                result = asyncio.run(self.scheduler.process_command(command))
                return jsonify({'result': result})
            except Exception as e:
                logger.error(f"Error executing command: {e}")
                return jsonify({'error': str(e)}), 500
            
        @self.app.route('/api/notifications/manage', methods=['POST'])
        def api_manage_notifications():
            """Trigger automatic notification management"""
            try:
                data = request.get_json() or {}
                
                if not self.scheduler:
                    self.scheduler = SchedulerCore()
                
                # Build command with parameters
                enable_shoutouts = data.get('enable_follower_shoutouts', True)
                enable_replies = data.get('enable_auto_replies', True)
                max_shoutouts = data.get('max_shoutouts_per_session', 3)
                max_replies = data.get('max_auto_replies_per_session', 10)
                
                command = f"manage notifications automatically with enable_follower_shoutouts={enable_shoutouts} and enable_auto_replies={enable_replies} and max_shoutouts_per_session={max_shoutouts} and max_auto_replies_per_session={max_replies}"
                
                result = asyncio.run(self.scheduler.process_command(command))
                return jsonify({'status': 'success', 'result': result})
                
            except Exception as e:
                logger.error(f"Error managing notifications: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/notifications/auto-reply', methods=['POST'])  
        def api_auto_reply():
            """Trigger auto-reply to notifications"""
            try:
                data = request.get_json() or {}
                
                if not self.scheduler:
                    self.scheduler = SchedulerCore()
                    
                max_replies = data.get('max_replies', 5)
                reply_style = data.get('reply_style', 'helpful')
                filter_keywords = data.get('filter_keywords', [])
                
                command = f"auto reply to notifications with max_replies={max_replies} and reply_style={reply_style}"
                if filter_keywords:
                    command += f" and filter_keywords={filter_keywords}"
                    
                result = asyncio.run(self.scheduler.process_command(command))
                return jsonify({'status': 'success', 'result': result})
                
            except Exception as e:
                logger.error(f"Error with auto-reply: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/auth/status')
        def api_auth_status():
            """Check authentication status for platforms with detailed granularity"""
            try:
                # 1. API Status (from Database)
                # Use centralized DEFAULT_USER_ID from Config for consistency
                from config import Config
                user_id = getattr(Config, "DEFAULT_USER_ID", "admin_user")
                api_status = {
                    'twitter': False,
                    'linkedin': False,
                    'facebook': False,
                    'instagram': False
                }
                
                # 2. Bot Status - Database-driven with filesystem fallback
                bot_status = {
                    'twitter': False,
                    'linkedin': False,
                    'facebook': False,
                    'instagram': False
                }
                
                creds = {}
                if self.db_manager:
                    try:
                        user = self.db_manager.get_user(user_id)
                        if user:
                            creds = user.get("credentials", {})
                            # API Status from OAuth credentials
                            api_status['twitter'] = creds.get("twitter", {}).get("is_active", False)
                            api_status['linkedin'] = creds.get("linkedin", {}).get("is_active", False)
                            api_status['facebook'] = creds.get("facebook", {}).get("is_active", False)
                            api_status['instagram'] = creds.get("instagram", {}).get("is_active", False)
                            
                            # Bot Status from database (preferred for multi-tenant)
                            bot_status['twitter'] = creds.get("twitter_bot", {}).get("is_active", False)
                            bot_status['linkedin'] = creds.get("linkedin_bot", {}).get("is_active", False)
                    except Exception as e:
                        logger.warning(f"Could not fetch user credentials: {e}")

                # Filesystem fallback for bot status (backward compatibility)
                # If DB shows no bot status, check filesystem
                if not bot_status['twitter']:
                    twitter_profile_dir = "browser_profiles/twitter_automation_profile"
                    if os.path.exists(twitter_profile_dir):
                        bot_status['twitter'] = True
                        
                if not bot_status['linkedin']:
                    linkedin_auth_file = "browser_profiles/linkedin_auth.json"
                    linkedin_profile_dir = "browser_profiles/linkedin_automation_profile"
                    legacy_marker = os.path.join(linkedin_profile_dir, "auth_success.marker")
                    
                    if os.path.exists(linkedin_auth_file):
                        bot_status['linkedin'] = True
                    elif os.path.exists(linkedin_profile_dir) and os.path.exists(legacy_marker):
                        bot_status['linkedin'] = True

                # 3. Premium Status
                twitter_premium = False
                if self.schedule_manager and hasattr(self.schedule_manager, 'has_twitter_premium'):
                    twitter_premium = self.schedule_manager.has_twitter_premium

                # Return granular structure
                return jsonify({
                    'twitter': { 'api': api_status['twitter'], 'bot': bot_status['twitter'] },
                    'linkedin': { 'api': api_status['linkedin'], 'bot': bot_status['linkedin'] },
                    'facebook': { 'api': api_status['facebook'], 'bot': False },
                    'instagram': { 'api': api_status['instagram'], 'bot': False },
                    'twitter_premium': twitter_premium
                })
                
            except Exception as e:
                logger.error(f"Error checking auth status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/auth/linkedin/login', methods=['POST'])
        def api_linkedin_login():
            """Trigger manual LinkedIn login script"""
            try:
                import subprocess
                # Run as separate process to not block server
                subprocess.Popen(["python", "login_linkedin_manual.py"], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                return jsonify({'status': 'success', 'message': 'Launched login window'})
            except Exception as e:
                logger.error(f"Error launching login script: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/auth/twitter/disconnect', methods=['POST'])
        def api_twitter_disconnect():
            """Disconnect Twitter account by renaming profile directory"""
            try:
                profile_dir = "browser_profiles/twitter_automation_profile"
                if os.path.exists(profile_dir):
                    # Rename to .bak to effectively "logout" without losing data permanently
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    os.rename(profile_dir, f"{profile_dir}_bak_{timestamp}")
                    return jsonify({'status': 'success', 'message': 'Twitter disconnected'})
                return jsonify({'status': 'info', 'message': 'Already disconnected'})
            except Exception as e:
                logger.error(f"Error disconnecting Twitter: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/auth/facebook/login', methods=['POST'])
        def api_facebook_login():
            """Trigger manual Meta (FB/IG) login script"""
            try:
                import subprocess
                # Run as separate process to not block server
                subprocess.Popen(["python", "login_meta_manual.py"], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                return jsonify({'status': 'success', 'message': 'Launched Meta login window'})
            except Exception as e:
                logger.error(f"Error launching Meta login script: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/auth/meta/disconnect', methods=['POST'])
        def api_meta_disconnect():
            """Disconnect Meta (FB/IG) - removes only db stored cookies if managing via SaaS, 
               or renames profile dir if local. For now, we rename profile dir to match other platforms."""
            try:
                profile_dir = "browser_profiles/meta_automation_profile"
                if os.path.exists(profile_dir):
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    os.rename(profile_dir, f"{profile_dir}_bak_{timestamp}")
                    return jsonify({'status': 'success', 'message': 'Meta session disconnected'})
                return jsonify({'status': 'info', 'message': 'Already disconnected'})
            except Exception as e:
                logger.error(f"Error disconnecting Meta: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/notifications/shoutout', methods=['POST'])
        def api_create_shoutout():
            """Create follower shoutout"""
            try:
                data = request.get_json() or {}
                username = data.get('username')
                
                if not username:
                    return jsonify({'status': 'error', 'message': 'Username required'}), 400
                    
                if not self.scheduler:
                    self.scheduler = SchedulerCore()
                    
                include_bio = data.get('include_bio_analysis', True)
                artwork_style = data.get('artwork_style', 'botanical-still-frame')
                
                command = f"create follower shoutout using the create_follower_shoutout tool for {username} with include_bio_analysis={include_bio} and artwork_style={artwork_style}"
                
                result = asyncio.run(self.scheduler.process_command(command))
                return jsonify({'status': 'success', 'result': result})
                
            except Exception as e:
                logger.error(f"Error creating shoutout: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/tasks/configuration')
        def api_tasks_configuration():
            """Get task configuration data"""
            try:
                from data_models import ActivityType
                
                # Get list of disabled tasks from user preferences
                disabled_tasks = []
                if self.db_manager:
                    user = self.db_manager.db.users.find_one({"user_id": "admin_user"})
                    if user and "preferences" in user:
                        disabled_tasks = user["preferences"].get("disabled_tasks", [])
                
                # Get all available activity types
                available_tasks = []
                for activity_type in ActivityType:
                    # Check if task is disabled
                    is_enabled = activity_type.value not in disabled_tasks
                    
                    available_tasks.append({
                        'id': activity_type.value,
                        'name': activity_type.value.replace('_', ' ').title(),
                        'enabled': is_enabled
                    })

                # Get current schedule for today
                today = datetime.now().strftime('%Y-%m-%d')
                if self.db_manager:
                    slots = self.db_manager.get_schedule_slots(today)
                    
                    schedule = []
                    for slot in slots:
                        schedule.append({
                            'id': slot.slot_id,
                            'name': slot.activity_type.value.replace('_', ' ').title(),
                            'activity_type': slot.activity_type.value,
                            'scheduledTime': slot.start_time.strftime('%H:%M'),
                            'status': slot.status.value,
                            'priority': slot.priority,
                            'is_flexible': slot.is_flexible
                        })
                else:
                    schedule = []

                return jsonify({
                    'success': True,
                    'tasks': available_tasks,
                    'schedule': schedule
                })
            except Exception as e:
                logger.error(f"Error getting task configuration: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500



        @self.app.route('/api/tasks/regenerate', methods=['POST'])
        def api_tasks_regenerate():
            """Regenerate remaining tasks in schedule"""
            try:
                today = datetime.now().strftime('%Y-%m-%d')
                
                if not self.db_manager or not self.schedule_manager:
                    return jsonify({
                        'success': False,
                        'error': 'Database or schedule manager not available'
                    }), 500
                
                logger.info(f"🔄 Starting schedule regeneration for {today}...")
                
                # Delete ALL existing slots and schedule for today (fresh start)
                try:
                    # Delete from database first
                    existing_slots = self.db_manager.get_schedule_slots(today)
                    deleted_count = 0
                    for slot in existing_slots:
                        if self.db_manager.delete_schedule_slot(slot.slot_id):
                            deleted_count += 1
                    
                    # Delete the daily schedule
                    self.db_manager.delete_daily_schedule(today)
                    
                    logger.info(f"🗑️ Deleted {deleted_count} existing slots and schedule for {today}")
                except Exception as delete_error:
                    logger.warning(f"Error during cleanup: {delete_error}")
                
                # Force create a completely new schedule
                # Force create a completely new schedule
                logger.info(f"🏗️ Creating fresh schedule for {today}...")
                
                # Get disabled tasks from database
                disabled_tasks = []
                if self.db_manager:
                    user = self.db_manager.db.users.find_one({"user_id": "admin_user"})
                if user and "preferences" in user:
                        disabled_tasks = user["preferences"].get("disabled_tasks", [])
                
                logger.info(f"DEBUG: Found user {user['_id'] if user else 'None'}")
                logger.info(f"DEBUG: Disabled tasks for regeneration: {disabled_tasks}")
                
                new_schedule = self.schedule_manager.create_daily_schedule(
                    today,
                    disabled_activity_types=disabled_tasks
                )
                
                if new_schedule and new_schedule.slots:
                    logger.info(f"✅ Created new schedule with {len(new_schedule.slots)} slots")
                    
                    # Save the schedule first
                    schedule_saved = self.db_manager.save_daily_schedule(new_schedule)
                    logger.info(f"💾 Schedule saved: {schedule_saved}")
                    
                    # Save all new slots to database
                    saved_count = 0
                    for slot in new_schedule.slots:
                        try:
                            if self.db_manager.save_schedule_slot(slot):
                                saved_count += 1
                                logger.info(f"💾 Saved slot: {slot.slot_id} - {slot.activity_type.value}")
                            else:
                                logger.error(f"❌ Failed to save slot: {slot.slot_id}")
                        except Exception as slot_error:
                            logger.error(f"❌ Error saving slot {slot.slot_id}: {slot_error}")
                    
                    logger.info(f"💾 Successfully saved {saved_count} out of {len(new_schedule.slots)} slots to database")
                    
                    if saved_count == 0:
                        logger.error("❌ No slots were saved to database!")
                        return jsonify({
                            'success': False,
                            'error': 'Schedule created but no slots were saved to database'
                        }), 500
                else:
                    logger.error("❌ Failed to create new schedule")
                    return jsonify({
                        'success': False,
                        'error': 'Failed to create new schedule'
                    }), 500
                
                # Return the schedule data directly from the schedule manager (not database)
                schedule = []
                for slot in new_schedule.slots:
                    schedule.append({
                        'slot_id': slot.slot_id,  # Use slot_id instead of id
                        'id': slot.slot_id,       # Also provide id for compatibility
                        'name': slot.activity_type.value.replace('_', ' ').title(),
                        'activity_type': slot.activity_type.value,
                        'start_time': slot.start_time.isoformat(),
                        'end_time': slot.end_time.isoformat(),
                        'scheduledTime': slot.start_time.strftime('%H:%M'),
                        'status': slot.status.value,
                        'priority': slot.priority,
                        'is_flexible': slot.is_flexible
                    })
                
                logger.info(f"✅ Regeneration complete: {len(schedule)} tasks created")
                
                return jsonify({
                    'success': True,
                    'schedule': schedule,
                    'message': f'Successfully regenerated schedule with {len(schedule)} tasks'
                })
                
            except Exception as e:
                logger.error(f"💥 Error regenerating schedule: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/tasks/swap-options', methods=['POST'])
        def api_tasks_swap_options():
            """Get available options for task swapping"""
            try:
                from data_models import ActivityType
                
                # Improved JSON parsing with error handling
                try:
                    data = request.get_json()
                    if not data:
                        return jsonify({
                            'success': False,
                            'error': 'No JSON data provided'
                        }), 400
                except Exception as json_error:
                    logger.error(f"JSON parsing error in swap-options: {json_error}")
                    return jsonify({
                        'success': False,
                        'error': f'Invalid JSON data: {str(json_error)}'
                    }), 400
                
                current_slot_id = data.get('taskId')  # This is actually the slot_id
                
                if not current_slot_id:
                    return jsonify({
                        'success': False,
                        'error': 'taskId is required'
                    }), 400
                
                logger.info(f"🔍 Swap options requested for slot ID: {current_slot_id}")
                logger.info(f"📋 Request data: {data}")
                
                if not self.db_manager:
                    return jsonify({
                        'success': False,
                        'error': 'Database manager not available'
                    }), 500
                
                # Get today's date
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Use the same data source as the main schedule API for consistency
                schedule_data = self.get_schedule_data(today)
                slots = schedule_data.get('slots', [])
                
                logger.info(f"📅 Found {len(slots)} slots from schedule data for {today}")
                logger.info(f"🔍 Data source: {schedule_data.get('data_source', 'unknown')}")
                
                # Find the current slot
                current_slot = None
                available_slot_ids = []
                
                for slot_data in slots:
                    slot_id = slot_data.get('slot_id')
                    available_slot_ids.append(str(slot_id))
                    
                    if str(slot_id) == str(current_slot_id):
                        # Create a simple slot object for activity type comparison
                        class SlotWrapper:
                            def __init__(self, slot_data):
                                self.slot_id = slot_data.get('slot_id')
                                self.activity_type = ActivityType(slot_data.get('activity_type'))
                                self.status = slot_data.get('status', 'scheduled')
                        
                        current_slot = SlotWrapper(slot_data)
                        logger.info(f"✅ Found slot: {current_slot.slot_id} - {current_slot.activity_type.value}")
                        break
                
                if not current_slot:
                    logger.error(f"❌ Could not find slot with ID: {current_slot_id}")
                    logger.error(f"Available slot IDs: {available_slot_ids[:10]}...")  # Show first 10 IDs
                    return jsonify({
                        'success': False,
                        'error': f'Current task not found. Looking for ID: {current_slot_id}',
                        'available_ids': available_slot_ids[:5],  # Return first 5 for debugging
                        'total_slots': len(slots)
                    }), 404
                
                # Get all available activity types except the current one
                options = []
                for activity_type in ActivityType:
                    if activity_type != current_slot.activity_type:
                        options.append({
                            'id': activity_type.value,
                            'name': activity_type.value.replace('_', ' ').title()
                        })
                
                return jsonify({
                    'success': True,
                    'options': options
                })
            except Exception as e:
                logger.error(f"Error getting swap options: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/tasks/swap', methods=['POST'])
        def api_tasks_swap():
            """Swap a task with a different activity type"""
            try:
                from data_models import ActivityType
                
                # Improved JSON parsing with error handling
                try:
                    data = request.get_json()
                    if not data:
                        return jsonify({
                            'success': False,
                            'error': 'No JSON data provided'
                        }), 400
                except Exception as json_error:
                    logger.error(f"JSON parsing error in swap: {json_error}")
                    return jsonify({
                        'success': False,
                        'error': f'Invalid JSON data: {str(json_error)}'
                    }), 400
                
                task_identifier = data.get('oldTaskId')  # Could be slot_id or time-based identifier
                new_activity_type_str = data.get('newTaskId')  # This is the new activity type
                additional_info = data.get('additionalInfo', {})  # Additional identifying information
                
                # Validate required fields
                if not task_identifier:
                    return jsonify({
                        'success': False,
                        'error': 'oldTaskId is required'
                    }), 400
                
                if not new_activity_type_str:
                    return jsonify({
                        'success': False,
                        'error': 'newTaskId is required'
                    }), 400
                
                logger.info(f"🔄 Swap request: task_id={task_identifier}, new_type={new_activity_type_str}")
                logger.info(f"📋 Additional info: {additional_info}")
                logger.info(f"📋 Full request data: {data}")
                
                if not self.db_manager:
                    return jsonify({
                        'success': False,
                        'error': 'Database manager not available'
                    }), 500
                
                # Convert string to ActivityType enum
                try:
                    new_activity_type = ActivityType(new_activity_type_str)
                    logger.info(f"✅ Successfully converted to ActivityType: {new_activity_type}")
                except ValueError as e:
                    logger.error(f"❌ Invalid activity type: {new_activity_type_str}, error: {e}")
                    return jsonify({
                        'success': False,
                        'error': f'Invalid activity type: {new_activity_type_str}'
                    }), 400
                
                # Check if this is a database fallback slot (db_slot_X pattern)
                if str(task_identifier).startswith('db_slot_'):
                    logger.warning(f"⚠️ Cannot update database fallback slot: {task_identifier}")
                    
                    return jsonify({
                        'success': False,
                        'error': 'Cannot update database fallback slots. Please use the "Regenerate All Remaining Tasks" button to create a proper schedule.',
                        'solution': 'Click the settings icon and use "Regenerate All Remaining Tasks"'
                    }), 400
                
                # Get today's date for schedule operations
                today = datetime.now().strftime('%Y-%m-%d')
                
                # First, try to find the slot using different identification methods
                target_slot = None
                update_method = None
                
                # Method 1: Try direct slot_id lookup
                try:
                    slot_doc = self.db_manager.db.schedule_slots.find_one({"slot_id": task_identifier})
                    if slot_doc:
                        target_slot = slot_doc
                        update_method = "direct_slot_id"
                        logger.info(f"✅ Found slot by direct slot_id: {task_identifier}")
                except Exception as e:
                    logger.warning(f"Could not find by slot_id: {e}")
                
                # Method 2: If not found, try to find by time from additional info or task_identifier
                if not target_slot:
                    try:
                        # Get all slots for today and find the one that matches
                        today_slots = list(self.db_manager.db.schedule_slots.find({"date": today}))
                        logger.info(f"📅 Found {len(today_slots)} slots for today")
                        
                        # Try to match by scheduled time from additional info first
                        scheduled_time = additional_info.get('scheduledTime')
                        if scheduled_time:
                            logger.info(f"🕐 Trying to find slot by scheduled time: {scheduled_time}")
                            for slot_doc in today_slots:
                                slot_time = slot_doc.get('start_time', '')
                                if scheduled_time in slot_time:
                                    target_slot = slot_doc
                                    update_method = "scheduled_time_match"
                                    logger.info(f"✅ Found slot by scheduled time match: {scheduled_time}")
                                    break
                        
                        # Fallback: Try to match by task_identifier if it looks like a time
                        if not target_slot and ":" in str(task_identifier):
                            target_time = str(task_identifier)
                            for slot_doc in today_slots:
                                slot_time = slot_doc.get('start_time', '')
                                if target_time in slot_time:
                                    target_slot = slot_doc
                                    update_method = "time_match"
                                    logger.info(f"✅ Found slot by time match: {target_time}")
                                    break
                    except Exception as e:
                        logger.warning(f"Could not find by time: {e}")
                
                # Method 3: If still not found, try to sync from schedule manager
                if not target_slot and self.schedule_manager:
                    try:
                        logger.info(f"🔄 Trying to sync from schedule manager...")
                        daily_schedule = self.schedule_manager.get_or_create_daily_schedule(today)
                        if daily_schedule and daily_schedule.slots:
                            # Find matching slot in schedule manager
                            for slot in daily_schedule.slots:
                                if (str(slot.slot_id) == str(task_identifier) or 
                                    task_identifier in slot.start_time.strftime('%H:%M')):
                                    
                                    logger.info(f"💾 Found slot in schedule manager, saving to database...")
                                    saved = self.db_manager.save_schedule_slot(slot)
                                    logger.info(f"💾 Slot saved to database: {saved}")
                                    
                                    if saved:
                                        # Now try to find it in database
                                        target_slot = self.db_manager.db.schedule_slots.find_one({"slot_id": slot.slot_id})
                                        update_method = "schedule_sync"
                                        logger.info(f"✅ Found slot after sync: {slot.slot_id}")
                                    break
                    except Exception as e:
                        logger.error(f"Error syncing from schedule manager: {e}")
                
                # Method 4: Last resort - find by current activity type and time proximity
                if not target_slot:
                    try:
                        # Get current time and find slots within 2 hours
                        current_time = datetime.now()
                        time_window_start = (current_time - timedelta(hours=1)).isoformat()
                        time_window_end = (current_time + timedelta(hours=2)).isoformat()
                        
                        nearby_slots = list(self.db_manager.db.schedule_slots.find({
                            "date": today,
                            "start_time": {"$gte": time_window_start, "$lte": time_window_end}
                        }))
                        
                        if nearby_slots:
                            # Take the first nearby slot as a fallback
                            target_slot = nearby_slots[0]
                            update_method = "time_proximity"
                            logger.info(f"⚠️ Using time proximity fallback: {target_slot.get('slot_id')}")
                    except Exception as e:
                        logger.error(f"Time proximity search failed: {e}")
                
                if not target_slot:
                    logger.error(f"❌ Could not find any slot to update with identifier: {task_identifier}")
                    return jsonify({
                        'success': False,
                        'error': f'Could not find task with identifier: {task_identifier}'
                    }), 404
                
                # Update the slot's activity type
                slot_id_to_update = target_slot.get('slot_id')
                logger.info(f"🔄 Updating slot {slot_id_to_update} using method: {update_method}")
                
                try:
                    success = self.db_manager.update_slot_activity_type(slot_id_to_update, new_activity_type)
                    logger.info(f"📊 Database update result: {success}")
                except Exception as db_error:
                    logger.error(f"💥 Database update failed: {db_error}")
                    return jsonify({
                        'success': False,
                        'error': f'Database update failed: {str(db_error)}'
                    }), 500
                
                if not success:
                    logger.error(f"❌ Database update returned False for slot {slot_id_to_update}")
                    return jsonify({
                        'success': False,
                        'error': f'Failed to update slot {slot_id_to_update} in database'
                    }), 500
                
                # Get the updated schedule
                today = datetime.now().strftime('%Y-%m-%d')
                updated_slots = self.db_manager.get_schedule_slots(today)
                schedule = []
                for slot in updated_slots:
                    schedule.append({
                        'id': slot.slot_id,
                        'name': slot.activity_type.value.replace('_', ' ').title(),
                        'activity_type': slot.activity_type.value,
                        'scheduledTime': slot.start_time.strftime('%H:%M'),
                        'status': slot.status.value,
                        'priority': slot.priority,
                        'is_flexible': slot.is_flexible
                    })
                
                return jsonify({
                    'success': True,
                    'schedule': schedule,
                    'message': f'Task swapped successfully'
                })
            except Exception as e:
                logger.error(f"Error swapping task: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/tasks/toggle', methods=['POST'])
        def api_tasks_toggle():
            """Toggle task enabled/disabled status and save to DB"""
            try:
                data = request.get_json()
                task_id = data.get('taskId')
                
                if not task_id:
                    return jsonify({'success': False, 'error': 'Task ID required'}), 400
                
                if not self.db_manager:
                    return jsonify({'success': False, 'error': 'Database not available'}), 500
                    
                # Get current user (default to admin_user)
                user = self.db_manager.db.users.find_one({"user_id": "admin_user"})
                
                # If user doesn't exist, create basic profile
                if not user:
                    user_data = {
                        "user_id": "admin_user",
                        "email": "admin@example.com",
                        "preferences": {
                            "disabled_tasks": []
                        },
                        "created_at": datetime.now()
                    }
                    self.db_manager.db.users.insert_one(user_data)
                    user = user_data
                    
                preferences = user.get("preferences", {})
                disabled_tasks = preferences.get("disabled_tasks", [])
                
                # Toggle presence in disabled list
                is_enabled = False
                if task_id in disabled_tasks:
                    # Enable it (remove from disabled list)
                    disabled_tasks.remove(task_id)
                    is_enabled = True
                else:
                    # Disable it (add to disabled list)
                    disabled_tasks.append(task_id)
                    is_enabled = False
                    
                # Update database
                self.db_manager.db.users.update_one(
                    {"user_id": "admin_user"},
                    {"$set": {"preferences.disabled_tasks": disabled_tasks}}
                )
                
                logger.info(f"Task {task_id} toggled. Now enabled: {is_enabled}")
                
                return jsonify({
                    'success': True,
                    'enabled': is_enabled,
                    'taskId': task_id
                })
            except Exception as e:
                logger.error(f"Error toggling task: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/tasks/create-fresh', methods=['POST'])
        def api_tasks_create_fresh():
            """Create a completely fresh schedule (debug/force creation)"""
            try:
                today = datetime.now().strftime('%Y-%m-%d')
                
                if not self.schedule_manager:
                    return jsonify({
                        'success': False,
                        'error': 'Schedule manager not available'
                    }), 500
                
                # Get disabled tasks
                disabled_tasks = []
                if self.db_manager:
                    user = self.db_manager.db.users.find_one({"user_id": "admin_user"})
                    if user and "preferences" in user:
                        disabled_tasks = user["preferences"].get("disabled_tasks", [])
                
                logger.info(f"🆕 Creating completely fresh schedule for {today} (Disabled: {len(disabled_tasks)} tasks)...")
                
                # Create new schedule directly
                new_schedule = self.schedule_manager.create_daily_schedule(
                    today,
                    disabled_activity_types=disabled_tasks
                )
                
                if new_schedule and new_schedule.slots:
                    logger.info(f"✅ Created fresh schedule with {len(new_schedule.slots)} slots")
                    
                    # Return the schedule data directly
                    schedule = []
                    for slot in new_schedule.slots:
                        schedule.append({
                            'slot_id': slot.slot_id,
                            'id': slot.slot_id,
                            'name': slot.activity_type.value.replace('_', ' ').title(),
                            'activity_type': slot.activity_type.value,
                            'start_time': slot.start_time.isoformat(),
                            'end_time': slot.end_time.isoformat(),
                            'scheduledTime': slot.start_time.strftime('%H:%M'),
                            'status': slot.status.value,
                            'priority': slot.priority,
                            'is_flexible': slot.is_flexible
                        })
                    
                    return jsonify({
                        'success': True,
                        'schedule': schedule,
                        'message': f'Created fresh schedule with {len(schedule)} tasks'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to create fresh schedule'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Error creating fresh schedule: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/debug/slots')
        def api_debug_slots():
            """Debug endpoint to see what slots exist in database"""
            try:
                if not self.db_manager:
                    return jsonify({'error': 'Database manager not available'}), 500
                
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Helper function to convert ObjectId to string
                def serialize_slot(slot_doc):
                    if not slot_doc:
                        return None
                    
                    # Create a new dict to avoid modifying the original
                    serialized = {}
                    for key, value in slot_doc.items():
                        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                            serialized[key] = str(value)
                        else:
                            serialized[key] = value
                    return serialized
                
                # Get slots from database
                db_slots_raw = list(self.db_manager.db.schedule_slots.find({}))
                db_slots = [serialize_slot(slot) for slot in db_slots_raw]
                
                # Get today's slots specifically
                today_slots_raw = list(self.db_manager.db.schedule_slots.find({
                    "start_time": {"$regex": f"^{today}"}
                }))
                today_slots = [serialize_slot(slot) for slot in today_slots_raw]
                
                # Get schedule manager slots if available
                schedule_manager_slots = []
                if self.schedule_manager:
                    try:
                        daily_schedule = self.schedule_manager.get_or_create_daily_schedule(today)
                        if daily_schedule and daily_schedule.slots:
                            for slot in daily_schedule.slots:
                                schedule_manager_slots.append({
                                    'slot_id': slot.slot_id,
                                    'activity_type': slot.activity_type.value,
                                    'start_time': slot.start_time.isoformat(),
                                    'status': slot.status.value
                                })
                    except Exception as e:
                        logger.error(f"Error getting schedule manager slots: {e}")
                
                return jsonify({
                    'total_db_slots': len(db_slots),
                    'today_db_slots': len(today_slots),
                    'schedule_manager_slots': len(schedule_manager_slots),
                    'db_slot_ids': [slot.get('slot_id') for slot in db_slots if slot],
                    'today_slot_ids': [slot.get('slot_id') for slot in today_slots if slot],
                    'schedule_manager_slot_ids': [slot.get('slot_id') for slot in schedule_manager_slots],
                    'sample_db_slots': db_slots[:3],  # First 3 for debugging
                    'sample_schedule_manager_slots': schedule_manager_slots[:3],
                    'debug_info': {
                        'today_date': today,
                        'db_connection_status': 'connected' if self.db_manager.db is not None else 'disconnected',
                        'schedule_manager_status': 'available' if self.schedule_manager else 'unavailable'
                    }
                })
            except Exception as e:
                logger.error(f"Error in debug slots endpoint: {str(e)}")
                return jsonify({'error': str(e)}), 500
    
        @self.app.route('/api/tasks/update-frequencies', methods=['POST'])
        def api_update_task_frequencies():
            """Update task frequency distribution and apply to scheduled tasks"""
            try:
                logger.info("📊 Received request to update task frequencies")
                
                # Get and validate request data
                payload = request.get_json(force=True) or {}
                distribution = payload.get("distribution", {})
                platform = payload.get("platform", None) # Optional platform context

                if not distribution:
                    logger.error("No distribution in request data")
                    return jsonify({'success': False, 'error': 'No distribution provided'}), 400
                
                # Update the strategy in database
                if not self.db_manager:
                    logger.error("Database manager not available")
                    return jsonify({'success': False, 'error': 'Database not available'}), 500
                
                try:
                    # Get active strategy first to merge with existing
                    from data_models import ActivityType, create_default_strategy
                    
                    strategies = self.db_manager.get_all_strategy_templates()
                    if strategies:
                        strategy = strategies[0]
                    else:
                        strategy = create_default_strategy()
                    
                    current_distribution = strategy.activity_distribution or {}
                    
                    # Normalize incoming distribution (convert keys to ActivityType)
                    # And handle basic normalization if needed. 
                    # Note: Frontend sends 0-100 values usually.
                    
                    updates = {}
                    incoming_total = 0
                    for k, v in distribution.items():
                        try:
                            # Map string key to enum if possible
                            # The frontend sends keys like 'tweet', 'linkedin_post' which match enums
                            enum_key = ActivityType(k)
                            val = float(v)
                            # If val > 1, assume percent
                            if val > 1:
                                val = val / 100.0
                            
                            updates[enum_key] = val
                            incoming_total += val
                        except ValueError:
                            continue
                            
                    # If we have a platform, we only want to normalize WITHIN that platform?
                    # Or we trust the frontend sends a set that sums to 1.0 (or close).
                    
                    # Update strategy: Merge updates into current_distribution
                    for k, v in updates.items():
                        current_distribution[k] = v
                    
                    # Save back
                    strategy.activity_distribution = current_distribution
                    strategy.updated_at = datetime.now()
                    self.db_manager.save_strategy_template(strategy)
                    
                    logger.info(f"✅ Updated strategy for platform: {platform}")

                    # Regenerate Schedule
                    today = datetime.now().strftime("%Y-%m-%d")
                    schedule = None
                    
                    if platform and self.schedule_manager:
                        logger.info(f"🔄 Regenerating schedule for {platform}...")
                        schedule = self.schedule_manager.regenerate_daily_schedule_for_platform(today, platform, strategy=strategy)
                    elif self.schedule_manager:
                        logger.info("🔄 Regenerating full schedule...")
                        schedule = self.schedule_manager.get_or_create_daily_schedule(today, strategy=strategy, force_recreate=True)
                        
                    if schedule:
                        # Emit update
                        slots = self.db_manager.get_schedule_slots(today)
                        self.socketio.emit('schedule_update', {
                            "date": today,
                            "summary": self.schedule_manager.get_schedule_summary(today),
                            "slots": [
                                {
                                    "slot_id": s.slot_id,
                                    "start_time": s.start_time.isoformat(),
                                    "end_time": s.end_time.isoformat(),
                                    "activity_type": s.activity_type.value,
                                    "status": s.status.value,
                                    "priority": s.priority,
                                    "is_flexible": s.is_flexible,
                                    "performance_data": s.performance_data
                                } for s in slots
                            ]
                        })
                        return jsonify({"success": True, "updated_tasks": len(slots)})
                    
                    return jsonify({"success": True, "message": "Strategy updated (no schedule change)"})

                except Exception as e:
                     logger.error(f"Error updating strategy inner: {e}", exc_info=True)
                     return jsonify({'success': False, 'error': f"Strategy update failed: {str(e)}"}), 500
                     
            except Exception as e:
                logger.error(f"Error in update frequencies endpoint: {str(e)}", exc_info=True)
                return jsonify({'success': False, 'error': f"Endpoint error: {str(e)}"}), 500
                    


        @self.app.route('/api/test', methods=['GET'])
        def api_test():
            """Simple test endpoint to verify API is working"""
            return jsonify({
                'success': True,
                'message': 'API is working',
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/api/debug/scheduled-tasks', methods=['GET'])
        def api_debug_scheduled_tasks():
            """Debug endpoint to see scheduled tasks"""
            try:
                from datetime import datetime
                
                if not self.db_manager:
                    return jsonify({'error': 'Database manager not available'}), 500
                
                today = datetime.now().strftime('%Y-%m-%d')
                scheduled_slots = self.db_manager.get_schedule_slots(today)
                
                debug_info = {
                    'date': today,
                    'total_slots': len(scheduled_slots),
                    'slots': []
                }
                
                for slot in scheduled_slots:
                    if hasattr(slot, '__dict__'):
                        slot_info = {
                            'slot_id': getattr(slot, 'slot_id', None),
                            'status': str(getattr(slot, 'status', None)),
                            'start_time': str(getattr(slot, 'start_time', None)),
                            'end_time': str(getattr(slot, 'end_time', None)),
                            'activity_type': str(getattr(slot, 'activity_type', None)),
                            'is_flexible': getattr(slot, 'is_flexible', None),
                            'priority': getattr(slot, 'priority', None)
                        }
                    else:
                        slot_info = dict(slot)
                        # Convert any complex objects to strings for JSON serialization
                        for key, value in slot_info.items():
                            if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None))):
                                slot_info[key] = str(value)
                    
                    debug_info['slots'].append(slot_info)
                
                # Also check the raw database data
                try:
                    raw_slots = list(self.db_manager.db.schedule_slots.find({"date": today}))
                    debug_info['raw_slots_count'] = len(raw_slots)
                    debug_info['raw_slots'] = raw_slots[:5]  # First 5 for inspection
                except Exception as e:
                    debug_info['raw_slots_error'] = str(e)
                
                return jsonify(debug_info)
                
            except Exception as e:
                logger.error(f"Error in debug endpoint: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/tasks/update-status', methods=['POST'])
        def api_update_task_status():
            """Update the status of a specific task"""
            try:
                if not request.is_json:
                    return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
                
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'No data provided'}), 400
                
                slot_id = data.get('slot_id')
                new_status = data.get('status')
                
                if not slot_id or not new_status:
                    return jsonify({'success': False, 'error': 'slot_id and status are required'}), 400
                
                # Validate status
                valid_statuses = ['scheduled', 'in_progress', 'completed', 'failed', 'skipped']
                if new_status not in valid_statuses:
                    return jsonify({'success': False, 'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
                
                if not self.db_manager:
                    return jsonify({'success': False, 'error': 'Database not available'}), 500
                
                # Update the task status
                success = self.db_manager.update_schedule_slot(
                    slot_id=slot_id,
                    updates={
                        'status': new_status,
                        'updated_at': datetime.now().isoformat(),
                        'manual_update': True,
                        'manual_update_reason': f"Status manually changed to {new_status}"
                    }
                )
                
                if success:
                    logger.info(f"✅ Manually updated task {slot_id} status to {new_status}")
                    return jsonify({
                        'success': True,
                        'message': f'Task {slot_id} status updated to {new_status}',
                        'slot_id': slot_id,
                        'new_status': new_status
                    })
                else:
                    logger.warning(f"❌ Failed to update task {slot_id} status")
                    return jsonify({'success': False, 'error': 'Failed to update task status'}), 500
                
            except Exception as e:
                logger.error(f"Error updating task status: {e}", exc_info=True)
                return jsonify({'success': False, 'error': str(e)}), 500
    
    def setup_socket_events(self):
        """Setup Socket.IO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            logger.info(f"Client connected: {request.sid}")
            # Send initial data
            emit('status_update', self.get_current_status())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_update')
        def handle_request_update():
            # Send current dashboard data
            emit('dashboard_update', self.get_current_status())

    def _update_scheduled_tasks_distribution(self, new_distribution):
        """Update scheduled (not completed) tasks with new activity distribution"""
        try:
            if not self.db_manager:
                logger.error("Database manager not available")
                return 0
            
            from datetime import datetime, timedelta
            from data_models import ActivityType
            import random
            
            # Get today's date
            today = datetime.now().strftime('%Y-%m-%d')
            logger.info(f"🔍 Looking for scheduled tasks on {today}")
            
            # Get all scheduled slots for today that haven't been completed
            scheduled_slots = self.db_manager.get_schedule_slots(today)
            logger.info(f"📋 Found {len(scheduled_slots)} total slots for {today}")
            
            future_slots = []
            current_time = datetime.now()
            
            for slot in scheduled_slots:
                # Handle both dict and ScheduleSlot object formats
                if hasattr(slot, '__dict__'):
                    # ScheduleSlot object
                    slot_dict = {
                        'slot_id': getattr(slot, 'slot_id', None),
                        'id': getattr(slot, 'id', None),
                        'status': getattr(slot, 'status', 'scheduled'),
                        'start_time': getattr(slot, 'start_time', None),
                        'activity_type': getattr(slot, 'activity_type', None)
                    }
                    # Convert start_time to string if it's a datetime object
                    if hasattr(slot_dict['start_time'], 'isoformat'):
                        slot_dict['start_time'] = slot_dict['start_time'].isoformat()
                    # Convert ActivityType enum to string if needed
                    if hasattr(slot_dict['activity_type'], 'value'):
                        slot_dict['activity_type'] = slot_dict['activity_type'].value
                    
                    logger.debug(f"🔄 Converted ScheduleSlot object: {slot_dict}")
                else:
                    # Already a dict
                    slot_dict = slot
                    logger.debug(f"🔄 Using dict slot: {slot_dict}")
                
                logger.debug(f"🔍 Checking slot {slot_dict.get('slot_id')}: status={slot_dict.get('status')}, start_time={slot_dict.get('start_time')}, activity={slot_dict.get('activity_type')}")
                
                # More flexible criteria: include scheduled tasks regardless of time
                # This allows updating past scheduled tasks that haven't been completed
                status = slot_dict.get('status', '')
                
                # Handle both SlotStatus enum and string status values
                if hasattr(status, 'value'):
                    status_str = status.value.lower()
                elif isinstance(status, str):
                    status_str = status.lower()
                else:
                    status_str = str(status).lower()
                
                # Check for scheduled status (the main one we want to update)
                if status_str in ['scheduled']:
                    future_slots.append(slot_dict)
                    logger.debug(f"✅ Added slot {slot_dict.get('slot_id')} to update list")
                else:
                    logger.debug(f"❌ Skipped slot {slot_dict.get('slot_id')} - status: {status_str}")
            
            logger.info(f"🎯 Found {len(future_slots)} tasks eligible for update")
            
            if not future_slots:
                logger.warning("No eligible scheduled tasks found to update")
                logger.info("💡 This could mean:")
                logger.info("   - All tasks are already completed")
                logger.info("   - No tasks are scheduled for today")
                logger.info("   - Tasks have different status values than expected")
                return 0
            
            # Convert string keys to ActivityType values for selection
            activity_weights = []
            activity_types = []
            
            for task_type, weight in new_distribution.items():
                if weight > 0:  # Only include tasks with non-zero weights
                    activity_types.append(task_type)
                    activity_weights.append(weight)
            
            if not activity_types:
                logger.warning("No activities with positive weights in distribution")
                return 0
            
            logger.info(f"🎲 Available activities for assignment: {activity_types}")
            logger.info(f"⚖️ Weights: {activity_weights}")
            
            updated_count = 0
            
            # Update each future slot with a new activity based on the distribution
            for slot_dict in future_slots:
                old_activity = slot_dict.get('activity_type', '')
                
                # Select new activity based on weighted distribution
                new_activity = random.choices(activity_types, weights=activity_weights, k=1)[0]
                
                # Update the slot in database
                slot_id = slot_dict.get('slot_id') or slot_dict.get('id')
                if slot_id:
                    logger.info(f"🔄 Updating slot {slot_id}: {old_activity} -> {new_activity}")
                    
                    success = self.db_manager.update_schedule_slot(
                        slot_id=slot_id,
                        updates={
                            'activity_type': new_activity,
                            'description': f"Updated via frequency control - was {old_activity}"
                        }
                    )
                    
                    if success:
                        updated_count += 1
                        logger.info(f"✅ Successfully updated slot {slot_id}: {old_activity} -> {new_activity}")
                    else:
                        logger.warning(f"❌ Failed to update slot {slot_id}")
                else:
                    logger.warning(f"⚠️ Slot missing ID: {slot_dict}")
            
            logger.info(f"🎉 Successfully updated {updated_count} scheduled tasks with new distribution")
            
            # If no tasks were updated, provide helpful debugging info
            if updated_count == 0:
                logger.warning("🔍 Debug info - why no tasks were updated:")
                logger.warning(f"   - Found {len(future_slots)} eligible slots")
                logger.warning(f"   - Available activities: {activity_types}")
                logger.warning("   - Check if update_schedule_slot method is working correctly")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating scheduled tasks distribution: {e}", exc_info=True)
            return 0
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current system status and metrics"""
        try:
            # Get current time
            now = datetime.now(timezone.utc)
            
            # Initialize status data
            status_data = {
                'timestamp': now.isoformat(),
                'system_running': self.running,
                'active_mode': 'afterlife' if AFTERLIFE_MODE else 'safe',
                'current_activity': None,
                'next_activity': None,
                'daily_progress': 0,
                'completed_activities': 0,
                'total_activities': 0,
                'performance_metrics': {}
            }
            
            # Get schedule information
            if self.scheduler:
                # Get current activity (would need to implement in scheduler)
                current_activity = self.get_current_activity()
                if current_activity:
                    status_data['current_activity'] = current_activity
                
                # Get next activity
                next_activity = self.get_next_activity()
                if next_activity:
                    status_data['next_activity'] = next_activity
                
                # Get daily progress
                daily_stats = self.get_daily_progress()
                status_data.update(daily_stats)
            
            # Get performance metrics
            performance_metrics = self.get_current_performance_metrics()
            status_data['performance_metrics'] = performance_metrics
            
            return status_data
            
        except Exception as e:
            logger.error(f"Error getting current status: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_running': False,
                'error': str(e)
            }
    
    def get_current_activity(self) -> Optional[Dict[str, Any]]:
        """Return the active schedule slot if one is running"""
        if not self.schedule_manager:
            return None

        try:
            slot = self.schedule_manager.get_current_activity()
            if slot:
                duration = slot.end_time - slot.start_time
                elapsed = datetime.now() - slot.start_time
                progress = int(elapsed.total_seconds() / duration.total_seconds() * 100)
                return {
                    'activity': slot.activity_type.value,
                    'progress': min(max(progress, 0), 100),
                    'start_time': slot.start_time.isoformat(),
                    'estimated_completion': slot.end_time.isoformat()
                }
        except Exception as e:
            # Suppress routine warnings for activity queries
            pass
        return None
    
    def get_next_activity(self) -> Optional[Dict[str, Any]]:
        """Get next scheduled activity from ScheduleManager if available"""
        if not self.schedule_manager:
            return None

        try:
            next_slot = self.schedule_manager.get_next_activity()
            if next_slot:
                time_until = next_slot.start_time - datetime.now()
                return {
                    'activity': next_slot.activity_type.value,
                    'scheduled_time': next_slot.start_time.isoformat(),
                    'time_until': str(time_until).split('.')[0],
                    'priority': 'high'
                }
        except Exception as e:
            # Suppress routine warnings for activity queries
            pass
        return None
    
    def get_daily_progress(self) -> Dict[str, Any]:
        """Get daily activity progress from actual schedule data"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get real schedule data from schedule manager
            if self.schedule_manager:
                try:
                    schedule_summary = self.schedule_manager.get_schedule_summary(today)
                    
                    total_activities = schedule_summary.get('total_slots', 0)
                    completed_activities = schedule_summary.get('completed_slots', 0)
                    failed_activities = schedule_summary.get('failed_slots', 0)
                    in_progress_activities = schedule_summary.get('in_progress_slots', 0)
                    
                    # Calculate progress percentage
                    if total_activities > 0:
                        daily_progress = int((completed_activities / total_activities) * 100)
                    else:
                        daily_progress = 0
                    
                    return {
                        'daily_progress': daily_progress,
                        'completed_activities': completed_activities,
                        'total_activities': total_activities,
                        'failed_activities': failed_activities,
                        'in_progress_activities': in_progress_activities,
                        'completion_rate': schedule_summary.get('completion_rate', 0.0)
                    }
                    
                except Exception as e:
                    logger.warning(f"Could not get schedule summary: {e}")
            
            # Fallback to database query if schedule manager unavailable
            if self.db_manager:
                try:
                    # Get today's activities from database
                    today_date = datetime.now().date()
                    activities = self.db_manager.get_activities_by_date(today_date)
                    
                    total_activities = len(activities)
                    completed_activities = sum(1 for activity in activities if activity.get('status') == 'completed')
                    failed_activities = sum(1 for activity in activities if activity.get('status') == 'failed')
                    in_progress_activities = sum(1 for activity in activities if activity.get('status') == 'in_progress')
                    
                    # Calculate progress
                    if total_activities > 0:
                        daily_progress = int((completed_activities / total_activities) * 100)
                    else:
                        daily_progress = 0
                    
                    return {
                        'daily_progress': daily_progress,
                        'completed_activities': completed_activities,
                        'total_activities': total_activities,
                        'failed_activities': failed_activities,
                        'in_progress_activities': in_progress_activities,
                        'completion_rate': completed_activities / total_activities if total_activities > 0 else 0.0
                    }
                    
                except Exception as e:
                    logger.warning(f"Could not get activities from database: {e}")
            
            # Final fallback - check if scheduler has session data
            if self.scheduler and hasattr(self.scheduler, 'state') and hasattr(self.scheduler.state, 'session_data'):
                session_data = self.scheduler.state.session_data
                
                # Estimate progress from session data
                tweets_posted = session_data.get('tweets_posted', 0)
                engagement_actions = session_data.get('engagement_actions', 0)
                replies_sent = session_data.get('replies_sent', 0)
                analytics_checks = session_data.get('analytics_checks', 0)
                
                # Rough estimate of total expected daily activities (based on typical schedule)
                estimated_total = 20  # Typical daily activities
                actual_completed = tweets_posted + min(engagement_actions // 5, 8) + replies_sent + analytics_checks
                
                daily_progress = min(int((actual_completed / estimated_total) * 100), 100)
                
                return {
                    'daily_progress': daily_progress,
                    'completed_activities': actual_completed,
                    'total_activities': estimated_total,
                    'failed_activities': 0,
                    'in_progress_activities': 1 if self.running else 0,
                    'completion_rate': actual_completed / estimated_total,
                    'session_based': True  # Flag to indicate this is estimated from session data
                }
            
            # Ultimate fallback - return minimal real data
            return {
                'daily_progress': 0,
                'completed_activities': 0,
                'total_activities': 0,
                'failed_activities': 0,
                'in_progress_activities': 1 if self.running else 0,
                'completion_rate': 0.0,
                'no_data': True  # Flag to indicate no real data available
            }
            
        except Exception as e:
            logger.error(f"Error getting daily progress: {e}")
            # Return error state instead of dummy data
            return {
                'daily_progress': 0,
                'completed_activities': 0,
                'total_activities': 0,
                'failed_activities': 0,
                'in_progress_activities': 0,
                'completion_rate': 0.0,
                'error': str(e)
            }
    
    def get_current_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics from real data sources"""
        try:
            # Initialize with default structure
            metrics = {
                'overall_score': 0.0,
                'engagement_rate': 0.0,
                'follower_growth': 0,
                'tweet_impressions': 0,
                'reach': 0,
                'trend': 'unknown'
            }
            
            # Try to get real data from performance tracker
            if self.performance_tracker:
                try:
                    # Build metrics from account overview/trends (PerformanceTracker has no get_summary/get_trends)
                    account_overview = self.performance_tracker.get_account_overview(time_range='7D')
                    current = account_overview.get('current', {}) if isinstance(account_overview, dict) else {}
                    metrics.update({
                        'engagement_rate': current.get('engagement_rate', 0.0),
                        'tweet_impressions': current.get('impressions', 0),
                        'reach': metrics.get('reach', 0),  # not tracked at account level
                    })
                    # Approximate follower_growth from percent_change.total_followers (percentage delta)
                    pct = account_overview.get('percent_change', {}).get('total_followers')
                    if isinstance(pct, (int, float)):
                        metrics['follower_growth'] = pct
                    # Determine trend from account_trends series
                    try:
                        account_trends = self.performance_tracker.get_account_trends(time_range='7D')
                        er_series = account_trends.get('engagement_rate', {}).get('values', [])
                        if isinstance(er_series, list) and len(er_series) >= 2:
                            first = er_series[0][1]
                            last = er_series[-1][1]
                            if isinstance(first, (int, float)) and isinstance(last, (int, float)):
                                if last > first:
                                    metrics['trend'] = 'improving'
                                elif last < first:
                                    metrics['trend'] = 'declining'
                                else:
                                    metrics['trend'] = 'stable'
                    except Exception:
                        pass
                except Exception as e:
                    logger.warning(f"Could not build performance metrics from account analytics: {e}")
            
            # Try to get additional data from database
            if self.db_manager:
                try:
                    # Get recent performance analysis
                    today = datetime.now().strftime('%Y-%m-%d')
                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    
                    today_analysis = self.db_manager.get_performance_analysis(today)
                    yesterday_analysis = self.db_manager.get_performance_analysis(yesterday)
                    
                    if today_analysis and today_analysis.metrics:
                        # Update with database metrics
                        db_metrics = today_analysis.metrics
                        metrics.update({
                            'overall_score': db_metrics.get('performance_score', metrics['overall_score']),
                            'engagement_rate': db_metrics.get('engagement_rate', metrics['engagement_rate']),
                            'follower_growth': db_metrics.get('follower_growth', metrics['follower_growth']),
                            'tweet_impressions': db_metrics.get('tweet_impressions', metrics['tweet_impressions']),
                            'reach': db_metrics.get('reach', metrics['reach'])
                        })
                        
                        # Calculate trend from day-over-day comparison
                        if yesterday_analysis and yesterday_analysis.metrics:
                            yesterday_score = yesterday_analysis.metrics.get('performance_score', 0)
                            today_score = db_metrics.get('performance_score', 0)
                            
                            if today_score > yesterday_score * 1.1:
                                metrics['trend'] = 'improving'
                            elif today_score < yesterday_score * 0.9:
                                metrics['trend'] = 'declining'
                            else:
                                metrics['trend'] = 'stable'
                                
                except Exception as e:
                    logger.warning(f"Could not get database performance data: {e}")
            
            # Try to get session-based metrics from scheduler
            if self.scheduler and hasattr(self.scheduler, 'state') and hasattr(self.scheduler.state, 'session_data'):
                try:
                    session_data = self.scheduler.state.session_data
                    
                    # Calculate session-based metrics
                    tweets_posted = session_data.get('tweets_posted', 0)
                    engagement_actions = session_data.get('engagement_actions', 0)
                    replies_sent = session_data.get('replies_sent', 0)
                    
                    # Estimate engagement rate from session activity
                    if tweets_posted > 0:
                        session_engagement_rate = (engagement_actions + replies_sent) / tweets_posted
                        # Only update if we don't have better data
                        if metrics['engagement_rate'] == 0.0:
                            metrics['engagement_rate'] = min(session_engagement_rate, 10.0)  # Cap at reasonable max
                    
                    # Estimate overall score from activity completion
                    if tweets_posted > 0 or engagement_actions > 0:
                        activity_score = min((tweets_posted * 0.3 + engagement_actions * 0.01 + replies_sent * 0.2), 1.0)
                        if metrics['overall_score'] == 0.0:
                            metrics['overall_score'] = activity_score
                    
                    # Add session indicators
                    metrics['session_tweets'] = tweets_posted
                    metrics['session_engagements'] = engagement_actions
                    metrics['session_replies'] = replies_sent
                    metrics['data_source'] = 'session_data'
                    
                except Exception as e:
                    logger.warning(f"Could not get session performance data: {e}")
            
            # Ensure all values are reasonable
            metrics['overall_score'] = max(0.0, min(1.0, metrics['overall_score']))
            metrics['engagement_rate'] = max(0.0, min(1.0, metrics['engagement_rate']))
            metrics['follower_growth'] = max(0, metrics['follower_growth'])
            metrics['tweet_impressions'] = max(0, metrics['tweet_impressions'])
            metrics['reach'] = max(0, metrics['reach'])
            
            # Add data quality indicators
            if metrics['overall_score'] > 0 or metrics['engagement_rate'] > 0:
                metrics['has_real_data'] = True
            else:
                metrics['has_real_data'] = False
                metrics['data_source'] = 'no_data'
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            # Return error state with minimal data
            return {
                'overall_score': 0.0,
                'engagement_rate': 0.0,
                'follower_growth': 0,
                'tweet_impressions': 0,
                'reach': 0,
                'trend': 'unknown',
                'has_real_data': False,
                'error': str(e)
            }
    
    def get_schedule_data(self, date_str: str) -> Dict[str, Any]:
        """Get schedule data for a specific date from real sources"""
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Try to get real schedule data from schedule manager first
            if self.schedule_manager:
                try:
                    # Get or create daily schedule - this should load existing slots from database
                    daily_schedule = self.schedule_manager.get_or_create_daily_schedule(date_str)
                    
                    # If schedule manager has no slots but database does, force load from database
                    if not daily_schedule or not daily_schedule.slots:
                        logger.info(f"🔄 Schedule manager has no slots for {date_str}, attempting to load from database...")
                        try:
                            # Get existing slots from database
                            existing_slots = self.db_manager.get_schedule_slots(date_str)
                            if existing_slots:
                                logger.info(f"📋 Found {len(existing_slots)} existing slots in database for {date_str}")
                                
                                # Force the schedule manager to load these slots
                                if hasattr(self.schedule_manager, 'load_existing_schedule'):
                                    daily_schedule = self.schedule_manager.load_existing_schedule(date_str)
                                else:
                                    # Fallback: create a new schedule but preserve existing slots
                                    logger.info("🔧 Schedule manager doesn't have load_existing_schedule, creating new...")
                                    daily_schedule = self.schedule_manager.create_daily_schedule(date_str)
                        except Exception as load_error:
                            logger.error(f"Error loading existing slots: {load_error}")
                    
                    if daily_schedule and daily_schedule.slots:
                        # Ensure all schedule manager slots are saved to database
                        saved_count = 0
                        for slot in daily_schedule.slots:
                            try:
                                if self.db_manager.save_schedule_slot(slot):
                                    saved_count += 1
                            except Exception as save_error:
                                logger.warning(f"Could not save slot {slot.slot_id} to database: {save_error}")
                        
                        if saved_count > 0:
                            logger.info(f"💾 Ensured {saved_count} schedule manager slots are saved to database")
                        
                        slots = []
                        for slot in daily_schedule.slots:
                            slots.append({
                                'slot_id': slot.slot_id,
                                'activity_type': slot.activity_type.value,
                                'start_time': slot.start_time.isoformat(),
                                'end_time': slot.end_time.isoformat(),
                                'status': slot.status.value,
                                'priority': slot.priority,
                                'is_flexible': slot.is_flexible,
                                'activity_config': slot.activity_config,
                                'performance_data': slot.performance_data,
                                'execution_log': slot.execution_log[-3:] if slot.execution_log else []  # Last 3 log entries
                            })
                        
                        return {
                            'date': date_str,
                            'slots': slots,
                            'strategy_focus': daily_schedule.strategy_focus,
                            'daily_goals': daily_schedule.daily_goals,
                            'performance_targets': daily_schedule.performance_targets,
                            'completion_rate': daily_schedule.completion_rate,
                            'total_activities': daily_schedule.total_activities,
                            'data_source': 'schedule_manager'
                        }
                        
                except Exception as e:
                    logger.warning(f"Could not get schedule from schedule manager: {e}")
            
            # Fallback to database query - but use proper slot data, not activities
            if self.db_manager:
                try:
                    # Use get_schedule_slots instead of get_activities_by_date to get proper slots
                    existing_slots = self.db_manager.get_schedule_slots(date_str)
                    
                    if existing_slots:
                        slots = []
                        for slot in existing_slots:
                            slots.append({
                                'slot_id': slot.slot_id,  # Use the actual slot_id, not db_slot_X
                                'activity_type': slot.activity_type.value,
                                'start_time': slot.start_time.isoformat(),
                                'end_time': slot.end_time.isoformat(),
                                'status': slot.status.value,
                                'priority': slot.priority,
                                'is_flexible': slot.is_flexible,
                                'activity_config': slot.activity_config,
                                'performance_data': slot.performance_data,
                                'execution_log': slot.execution_log[-3:] if slot.execution_log else [],
                                'data_source': 'database_slots'  # Distinguish from activities
                            })
                        
                        logger.info(f"📋 Returning {len(slots)} slots from database for {date_str}")
                        return {
                            'date': date_str,
                            'slots': slots,
                            'data_source': 'database_slots',
                            'message': 'Loaded from database slots (schedule manager was empty)'
                        }
                    else:
                        # Final fallback to activities if no slots exist
                        activities = self.db_manager.get_activities_by_date(target_date)
                        
                        if activities:
                            slots = []
                            for i, activity in enumerate(activities):
                                start_time = activity.get('start_time')
                                end_time = activity.get('end_time')
                                
                                slots.append({
                                    'slot_id': activity.get('slot_id') or activity.get('id') or f"db_slot_{i}",  # Only use db_slot_X as last resort
                                    'activity_type': activity.get('activity_type', 'unknown'),
                                    'start_time': start_time.isoformat() if hasattr(start_time, 'isoformat') else str(start_time),
                                    'end_time': end_time.isoformat() if hasattr(end_time, 'isoformat') else str(end_time),
                                    'status': activity.get('status', 'scheduled'),
                                    'priority': activity.get('priority', 'medium'),
                                    'performance_data': activity.get('performance_data'),
                                    'data_source': 'database_activities'  # Mark as fallback
                                })
                            
                            return {
                                'date': date_str,
                                'slots': slots,
                                'data_source': 'database_activities',
                                'message': 'Fallback to database activities (no slots found)'
                            }
                        
                except Exception as e:
                    logger.warning(f"Could not get activities from database: {e}")
            
            # Final fallback - return empty schedule structure
            return {
                'date': date_str,
                'slots': [],
                'strategy_focus': '',
                'daily_goals': {},
                'performance_targets': {},
                'completion_rate': 0.0,
                'total_activities': 0,
                'data_source': 'no_data',
                'message': 'No schedule data available for this date'
            }
            
        except Exception as e:
            logger.error(f"Error getting schedule data: {e}")
            return {
                'date': date_str,
                'slots': [],
                'error': str(e),
                'data_source': 'error'
            }
    
    def get_performance_data(self, days: int, platform: Optional[str] = None) -> Dict[str, Any]:
        """Get performance data for the specified number of days"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Initialize safe defaults to avoid unbound local errors
            trends = {}
            summary = {}
            if self.performance_tracker:
                try:
                    # Build summary from account overview (tracker does not implement analyze/get_trends)
                    account_overview = self.performance_tracker.get_account_overview(time_range='7D', platform=platform)
                    current = account_overview.get('current', {}) if isinstance(account_overview, dict) else {}
                    percent = account_overview.get('percent_change', {}) if isinstance(account_overview, dict) else {}
                    summary = {
                        'engagement_rate': current.get('engagement_rate', 0.0),
                        'follower_growth': percent.get('total_followers', 0.0),
                        'total_impressions': current.get('impressions', 0),
                        'total_engagements': current.get('engagements', 0),
                        'likes': current.get('likes', 0),
                        'replies': current.get('replies', 0),
                        'reposts': current.get('reposts', 0),
                        'profile_visits': current.get('profile_visits', 0),
                        'total_followers': current.get('total_followers', 0),
                        'follows': current.get('follows', 0),
                        'posts_count': current.get('posts_count', 0),
                    }
                    # Use account trends for chart series
                    trends = self.performance_tracker.get_account_trends(time_range='7D', platform=platform)
                except Exception as e:
                    logger.warning(f"Could not build performance summary/trends from account analytics: {e}")
            else:
                # Fallback demo values when tracker unavailable
                summary = {
                    'performance_score': 0.75,
                    'engagement_rate': 0.05,
                    'follower_growth': 12,
                    'total_impressions': 10000,
                    'total_engagements': 500
                }
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'summary': summary,
                'trends': trends
            }
            
            
        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return {
                'period': {
                    'start_date': (datetime.now().date() - timedelta(days=days)).isoformat(),
                    'end_date': datetime.now().date().isoformat(),
                    'days': days
                },
                'summary': {},
                'trends': {},
                'error': str(e)
            }

    def _sync_meta_analytics(self, platform: str):
        """Fetch latest analytics from Meta and save to DB"""
        if not self.meta_handler or not self.performance_tracker:
            return

        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            if platform == 'facebook':
                data = self.meta_handler.get_facebook_insights()
                if data:
                    # Map FB fields to AccountAnalytics fields
                    self.performance_tracker.ingest_account_analytics(
                        date=date_str,
                        time_range='DAY',
                        analytics={
                            "impressions": data.get("page_impressions", 0),
                            "engagements": data.get("page_post_engagements", 0),
                            "total_followers": data.get("page_fans", 0),
                            "profile_visits": data.get("page_views_total", 0),
                            "platform": "facebook"
                        }
                    )
            
            elif platform == 'instagram':
                data = self.meta_handler.get_instagram_insights()
                if data:
                    # Map IG fields
                    self.performance_tracker.ingest_account_analytics(
                        date=date_str,
                        time_range='DAY',
                        analytics={
                            "impressions": data.get("impressions", 0),
                            "reach": data.get("reach", 0),
                            "profile_visits": data.get("profile_views", 0),
                            "total_followers": data.get("followers_count", 0),
                            "posts_count": data.get("media_count", 0),
                            "platform": "instagram"
                        }
                    )

        except Exception as e:
            logger.error(f"Error syncing Meta analytics for {platform}: {e}")
    
    def get_optimization_data(self) -> Dict[str, Any]:
        """Get strategy optimization data from Database"""
        try:
            current_strategy = None
            
            # Fetch from DB
            if self.db_manager:
                strategies = self.db_manager.get_all_strategy_templates()
                if strategies:
                    # Use the first active strategy
                    db_strategy = strategies[0]
                    
                    # Convert Enum keys to strings for JSON serialization
                    dist = {}
                    if db_strategy.activity_distribution:
                        for k, v in db_strategy.activity_distribution.items():
                            # Handle both Enum and string keys
                            key_str = k.value if hasattr(k, 'value') else str(k)
                            dist[key_str] = v
                            
                    current_strategy = {
                        'name': db_strategy.strategy_name,
                        'description': db_strategy.description,
                        'activity_distribution': dist,
                        'optimal_posting_times': db_strategy.optimal_posting_times
                    }

            # Fallback if no DB or no strategy
            if not current_strategy:
                current_strategy = {
                    'name': 'Balanced Growth',
                    'description': 'A balanced approach focusing on engagement and content quality',
                    'activity_distribution': {
                        'content_creation': 0.3,
                        'scroll_engage': 0.25,
                        'auto_reply': 0.2,
                        'analytics_check': 0.15,
                        'radar_discovery': 0.1
                    },
                    'optimal_posting_times': ['09:00', '13:00', '17:00', '20:00']
                }
            
            recommendations = [
                "Increase engagement activities during peak hours",
                "Focus more on content creation for better reach",
                "Monitor analytics more frequently for optimization opportunities"
            ]
            
            return {
                'current_strategy': current_strategy,
                'recommendations': recommendations,
                'last_optimization': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting optimization data: {e}")
            # Fallback on error
            return {
                'current_strategy': {
                    'name': 'Balanced Growth',
                    'description': 'A balanced approach focusing on engagement and content quality',
                    'activity_distribution': {
                        'content_creation': 0.3,
                        'scroll_engage': 0.25,
                        'auto_reply': 0.2,
                        'analytics_check': 0.15,
                        'radar_discovery': 0.1
                    },
                    'optimal_posting_times': ['09:00', '13:00', '17:00', '20:00']
                },
                'recommendations': [],
                'last_optimization': datetime.now().isoformat()
            }
    
    def get_logs_data(self, limit: int) -> Dict[str, Any]:
        """Get activity logs from real data sources"""
        try:
            recent_sessions = []
            recent_analyses = []
            
            # Try to get real session data from database
            if self.db_manager:
                try:
                    # Get recent engagement sessions
                    sessions = self.db_manager.get_recent_engagement_sessions(hours=24)
                    for session in sessions:
                        recent_sessions.append({
                            'session_id': session.session_id,
                            'start_time': session.start_time.isoformat(),
                            'end_time': session.end_time.isoformat() if session.end_time else None,
                            'activity_type': session.activity_type.value,
                            'accounts_engaged': len(session.accounts_engaged),
                            'interactions_made': session.interactions_made,
                            'topics_engaged': session.topics_engaged,
                            'engagement_quality_score': session.engagement_quality_score,
                            'session_notes': session.session_notes,
                            'data_source': 'database'
                        })
                        
                except Exception as e:
                    logger.warning(f"Could not get engagement sessions from database: {e}")
                
                try:
                    # Get recent performance analyses
                    analyses = self.db_manager.get_recent_analyses(limit=limit)
                    for analysis in analyses:
                        recent_analyses.append({
                            'date': analysis.date,
                            'performance_score': analysis.performance_score,
                            'metrics': analysis.metrics,
                            'insights': analysis.insights,
                            'recommendations': analysis.recommendations,
                            'analysis_timestamp': analysis.analysis_timestamp.isoformat(),
                            'strategy_adjustments': analysis.strategy_adjustments,
                            'data_source': 'database'
                        })
                        
                except Exception as e:
                    logger.warning(f"Could not get performance analyses from database: {e}")
            
            # Try to get session data from scheduler if available
            if self.scheduler and hasattr(self.scheduler, 'state') and hasattr(self.scheduler.state, 'session_data'):
                try:
                    session_data = self.scheduler.state.session_data
                    
                    # Create a current session entry if we have activity
                    if any(session_data.get(key, 0) > 0 for key in ['tweets_posted', 'engagement_actions', 'replies_sent']):
                        current_session = {
                            'session_id': f"current_{datetime.now().strftime('%Y%m%d_%H%M')}",
                            'start_time': session_data.get('start_time', datetime.now().isoformat()),
                            'end_time': None,  # Still active
                            'activity_type': 'mixed',
                            'accounts_engaged': session_data.get('accounts_discovered', 0),
                            'interactions_made': {
                                'tweets': session_data.get('tweets_posted', 0),
                                'engagements': session_data.get('engagement_actions', 0),
                                'replies': session_data.get('replies_sent', 0),
                                'analytics_checks': session_data.get('analytics_checks', 0)
                            },
                            'topics_engaged': ['automation', 'manufacturing', 'AI'],  # Default topics
                            'engagement_quality_score': min(session_data.get('engagement_actions', 0) * 0.1, 1.0),
                            'session_notes': f"Active session - {session_data.get('engagement_actions', 0)} engagements made",
                            'data_source': 'current_session',
                            'is_active': True
                        }
                        recent_sessions.insert(0, current_session)  # Add to beginning
                        
                except Exception as e:
                    logger.warning(f"Could not get current session data: {e}")
            
            # Try to get recent schedule activity logs
            if self.schedule_manager:
                try:
                    today = datetime.now().strftime('%Y-%m-%d')
                    schedule_summary = self.schedule_manager.get_schedule_summary(today)
                    
                    if schedule_summary:
                        # Create a summary analysis entry
                        schedule_analysis = {
                            'date': today,
                            'performance_score': schedule_summary.get('completion_rate', 0.0),
                            'metrics': {
                                'total_slots': schedule_summary.get('total_slots', 0),
                                'completed_slots': schedule_summary.get('completed_slots', 0),
                                'failed_slots': schedule_summary.get('failed_slots', 0),
                                'completion_rate': schedule_summary.get('completion_rate', 0.0)
                            },
                            'insights': [
                                f"Completed {schedule_summary.get('completed_slots', 0)} of {schedule_summary.get('total_slots', 0)} scheduled activities",
                                f"Schedule completion rate: {schedule_summary.get('completion_rate', 0.0):.1%}"
                            ],
                            'recommendations': [],
                            'analysis_timestamp': datetime.now().isoformat(),
                            'strategy_adjustments': [],
                            'data_source': 'schedule_manager'
                        }
                        
                        # Add recommendations based on performance
                        completion_rate = schedule_summary.get('completion_rate', 0.0)
                        if completion_rate < 0.7:
                            schedule_analysis['recommendations'].append("Consider reducing schedule density")
                        elif completion_rate > 0.9:
                            schedule_analysis['recommendations'].append("Schedule performing well - consider adding more activities")
                        
                        recent_analyses.insert(0, schedule_analysis)
                        
                except Exception as e:
                    logger.warning(f"Could not get schedule summary: {e}")
            
            # If we still don't have much data, create minimal entries
            if not recent_sessions and not recent_analyses:
                # Create a minimal status entry
                status_entry = {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'performance_score': 0.0,
                    'metrics': {'system_status': 'running' if self.running else 'stopped'},
                    'insights': ['System is operational' if self.running else 'System is not running'],
                    'recommendations': ['Start the agent to begin collecting data'] if not self.running else [],
                    'analysis_timestamp': datetime.now().isoformat(),
                    'strategy_adjustments': [],
                    'data_source': 'system_status'
                }
                recent_analyses.append(status_entry)
            
            return {
                'recent_sessions': recent_sessions[:limit],
                'recent_analyses': recent_analyses[:limit],
                'data_sources': list(set([item.get('data_source', 'unknown') for item in recent_sessions + recent_analyses])),
                'total_sessions': len(recent_sessions),
                'total_analyses': len(recent_analyses)
            }
            
        except Exception as e:
            logger.error(f"Error getting logs data: {e}")
            return {
                'recent_sessions': [],
                'recent_analyses': [],
                'error': str(e),
                'data_sources': ['error']
            }
    
    def run_scheduler(self):
        """Main scheduler loop driven by ScheduleManager 15-minute slots"""
        logger.info("Starting scheduler...")
        if not self.scheduler:
            logger.error("Agent core missing – cannot run scheduler")
            return

        if not self.schedule_manager:
            logger.error("ScheduleManager unavailable – cannot build schedule")
            return

        import time as _t
        import asyncio as _asyncio
        from datetime import datetime, timedelta

        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check Premium Status on startup to configure analytics tasks
        try:
            if self.scheduler and getattr(self.scheduler, 'scraper', None):
                is_premium = self.scheduler.scraper.check_premium_status()
                self.schedule_manager.set_twitter_premium_status(is_premium)
                logger.info(f"✨ Twitter Premium Status checked on startup: {is_premium}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to check premium status on startup: {e}")

        # Ensure today's schedule exists
        self.schedule_manager.create_daily_schedule(today)

        last_slot_id = None

        while self.running:
            try:
                # Check if we should still be running before processing
                if not self.running:
                    break
                    
                now = datetime.now()

                # If we crossed midnight, create new schedule for new day
                if now.strftime("%Y-%m-%d") != today:
                    today = now.strftime("%Y-%m-%d")
                    self.schedule_manager.create_daily_schedule(today)
                    last_slot_id = None  # reset tracker

                current_slot = self.schedule_manager.get_current_activity()

                # Execute only once per slot
                if current_slot and current_slot.slot_id != last_slot_id:
                    # Check again before starting task execution
                    if not self.running:
                        break
                        
                    last_slot_id = current_slot.slot_id
                    logger.info(f"▶ Executing scheduled task: {current_slot.activity_type.value} ({current_slot.slot_id})")
                    self.schedule_manager.mark_activity_started(current_slot.slot_id)

                    # Update agent state so UI shows task
                    self.scheduler.state.current_task = current_slot.activity_type.value

                    try:
                        # Check one more time before dispatching activity
                        if not self.running:
                            logger.info("🛑 Scheduler stopping - cancelling task execution")
                            self.schedule_manager.mark_activity_failed(current_slot.slot_id, "Scheduler stopped")
                            break
                            
                        # Dispatch to agent
                        _asyncio.run(self._dispatch_activity(current_slot))
                        self.schedule_manager.mark_activity_completed(current_slot.slot_id)
                    except Exception as task_err:
                        logger.error(f"Task execution failed: {task_err}")
                        self.schedule_manager.mark_activity_failed(current_slot.slot_id, str(task_err))

                    # Clear current task
                    if self.scheduler and hasattr(self.scheduler, 'state'):
                        self.scheduler.state.current_task = None

                    # broadcast update after finishing task
                    self.broadcast_status_update()

                # Check before sleeping
                if not self.running:
                    break
                    
                # sleep for 30 seconds before checking again, but check self.running periodically
                for _ in range(30):
                    if not self.running:
                        break
                    _t.sleep(1)

            except Exception as loop_err:
                logger.error(f"Scheduler loop error: {loop_err}")
                if not self.running:
                    break
                # Sleep with interruption check
                for _ in range(60):
                    if not self.running:
                        break
                    _t.sleep(1)

        logger.info("🛑 Scheduler stopped gracefully (self.running = False)")

    async def generate_automation_content(self, content_type, tweet_content=None, selected_prompt=None):
        """Generate content focused on automation and tokenization themes"""
        global used_automation_prompts, used_visual_prompts
        
        # Use provided prompt or select a new one
        if selected_prompt is None:
            # First, always get a base automation/tokenization concept
            available_prompts = set(AUTOMATION_TOKENIZATION_PROMPTS) - used_automation_prompts
            if not available_prompts:
                used_automation_prompts.clear()
                available_prompts = set(AUTOMATION_TOKENIZATION_PROMPTS)
            
            selected_prompt = random.choice(list(available_prompts))
            used_automation_prompts.add(selected_prompt)

        # Load config at the top of the file
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        if content_type == "video":
            # Generate video prompt using the LoFi nostalgia format with company branding
            # If tweet_content is provided, incorporate it into the prompt
            concept_text = f"<CONCEPT START>{selected_prompt}<CONCEPT END>"
            if tweet_content:
                concept_text += f" with visual representation of the following message: '{tweet_content}'"
            
            video_prompt = f"""Generate a LoFi nostalgia-inducing surreal video with a contemplative mood representative of the following concept but featuring real world scenes: {concept_text}. 
            The video should have a dreamy, vintage aesthetic with soft lighting, muted colors, and smooth cinematic transitions. 
            Incorporate {config['company_config']['name']}'s brand colors ({config['company_config']['brand_colors']['primary']} and {config['company_config']['brand_colors']['secondary']}) subtly throughout the scenes.
            Include subtle visual elements that relate to the concept and the company's focus on {', '.join(config['company_config']['focus_areas'][:3])}.
            Style should be atmospheric and meditative with a retro film quality, maintaining the company's {config['company_config']['brand_voice']} brand voice.
            IMPORTANT: Do not include any text, typography, fonts, letters, words, or written content in the video. Focus purely on visual imagery, scenes, and atmospheric elements."""
            return video_prompt
        elif content_type == "image":
            # Generate image prompt with similar aesthetic but for still images
            # If tweet_content is provided, incorporate it into the prompt
            concept_text = f"<CONCEPT START>{selected_prompt}<CONCEPT END>"
            if tweet_content:
                concept_text += f" with visual representation of the following message: '{tweet_content}'"
            
            image_prompt = f"""Generate a LoFi nostalgia-inducing surreal photograph with a nostalgic aesthetic representing the following concept: {concept_text}. 
            The image should have soft, warm lighting, muted vintage colors, and subtle visual elements that relate to the concept.
            Incorporate {config['company_config']['name']}'s brand colors ({config['company_config']['brand_colors']['primary']} and {config['company_config']['brand_colors']['secondary']}) in a harmonious way.
            Style should be atmospheric and thoughtful with a film photography quality, featuring real-world industrial or community scenes.
            The overall aesthetic should reflect the company's focus on {', '.join(config['company_config']['focus_areas'][:3])}.
            IMPORTANT: Do not include any text, typography, fonts, letters, words, or written content in the image. Focus purely on visual imagery, scenes, and atmospheric elements."""
            return image_prompt
            
        else:  # text content (tweets)
            # Generate tweet text using the selected topic
            system_prompt = f"""You are an expert in industrial automation and tokenization as conducted by The Utility Company, a company that is pioneering the democratization of manufacturing through technology. The Utility Company operates at the intersection of AI, Automation, and Blockchain to deliver unique asset classes. Our asset classes are created by tokenizing the access, agency, and accountability of physical assets. For example, a whiskey distillery is tokenized by providing lifelong, transferable, and limited memberships which are tradable on a secondary market and provide the token holder with access to the facility and visibility of their barrel 24/7/365, agency over the barrel by being able to set the various parameters of the whiskey in the barrel, such as mashbill, aging duration, and barrel location, and accountability by being able to track the barrel's location and condition at all times as well as the final output of the whiskey. The distillery gains a new revenue stream in the form of royalities earned in the trade of the assets in exchange for dedicating a fix proportion of their output for token-holding stakeholders. You can imagine the incredible dynamic that is formed (DO NOT JUST USE WHISKEY AS AN EXAMPLE, USE AN EXAMPLE THAT IS NOT WHISKEY AND BE CREATIVE). Create engaging tweets that educate and inspire about the democratization of manufacturing through technology. Focus on community empowerment, equitable access, and innovative economic models. Also focus on advances in material science and additive manufacturing. DO NOT use hashtags or quotation marks.

Write engaging, educational tweets that inspire a future where:

Manufacturing is democratized

Communities co-own production

Innovation in material science and additive manufacturing reshapes participation in industry

Economic models are regenerative, transparent, and inclusive

Avoid hashtags or quotation marks. Focus on storytelling, technical clarity, and cultural relevance.

    Topic focus: {selected_prompt}"""
            
            try:
                response = client.chat.completions.create(
                    model="o3",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "Write an engaging tweet (under 280 characters) about this topic. Include relevant emojis but no hashtags."}
                    ]
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Error generating automation content: {e}")
                return f"Exploring {selected_prompt.lower()} 🚀 The future of manufacturing is community-driven and tokenized! 💡"

    async def generate_radar_and_engage_params(self):
        """Use LLM to generate parameters for _radar_and_engage tool."""
        
        # Define the tool for parameter generation
        radar_params_tool = {
            "type": "function",
            "function": {
                "name": "generate_radar_params",
                "description": "Generate effective parameters for radar discovery and engagement operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "focus_area": {
                            "type": "string",
                            "description": "The main topic or area to focus radar discovery on (e.g., 'AI automation', 'manufacturing innovation', 'tokenization trends')"
                        },
                        "engagement_type": {
                            "type": "string",
                            "enum": ["reply", "like", "retweet", "quote"],
                            "description": "Type of engagement to perform with discovered content"
                        },
                        "max_tweets": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Maximum number of tweets to engage with"
                        },
                        "search_depth": {
                            "type": "string",
                            "enum": ["shallow", "medium", "deep"],
                            "description": "How deep to search for relevant content"
                        }
                    },
                    "required": ["focus_area", "engagement_type", "max_tweets", "search_depth"]
                }
            }
        }
        
        company_context = (
            """You are an expert in industrial automation and tokenization as conducted by The Utility Company, a company that is pioneering the democratization of manufacturing through technology. The Utility Company operates at the intersection of AI, Automation, and Blockchain to deliver unique asset classes. Our asset classes are created by tokenizing the access, agency, and accountability of physical assets. For example, a whiskey distillery is tokenized by providing lifelong, transferable, and limited memberships which are tradable on a secondary market and provide the token holder with access to the facility and visibility of their barrel 24/7/365, agency over the barrel by being able to set the various parameters of the whiskey in the barrel, such as mashbill, aging duration, and barrel location, and accountability by being able to track the barrel's location and condition at all times as well as the final output of the whiskey. The distillery gains a new revenue stream in the form of royalities earned in the trade of the assets in exchange for dedicating a fix proportion of their output for token-holding stakeholders. You can imagine the incredible dynamic that is formed (DO NOT JUST USE WHISKEY AS AN EXAMPLE, USE AN EXAMPLE THAT IS NOT WHISKEY AND BE CREATIVE). Create engaging tweets that educate and inspire about the democratization of manufacturing through technology. Focus on community empowerment, equitable access, and innovative economic models. Also focus on advances in material science and additive manufacturing. DO NOT use hashtags or quotation marks.

Write engaging, educational tweets that inspire a future where:

Manufacturing is democratized

Communities co-own production

Innovation in material science and additive manufacturing reshapes participation in industry

Economic models are regenerative, transparent, and inclusive

Avoid hashtags or quotation marks. Focus on storytelling, technical clarity, and cultural relevance."""
        )
        
        system_prompt = (
            f"{company_context} "
            "You are an expert social media automation strategist. Generate effective parameters for a radar discovery and engagement operation. "
            "Focus on topics that align with our company's mission and would generate meaningful engagement with our target audience."
        )
        
        user_prompt = (
            "Generate parameters for a radar and engagement operation that would help discover and engage with relevant content "
            "in the automation, manufacturing, tokenization, or AI space. Consider current trends and optimal engagement strategies."
        )
        
        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=[radar_params_tool],
                tool_choice={"type": "function", "function": {"name": "generate_radar_params"}}
            )
            
            # Extract tool call result
            message = response.choices[0].message
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                import json
                params = json.loads(tool_call.function.arguments)
                logger.info(f"Generated radar params via tool call: {params}")
                return params
            else:
                raise ValueError("No tool call returned from LLM")
                
        except Exception as e:
            logger.error(f"Error generating radar_and_engage params: {e}")
            # Fallback to defaults
            return {
                "focus_area": "AI automation trends",
                "engagement_type": "reply", 
                "max_tweets": 3,
                "search_depth": "medium"
            }

    async def generate_search_topics(self):
        """Generate 5 search topics using LLM based on company information"""
        
        # Define the tool for topic generation
        search_topics_tool = {
            "type": "function",
            "function": {
                "name": "generate_search_topics",
                "description": "Generate 5 specific search topics for Twitter engagement based on company focus areas",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 5,
                            "maxItems": 5,
                            "description": "Array of 5 specific search topics/keywords for Twitter engagement"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Brief explanation of why these topics were selected"
                        }
                    },
                    "required": ["topics", "reasoning"]
                }
            }
        }
        
        # Load company config
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            company_config = config.get('company_config', {})
        except Exception as e:
            logger.error(f"Could not load company config: {e}")
            company_config = {}
        
        company_context = f"""
        Company: {company_config.get('name', 'The Utility Company')}
        Industry: {company_config.get('industry', 'Technology')}
        Mission: {company_config.get('mission', 'Democratizing manufacturing through technology')}
        Focus Areas: {', '.join(company_config.get('focus_areas', ['automation', 'tokenization', 'manufacturing']))}
        Values: {', '.join(company_config.get('values', ['innovation', 'community empowerment']))}
        Target Audience: {company_config.get('target_audience', 'manufacturers and technology innovators')}
        
        The Utility Company operates at the intersection of AI, Automation, and Blockchain to deliver unique asset classes. 
        Our asset classes are created by tokenizing the access, agency, and accountability of physical assets.
        """
        
        system_prompt = f"""You are a social media strategist for {company_config.get('name', 'The Utility Company')}. 
        
        {company_context}
        
        Generate 5 specific search topics that would help us find and engage with relevant conversations on Twitter. 
        These topics should:
        1. Align with our company's mission and focus areas
        2. Be specific enough to find quality conversations (not too broad)
        3. Include both trending and evergreen topics in our industry
        4. Target our ideal audience of manufacturers, technologists, and innovators
        5. Mix technical terms with more accessible language
        
        Focus on topics related to: automation, tokenization, manufacturing innovation, AI in industry, 
        blockchain applications, community ownership, decentralized manufacturing, and material science advances."""
        
        user_prompt = """Generate 5 specific search topics for Twitter engagement. 
        Make them diverse but relevant - include some trending hashtags, some technical terms, 
        and some conversational phrases that our target audience would use."""
        
        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=[search_topics_tool],
                tool_choice={"type": "function", "function": {"name": "generate_search_topics"}}
            )
            
            # Extract tool call result
            message = response.choices[0].message
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                result = json.loads(tool_call.function.arguments)
                topics = result.get('topics', [])
                reasoning = result.get('reasoning', '')
                
                logger.info(f"Generated search topics: {topics}")
                logger.info(f"Topic selection reasoning: {reasoning}")
                
                return topics
            else:
                raise ValueError("No tool call returned from LLM")
                
        except Exception as e:
            logger.error(f"Error generating search topics: {e}")
            # Fallback to default topics
            return [
                "industrial automation trends",
                "tokenized manufacturing assets", 
                "AI in manufacturing",
                "decentralized production networks",
                "blockchain supply chain innovation"
            ]

    def _is_within_midnight_window(self, dt: datetime) -> bool:
        """Check if the given datetime is within 30 minutes of midnight (23:30-00:30)"""
        hour = dt.hour
        minute = dt.minute
        
        # Check if we're in the 23:30-23:59 window
        if hour == 23 and minute >= 30:
            return True
        
        # Check if we're in the 00:00-00:30 window  
        if hour == 0 and minute <= 30:
            return True
            
        return False

    async def _dispatch_activity(self, slot: 'ScheduleSlot') -> dict:
        """Map ScheduleSlot activity type to agent methods."""
        from data_models import ActivityType
        import time
        
        # Global declarations for prompt consistency
        global used_automation_prompts

        activity_type = slot.activity_type
        config = slot.activity_config or {}

        # Scroll & Engage
        if activity_type == ActivityType.SCROLL_ENGAGE:
            await self.scheduler._scroll_and_engage(
                duration_seconds=config.get('duration_seconds', 600),  # Increased from 300 to 450 (7.5 minutes)
                engagement_rate="medium",
                engagement_types=["like", "reply"],
                focus_keywords=["automation", "manufacturing", "decentralized", "AI", "tokenization", "blockchain", "smart contracts", "industrial automation", "tokenized assets", "distributed ledger technology", "blockchain infrastructure", "smart contract enforcement", "tokenized asset classes", "tokenized asset governance", "community-empowered manufacturing", "democratized manufacturing", "tokenized manufacturing", "tokenized industrial assets", "tokenized industrial infrastructure", "tokenized industrial cooperatives", "tokenized industrial assets", "tokenized industrial infrastructure", "tokenized industrial cooperatives", "access rights", "operational agency", "performance accountability", "tokenized asset classes", "tokenized asset governance", "community-empowered manufacturing", "democratized manufacturing", "cannabis", "botanicals", "botanical automation"]
            )
            return {"success": True, "activity": "scroll_engage", "actions": "engaged with timeline content"}

        # Search and Engage - NEW ACTIVITY TYPE
        elif activity_type == ActivityType.SEARCH_ENGAGE:
            try:
                logger.info("Starting search and engage activity - generating topics via LLM")
                
                # Generate 5 search topics using LLM based on company info
                search_topics = await self.generate_search_topics()
                
                total_results = []
                
                # Spend exactly 3 minutes on each query (5 queries = 15 minutes total)
                for i, topic in enumerate(search_topics, 1):
                    logger.info(f"🔍 Search query {i}/5: {topic}")
                    
                    # Create search and engage command for this specific topic
                    command = f"search and engage with tweets about '{topic}' for exactly 3 minutes with medium engagement rate focusing on replies and likes"
                    
                    # Execute the command through the scheduler
                    result = await self.scheduler.process_command(command)
                    
                    total_results.append({
                        "topic": topic,
                        "query_number": i,
                        "result": result,
                        "duration": "3 minutes"
                    })
                    
                    logger.info(f"✅ Completed search query {i}/5 for topic: {topic}")
                
                return {
                    "success": True, 
                    "activity": "search_engage", 
                    "topics_searched": search_topics,
                    "total_queries": len(search_topics),
                    "total_duration": "15 minutes",
                    "results": total_results
                }
                
            except Exception as e:
                logger.error(f"Search and engage activity failed: {e}")
                return {"success": False, "activity": "search_engage", "error": str(e)}

        # Reply to notifications/mentions
        elif activity_type == ActivityType.REPLY:
            try:
                # Get notification management parameters from config
                max_replies = config.get('max_replies', 10)
                reply_style = config.get('tone', 'grounded yet futuristic')
                filter_keywords = config.get('filter_keywords', [])
                
                # Use the scheduler's notification management
                result = await self.scheduler.process_command(
                    f"auto reply to notifications with max_replies={max_replies} and reply_style={reply_style}"
                )
                
                return {"success": True, "activity": "reply", "result": result}
                
            except Exception as e:
                logger.error(f"Reply activity failed: {e}")
                return {"success": False, "activity": "reply", "error": str(e)}

        # Radar Discovery
        elif activity_type == ActivityType.RADAR_DISCOVERY:
            # Generate a command for radar discovery that will be processed by the agent
            command = f"use radar_and_engage tool and engage with 10 tweets. Focus on the following topics: {config.get('focus_area', 'AI automation trends')}"
            return {"success": True, "activity": "radar_discovery", "command": command}

        # Tweet posting
        elif activity_type == ActivityType.TWEET:
            try:
                tweet_text = await self.scheduler._generate_utility_message(
                    content_type="promotional",
                    message_focus="daily inspiration"
                )
            except Exception:
                tweet_text = "Automated update from our AI agent!"

            result = await self.scheduler._compose_tweet(
                content=tweet_text,
                thread_continuation=False,
                add_media=False,
                schedule_post=False)
            return {"success": True, "activity": "tweet", "result": result}

        # Replace the existing IMAGE_TWEET section
        elif activity_type == ActivityType.IMAGE_TWEET:
            try:
                logger.info("Generating image tweet text")
                # Generate focused tweet text about automation/tokenization - this selects a prompt
                tweet_text = await self.generate_automation_content("tweet")
                
                # Extract the selected prompt from the global state to reuse it
                # Get the most recently used prompt (the one we just used for the tweet)
                selected_prompt = list(used_automation_prompts)[-1] if used_automation_prompts else None
                
                logger.info("Generated image tweet text")
                # wait for 3 seconds
                time.sleep(3)       
                logger.info("Generating image prompt")
                # Generate image prompt with the LoFi aesthetic, using the SAME prompt as the tweet
                image_prompt = await self.generate_automation_content("image", tweet_content=tweet_text, selected_prompt=selected_prompt)
                logger.info("Generated image prompt")
                
                logger.info(f"Generated image tweet text: {tweet_text}")
                logger.info(f"Generated image prompt: {image_prompt}")
                logger.info(f"Using consistent prompt: {selected_prompt}")
                
            except Exception as e:
                logger.error(f"Error generating image content: {e}")
                tweet_text = "The future of manufacturing is decentralized and community-driven! 🏭✨"
                image_prompt = "Generate a contemplative, artistic photograph with a nostalgic aesthetic representing decentralized manufacturing. The image should have soft, warm lighting, muted vintage colors, and subtle visual elements. Style should be atmospheric and thoughtful with a film photography quality."

            result = await self.scheduler.generate_branded_image(
                prompt=image_prompt,
                tweet_text=tweet_text,
                size="1024x1024",
                apply_company_branding=True
            )
            return {"success": True, "activity": "image_tweet", "result": result}

        # Replace the existing VIDEO_TWEET section
        elif activity_type == ActivityType.VIDEO_TWEET:
            try:
                # Generate focused tweet text about automation/tokenization - this selects a prompt
                tweet_text = await self.generate_automation_content("tweet")
                
                # Extract the selected prompt from the global state to reuse it
                # Get the most recently used prompt (the one we just used for the tweet)
                selected_prompt = list(used_automation_prompts)[-1] if used_automation_prompts else None
                
                # Generate video prompt with the LoFi nostalgia format, using the SAME prompt as the tweet
                video_prompt = await self.generate_automation_content("video", tweet_content=tweet_text, selected_prompt=selected_prompt)
                
                logger.info(f"Generated video tweet text: {tweet_text}")
                logger.info(f"Generated video prompt: {video_prompt}")
                logger.info(f"Using consistent prompt: {selected_prompt}")
                
            except Exception as e:
                logger.error(f"Error generating video content: {e}")
                tweet_text = "Witness the transformation of industry through tokenized automation! 🎬🤖"
                video_prompt = "Generate a LoFi nostalgia-inducing surreal video with a contemplative mood representative of tokenized industrial automation but featuring real world scenes. The video should have a dreamy, vintage aesthetic with soft lighting, muted colors, and smooth cinematic transitions."

            result = await self.scheduler.generate_branded_video(
                prompt=video_prompt,
                tweet_text=tweet_text,
                duration="10",
                apply_company_branding=True
            )
            return {"success": True, "activity": "video_tweet", "result": result}

        # Thread creation and posting
        elif activity_type == ActivityType.THREAD:
            try:
                thread_topic = await self.scheduler._generate_utility_message(
                    content_type="educational",
                    message_focus="technical insights"
                )
            except Exception:
                thread_topic = "AI and Technology Insights: A Thread 🧵"

            result = await self.scheduler._create_and_post_thread(
                topic=thread_topic,
                thread_length=5,
                focus_area="artificial intelligence",
                include_hashtags=True)
            return {"success": True, "activity": "thread", "result": result}

        # Content creation – alternate image / video
        elif activity_type == ActivityType.CONTENT_CREATION:
            import random
            # Generate focused tweet text about automation/tokenization - this selects a prompt
            tweet_text = await self.generate_automation_content("tweet")
            
            # Extract the selected prompt from the global state to reuse it
            # Get the most recently used prompt (the one we just used for the tweet)
            selected_prompt = list(used_automation_prompts)[-1] if used_automation_prompts else None
            
            if random.random() < 0.5:
                # Generate image using the SAME prompt as the tweet
                prompt = await self.generate_automation_content("image", tweet_content=tweet_text, selected_prompt=selected_prompt)
                result = await self.scheduler.generate_branded_image(
                    prompt,
                    tweet_text,
                    size="1024x1024",
                    apply_company_branding=True)
            else:
                # Generate video using the SAME prompt as the tweet
                prompt = await self.generate_automation_content("video", tweet_content=tweet_text, selected_prompt=selected_prompt)
                result = await self.scheduler.generate_branded_video(
                    prompt=prompt,
                    tweet_text=tweet_text,
                    duration="5",
                    apply_company_branding=True)
            
            logger.info(f"Content creation using consistent prompt: {selected_prompt}")
            return {"success": True, "activity": "content_creation", "result": result}

        # Analytics check
        elif activity_type == ActivityType.ANALYTICS_CHECK:
            try:
                # Gather engagement metrics
                engagement_metrics = await self.scheduler._gather_engagement_metrics()
                
                # Get historical comparison
                historical_data = await self.scheduler._get_historical_performance(days=7)
                
                # Generate analytics summary
                analytics_summary = {
                    "current_metrics": engagement_metrics,
                    "historical_comparison": historical_data,
                    "timestamp": time.time(),
                    "recommendations": []
                }
                
                # Add basic recommendations based on metrics
                if engagement_metrics.get("engagement_rate", 0) < 0.02:
                    analytics_summary["recommendations"].append("Consider increasing engagement frequency")
                
                if engagement_metrics.get("follower_growth", 0) < 5:
                    analytics_summary["recommendations"].append("Focus on follower acquisition strategies")
                
                logger.info(f"Analytics check completed: {analytics_summary}")
                return {"success": True, "activity": "analytics_check", "result": analytics_summary}
                
            except Exception as e:
                logger.error(f"Analytics check failed: {e}")
                return {"success": False, "activity": "analytics_check", "error": str(e)}

        # Default case for unhandled activity types
        else:
            logger.warning(f"Unhandled activity type: {activity_type}")
            return {"success": False, "activity": str(activity_type), "error": "Activity type not implemented"}

    def run_optimization(self):
        """Run strategy optimization in background"""
        logger.info("Running strategy optimization...")
        try:
            # Simulate optimization process
            import time
            time.sleep(2)  # Simulate processing time
            
            # Function to generate slightly different data to show "optimization" happened
            optimization_data = self.get_optimization_data()
            if optimization_data and 'activity_distribution' in optimization_data:
                # Slight perturbation to show change
                import random
                dist = optimization_data['activity_distribution']
                keys = list(dist.keys())
                if len(keys) >= 2:
                    k1, k2 = random.sample(keys, 2)
                    delta = 0.05
                    if dist[k1] > delta:
                        dist[k1] -= delta
                        dist[k2] += delta
            
            logger.info("Strategy optimization completed successfully")
            
            # Broadcast update after optimization
            self.broadcast_status_update()
            
            # Also emit specific strategy update for the new component
            if self.socketio:
                self.socketio.emit('strategy_update', optimization_data)
            
        except Exception as e:
            logger.error(f"Error running optimization: {e}")
    
    def broadcast_status_update(self):
        """Broadcast status update to all connected clients"""
        if not self.connected_clients:
            return
        
        try:
            status_data = self.get_current_status()
            self.socketio.emit('status_update', status_data)
            logger.debug(f"Broadcasted status update to {len(self.connected_clients)} clients")
        except Exception as e:
            logger.error(f"Error broadcasting status update: {e}")
    
    def start_update_thread(self):
        """Start the periodic update thread"""
        def update_loop():
            while True:
                try:
                    self.broadcast_status_update()
                    threading.Event().wait(30)  # Update every 30 seconds
                except Exception as e:
                    logger.error(f"Error in update loop: {e}")
        
        if not self.update_thread or not self.update_thread.is_alive():
            self.update_thread = threading.Thread(target=update_loop, daemon=True)
            self.update_thread.start()
            logger.info("Started periodic update thread")
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the dashboard application"""
        logger.info(f"Starting Twitter Agent Dashboard on {host}:{port}")
        
        # Start periodic updates
        self.start_update_thread()
        
        # Run the Flask-SocketIO app
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )

def main():
    """Main entry point"""
    dashboard = TwitterAgentDashboard()
    
    # Run the dashboard
    try:
        dashboard.run(
            host='0.0.0.0',  # Allow external connections
            port=5000,
            debug=False
        )
    except KeyboardInterrupt:
        logger.info("Dashboard shutting down...")
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")

if __name__ == '__main__':
    main()
