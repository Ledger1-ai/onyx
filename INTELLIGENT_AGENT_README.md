# Intelligent Twitter Super Agent

An advanced AI-powered Twitter agent that uses Azure OpenAI's Responses API with tool calling to autonomously manage Twitter engagement and content strategy for The Utility Company.

## 🚀 Features

### Tool-Based Architecture
- **Switchable Operation Modes**: Reply bot, trending monitor, quote tweeting, content creation, account discovery
- **Dynamic Tool Selection**: AI decides which tools to use based on context and objectives
- **State Management**: Maintains conversation context and operational state across sessions

### Background Monitoring
- **Automatic Reply Detection**: Checks for new replies every 5 minutes
- **Smart Reactivation**: Wakes up from pause mode when replies are detected
- **Performance Tracking**: Continuous monitoring of engagement metrics

### Intelligent Features
- **Dynamic Account Discovery**: AI-powered identification of relevant accounts to engage with
- **Adaptive Strategy**: Adjusts engagement patterns based on performance data
- **Pause/Resume Functionality**: Can pause operations and resume when needed

## 🛠️ Installation & Setup

### Prerequisites
```bash
pip install openai selenium sqlite3 requests aiohttp
```

### Configuration
1. Ensure `config.env` is properly configured with Twitter credentials
2. Verify `agent_config.json` contains your target keywords and preferences
3. Set up Azure OpenAI credentials in environment variables

### File Structure
```
x-scraper/
├── intelligent_agent.py          # Main intelligent agent with tool calling
├── launch_intelligent_agent.py   # Launcher script with multiple modes
├── bot_controller.py             # Core Twitter functionality
├── selenium_scraper.py           # Web scraping capabilities
├── agent_config.json             # Agent configuration
├── config.env                    # Environment configuration
└── account_manager.py            # Account management utilities
```

## 🎯 Usage

### Interactive Mode (Recommended for Testing)
```bash
python launch_intelligent_agent.py --interactive
```

This starts an interactive session where you can:
- Issue natural language commands
- Switch between operational modes
- Monitor performance in real-time
- Test individual functions

#### Example Commands:
```
> switch to reply mode with professional style
> execute current mode
> get performance summary
> pause for 30 minutes
> check reply status
> switch to trending mode with moderate engagement
> return to main mode
```

### Autonomous Mode
```bash
# Run for 1 hour (default)
python launch_intelligent_agent.py --autonomous

# Run for 4 hours
python launch_intelligent_agent.py --autonomous --hours 4
```

### Tool Testing
```bash
python launch_intelligent_agent.py --test-tools
```

### Single Command Execution
```bash
python launch_intelligent_agent.py --command "switch to content mode"
```

## 🔧 Available Tools

### Mode Switching Tools
- `switch_to_reply_mode` - Monitor and respond to tweet replies
- `switch_to_trending_mode` - Engage with trending topics
- `switch_to_quote_mode` - Find and quote tweet opportunities
- `switch_to_content_mode` - Create original content
- `switch_to_discovery_mode` - Discover new relevant accounts
- `return_to_main_mode` - Return to main control interface

### Operational Tools
- `set_pause_timer` - Pause agent for specified duration
- `check_reply_status` - Check for new replies to recent tweets
- `get_performance_summary` - View engagement metrics
- `execute_current_mode` - Run the active mode's primary function
- `analyze_and_adjust_strategy` - AI-driven strategy optimization

## 🧠 How the AI Agent Works

### 1. Tool Selection
The agent uses Azure OpenAI's Responses API to intelligently select which tools to use based on:
- Current context and conversation
- Performance metrics
- Mission alignment with The Utility Company's goals

### 2. State Management
- Maintains conversation context across tool calls
- Tracks current operational mode and task
- Preserves pause/resume state

### 3. Background Monitoring
```python
# Automatic reply checking every 5 minutes
def _reply_monitor_loop(self):
    while self.reply_monitor_active:
        self._check_for_new_replies()
        time.sleep(300)  # 5 minutes
```

### 4. Intelligent Decision Making
The agent considers:
- Company mission and values
- Recent performance data
- Engagement patterns
- Reply sentiment and context

## 📊 Performance Monitoring

The agent automatically tracks:
- **Reply Metrics**: Response rate, engagement quality
- **Trending Interactions**: Successful trend engagements
- **Quote Tweet Performance**: Engagement on quote tweets
- **Content Creation**: Original post performance
- **Account Discovery**: Quality of discovered accounts

### Database Tables
- `replies` - Reply bot activities
- `trending_interactions` - Trending topic engagements
- `quote_tweets` - Quote tweet activities
- `content_posts` - Original content posts
- `discovered_accounts` - AI-discovered relevant accounts
- `analytics_data` - Performance metrics

## 🎛️ Configuration Options

### Agent Personality (in `intelligent_agent.py`)
- Professional yet approachable
- Focused on community empowerment
- Strategic engagement decisions
- Transparent about AI nature

### Operational Modes
Each mode has configurable parameters:

```python
# Reply Mode
{
    "auto_engage": True,
    "response_style": "professional|casual|insightful_sage|supportive_community"
}

# Trending Mode  
{
    "keywords": ["AI", "automation", "blockchain"],
    "engagement_level": "conservative|moderate|active"
}

# Quote Mode
{
    "target_accounts": ["elonmusk", "OpenAI"],
    "commentary_style": "analytical|supportive|educational|thought_provoking"
}
```

## 🔒 Safety Features

### Rate Limiting
- Respects Twitter's API limits
- Built-in delays between actions
- Configurable action limits per session

### Pause Functionality
- Manual pause/resume control
- Automatic pause on rate limit detection
- Emergency stop capabilities

### Content Filtering
- Alignment with company values
- Avoids controversial topics
- Quality checks before posting

## 🐛 Troubleshooting

### Common Issues

1. **Agent Not Responding**
   ```bash
   # Check if paused
   python launch_intelligent_agent.py --command "check reply status"
   ```

2. **Tool Call Errors**
   ```bash
   # Test all tools
   python launch_intelligent_agent.py --test-tools
   ```

3. **Database Issues**
   ```bash
   # Recreate database tables
   python bot_controller.py --init-db
   ```

### Logging
Check log files for detailed information:
- `intelligent_agent.log` - Main agent operations
- `agent_launcher.log` - Launcher activities
- `twitter_agent.log` - Twitter-specific activities

## 🔮 Advanced Usage

### Custom Tool Development
Add new tools by extending the `_define_tools()` method:

```python
{
    "type": "function",
    "name": "custom_tool",
    "description": "Your custom tool description",
    "parameters": {
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter description"}
        },
        "required": ["param"]
    }
}
```

### Integration with Other Systems
The agent can be integrated with:
- Discord bots (like Vader.py)
- Web dashboards
- Analytics platforms
- Content management systems

## 📈 Performance Optimization

### Best Practices
1. Start with discovery mode to build relevant account list
2. Use moderate engagement levels initially
3. Monitor performance metrics regularly
4. Adjust strategy based on data insights

### Scaling
- Run multiple instances for different topics
- Use different configurations per target audience
- Implement A/B testing for engagement strategies

## 🆘 Support

For issues or questions:
1. Check the log files first
2. Test individual tools
3. Review configuration settings
4. Contact The Utility Company technical team

---

*The Intelligent Twitter Super Agent embodies The Utility Company's mission of Industrial Automation as a Service, bringing AI-powered automation to social media engagement while maintaining authentic community connections.* 