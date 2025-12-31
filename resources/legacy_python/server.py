from flask import Flask, request, jsonify, render_template_string
import asyncio
import threading
import json
from datetime import datetime
import logging
from intelligent_agent import IntelligentTwitterAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global agent instance
agent = None
agent_lock = threading.Lock()

def initialize_agent():
    """Initialize the Twitter agent"""
    global agent
    with agent_lock:
        if agent is None:
            logger.info("Initializing Twitter Agent...")
            agent = IntelligentTwitterAgent(headless=False, use_persistent_profile=True)
            logger.info("Twitter Agent initialized successfully!")
        return agent

def run_async_command(command):
    """Run async command in thread-safe way"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(agent.process_command(command))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return f"❌ Error: {str(e)}"

# Web Interface Template
WEB_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Twitter Agent Server</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            padding: 30px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
            color: #333;
        }
        .header h1 { 
            margin: 0; 
            color: #1da1f2; 
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .header p { 
            color: #666; 
            font-size: 1.1em; 
            margin-top: 10px;
        }
        .status { 
            padding: 15px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
            font-weight: bold;
        }
        .status.ready { 
            background: #d4edda; 
            color: #155724; 
            border: 1px solid #c3e6cb;
        }
        .status.error { 
            background: #f8d7da; 
            color: #721c24; 
            border: 1px solid #f5c6cb;
        }
        .command-form { 
            margin-bottom: 30px; 
        }
        .form-group { 
            margin-bottom: 15px; 
        }
        label { 
            display: block; 
            margin-bottom: 5px; 
            font-weight: bold; 
            color: #333;
        }
        input, textarea, select { 
            width: 100%; 
            padding: 12px; 
            border: 2px solid #ddd; 
            border-radius: 8px; 
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input:focus, textarea:focus, select:focus { 
            outline: none; 
            border-color: #1da1f2; 
        }
        textarea { 
            height: 100px; 
            resize: vertical; 
        }
        button { 
            background: linear-gradient(45deg, #1da1f2, #0d8bd9); 
            color: white; 
            padding: 12px 30px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: bold;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 5px 15px rgba(29, 161, 242, 0.4);
        }
        button:disabled { 
            background: #ccc; 
            cursor: not-allowed; 
            transform: none;
            box-shadow: none;
        }
        .result { 
            margin-top: 20px; 
            padding: 20px; 
            background: #f8f9fa; 
            border-radius: 8px; 
            border-left: 4px solid #1da1f2;
            white-space: pre-wrap; 
            font-family: 'Courier New', monospace;
            max-height: 400px;
            overflow-y: auto;
        }
        .quick-actions { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin-bottom: 30px;
        }
        .quick-action { 
            padding: 15px; 
            background: #f8f9fa; 
            border: 2px solid #e9ecef; 
            border-radius: 8px; 
            cursor: pointer; 
            transition: all 0.3s;
            text-align: center;
        }
        .quick-action:hover { 
            background: #e9ecef; 
            border-color: #1da1f2; 
            transform: translateY(-2px);
        }
        .loading { 
            display: none; 
            text-align: center; 
            margin: 20px 0;
        }
        .spinner { 
            border: 4px solid #f3f3f3; 
            border-top: 4px solid #1da1f2; 
            border-radius: 50%; 
            width: 40px; 
            height: 40px; 
            animation: spin 1s linear infinite; 
            margin: 0 auto;
        }
        @keyframes spin { 
            0% { transform: rotate(0deg); } 
            100% { transform: rotate(360deg); } 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Twitter Agent Server</h1>
            <p>Intelligent Twitter automation at your fingertips</p>
        </div>
        
        <div class="status ready">
            ✅ Agent Ready - Server running on {{ request.url_root }}
        </div>
        
        <div class="quick-actions">
            <div class="quick-action" onclick="setQuickCommand('tweet', 'What would you like to tweet?')">
                🐦 Quick Tweet
            </div>
            <div class="quick-action" onclick="setQuickCommand('schedule_space', 'Title: My Space\\nTime: tomorrow 3pm\\nTopics: AI, Tech')">
                🎙️ Schedule Space
            </div>
            <div class="quick-action" onclick="setQuickCommand('check_analytics', 'Show me analytics for the past week')">
                📊 Check Analytics
            </div>
            <div class="quick-action" onclick="setQuickCommand('get_status', 'What\\'s my current session status?')">
                ⚡ Get Status
            </div>
        </div>
        
        <form class="command-form" onsubmit="executeCommand(event)">
            <div class="form-group">
                <label for="command">Command:</label>
                <textarea id="command" name="command" placeholder="Enter your command here... (e.g., 'tweet Hello world!' or 'schedule a space for tomorrow at 3pm about AI')" required></textarea>
            </div>
            <button type="submit" id="submit-btn">Execute Command</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Executing command...</p>
        </div>
        
        <div class="result" id="result" style="display: none;"></div>
    </div>
    
    <script>
        function setQuickCommand(type, template) {
            document.getElementById('command').value = template;
        }
        
        async function executeCommand(event) {
            event.preventDefault();
            
            const command = document.getElementById('command').value;
            const submitBtn = document.getElementById('submit-btn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            
            // Show loading
            submitBtn.disabled = true;
            loading.style.display = 'block';
            result.style.display = 'none';
            
            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ command: command })
                });
                
                const data = await response.json();
                
                // Show result
                result.textContent = data.result;
                result.style.display = 'block';
                
                // Scroll to result
                result.scrollIntoView({ behavior: 'smooth' });
                
            } catch (error) {
                result.textContent = `❌ Error: ${error.message}`;
                result.style.display = 'block';
            } finally {
                // Hide loading
                loading.style.display = 'none';
                submitBtn.disabled = false;
            }
        }
        
        // Auto-focus command input
        document.getElementById('command').focus();
    </script>
</body>
</html>
"""

# Reuse the same template for /chat for compatibility
CHAT_TEMPLATE = WEB_TEMPLATE

@app.route('/')
def index():
    """Serve the web interface"""
    return render_template_string(WEB_TEMPLATE, request=request)

# Compatibility route for legacy /chat URL
@app.route('/chat')
def chat_panel():
    """Serve the chat panel (legacy route)."""
    return render_template_string(CHAT_TEMPLATE, request=request)

@app.route('/api/command', methods=['POST'])
def execute_command():
    """API endpoint to execute commands"""
    try:
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({'error': 'No command provided'}), 400
        
        command = data['command']
        logger.info(f"Executing command: {command}")
        
        # Ensure agent is initialized
        initialize_agent()
        
        # Execute command
        result = run_async_command(command)
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in execute_command: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/status')
def get_status():
    """Get agent status"""
    try:
        if agent is None:
            return jsonify({
                'status': 'not_initialized',
                'message': 'Agent not initialized'
            })
        
        status = agent.get_status()
        return jsonify({
            'status': 'ready',
            'agent_status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/initialize', methods=['POST'])
def initialize():
    """Initialize the agent manually"""
    try:
        initialize_agent()
        return jsonify({
            'success': True,
            'message': 'Agent initialized successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """Shutdown the agent"""
    try:
        global agent
        with agent_lock:
            if agent:
                agent.shutdown()
                agent = None
        
        return jsonify({
            'success': True,
            'message': 'Agent shutdown successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("🤖 Starting Twitter Agent Server...")
    print("📡 Initializing agent on startup...")
    
    # Initialize agent on startup
    try:
        initialize_agent()
        print("✅ Agent initialized successfully!")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize agent on startup: {e}")
        print("💡 Agent will be initialized on first request")
    
    print("🌐 Starting web server...")
    print("🔗 Web Interface: http://localhost:5000")
    print("🔌 API Endpoint: http://localhost:5000/api/command")
    print("📊 Status Endpoint: http://localhost:5000/api/status")
    print("\n🚀 Server ready! Open http://localhost:5000 in your browser")
    
    app.run(
        host='0.0.0.0',  # Accept connections from any IP
        port=5000,
        debug=False,     # Disable debug mode for production
        threaded=True    # Handle multiple requests
    ) 