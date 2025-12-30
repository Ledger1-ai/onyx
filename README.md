# Twitter Automation Bot

A powerful, API-free Twitter automation bot that uses web scraping to control your Twitter account autonomously. This bot can post tweets, reply to others, search for trending content, retweet, and follow users - all without requiring Twitter API access.

## ⚠️ Important Disclaimer

This bot is for educational and personal use only. Please ensure you comply with Twitter's Terms of Service and use this tool responsibly. Avoid spam-like behavior and respect rate limits to prevent account suspension.

## 🚀 Features

- **🤖 Autonomous Operations**: Fully automated Twitter management
- **📝 Tweet Posting**: Generate and post tweets automatically
- **💬 Smart Replies**: Reply to tweets with contextual responses  
- **🔄 Retweet System**: Automatically retweet relevant content
- **🔍 Content Search**: Search and engage with trending topics
- **👥 User Following**: Follow users based on trending topics
- **📊 Activity Tracking**: Comprehensive logging and statistics
- **⚡ Rate Limiting**: Built-in protection against spam detection
- **🎯 Keyword Targeting**: Focus on specific topics and hashtags
- **🔒 Anti-Detection**: Human-like behavior patterns and delays

## 🛠️ Installation

### Prerequisites

- Python 3.7 or higher
- Google Chrome browser
- Windows, macOS, or Linux

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd x-scraper
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configuration

1. Copy the example configuration file:
   ```bash
   cp config.env.example .env
   ```

2. Edit the `.env` file with your Twitter credentials:
   ```env
   # Twitter Account Credentials
   TWITTER_USERNAME=your_username_here
   TWITTER_PASSWORD=your_password_here  
   TWITTER_EMAIL=your_email_here
   
   # Bot Configuration
   MAX_TWEETS_PER_HOUR=10
   MAX_REPLIES_PER_HOUR=20
   MAX_RETWEETS_PER_HOUR=15
   SEARCH_KEYWORDS=python,AI,technology
   TARGET_HASHTAGS=#python,#AI,#tech
   
   # Selenium Configuration
   HEADLESS_MODE=true
   IMPLICIT_WAIT=10
   ```

## 🎮 Usage

### Command Line Interface

The bot includes a comprehensive CLI for easy control:

```bash
# Run in interactive mode
python main.py

# Full autonomous mode
python main.py --autonomous

# Post a specific tweet
python main.py --tweet "Hello, Twitter! 🚀"

# Post an auto-generated tweet
python main.py --auto-tweet

# Search and engage with tweets
python main.py --search "python programming" --max 10

# Follow a user
python main.py --follow elonmusk

# Show trending topics
python main.py --trending

# Show activity statistics
python main.py --stats

# Test login functionality
python main.py --test-login
```

### Interactive Mode

Run `python main.py` without arguments to enter interactive mode with a menu-driven interface.

### Autonomous Mode

The autonomous mode is the core feature that runs the bot continuously:

```python
from twitter_bot import TwitterBot

bot = TwitterBot()
bot.start_autonomous_mode()  # Runs indefinitely
```

## 🔧 Configuration Options

### Bot Behavior Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `MAX_TWEETS_PER_HOUR` | Maximum tweets per hour | 10 |
| `MAX_REPLIES_PER_HOUR` | Maximum replies per hour | 20 |
| `MAX_RETWEETS_PER_HOUR` | Maximum retweets per hour | 15 |
| `SEARCH_KEYWORDS` | Keywords to search for | python,AI,technology |
| `TARGET_HASHTAGS` | Hashtags to use in tweets | #python,#AI,#tech |

### Selenium Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `HEADLESS_MODE` | Run browser in background | true |
| `IMPLICIT_WAIT` | Wait time for elements | 10 |

## 🎯 Bot Strategies

### Autonomous Actions

The bot performs weighted random actions:

- **Search & Engage (40%)**: Finds and interacts with relevant tweets
- **Post Tweet (30%)**: Creates and posts original content
- **Follow Users (10%)**: Follows users from trending topics
- **Rest (20%)**: Maintains natural activity patterns

### Content Generation

- Uses template-based tweet generation
- Incorporates trending keywords
- Adds relevant hashtags automatically
- Generates contextual replies

### Rate Limiting

- Respects hourly limits for all actions
- Implements minimum delays between actions
- Uses random delays to mimic human behavior
- Tracks activity to prevent spam detection

## 📊 Activity Logging

The bot maintains detailed logs of all activities:
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "action": "tweet",
  "details": {
    "content": "Exploring AI today. What are your thoughts? 🤔 #AI",
    "success": true
  }
}
```

View statistics with:
```bash
python main.py --stats
```

## 🔍 Advanced Usage

### Custom Tweet Templates

Modify the `generate_tweet_content()` method in `twitter_bot.py` to customize tweet templates:

```python
templates = [
    "Your custom template with {topic}! 🚀",
    "Another template about {topic} 💡",
    # Add more templates
]
```

### Search Strategies

Customize search behavior by modifying the `search_and_engage()` method:

```python
# Search for specific tweet types
query = f"{keyword} -is:retweet lang:en"
tweets = self.scraper.search_tweets(query, max_results=10)
```

### Engagement Rules

Modify engagement logic in the bot's decision-making process:

```python
# Custom engagement decision
if tweet_metrics['like_count'] > 100:
    action = 'retweet'
elif 'question' in tweet['text'].lower():
    action = 'reply'
```

## 🛡️ Security & Best Practices

### Account Safety

1. **Start Slowly**: Begin with low activity rates
2. **Monitor Activity**: Check logs regularly
3. **Use Delays**: Maintain natural timing patterns
4. **Avoid Spam**: Don't repeat content or actions
5. **Respect Limits**: Stay within configured rate limits

### Recommended Settings

For new accounts or cautious usage:

```env
MAX_TWEETS_PER_HOUR=5
MAX_REPLIES_PER_HOUR=10
MAX_RETWEETS_PER_HOUR=8
HEADLESS_MODE=true
```

### Detection Avoidance

The bot includes several anti-detection features:

- Random user agents
- Human-like typing delays
- Varied action timing
- Browser fingerprint masking
- Natural pause patterns

## 🐛 Troubleshooting

### Common Issues

**Login Failures**
- Verify credentials in `.env` file
- Check for 2FA requirements
- Ensure account isn't locked

**Element Not Found Errors**
- Twitter may have updated their interface
- Try running in non-headless mode for debugging
- Check Chrome version compatibility

**Rate Limiting**
- Reduce action frequencies in configuration
- Increase delays between actions
- Monitor activity logs

### Debug Mode

Run with visible browser for debugging:

```env
HEADLESS_MODE=false
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational purposes. Use responsibly and in accordance with Twitter's Terms of Service.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `twitter_bot.log`
3. Create an issue with detailed information

## 🔐 **Persistent Login Sessions**

The agent now supports **persistent browser profiles** so you don't have to login to Twitter every time!

### **First-Time Setup**
```bash
# Setup your login once
python launch_intelligent_agent.py --setup-login
```

This will:
1. Open a browser window to Twitter login
2. Guide you through manual login process
3. Save your session for future use
4. Handle 2FA and security challenges automatically

### **Daily Usage**
```bash
# Just run normally - no login needed!
python launch_intelligent_agent.py --interactive

# Or autonomous mode
python launch_intelligent_agent.py --autonomous --mode hybrid --hours 2
```

The agent will automatically detect your saved session and continue where you left off.

### **Profile Management**
```bash
# Clear saved login (logout)
python launch_intelligent_agent.py --clear-login

# Disable persistent profiles (login each time)
python launch_intelligent_agent.py --interactive --no-persistent-profile

# Run in headless mode (no browser window)
python launch_intelligent_agent.py --interactive --headless
```

### **How It Works**
- Creates a `browser_profiles/` directory in your workspace
- Saves Chrome profile data including cookies, localStorage, etc.
- Automatically detects if you're already logged in
- Falls back to manual login if session expires

### **Benefits**
✅ **No daily logins** - Login once, use forever  
✅ **Faster startup** - Skip authentication delay  
✅ **Better security** - No need to store passwords in memory  
✅ **2FA compatible** - Handle complex authentication once  
✅ **Multiple profiles** - Can support multiple Twitter accounts

---

**Remember**: This tool is powerful but should be used ethically and responsibly. Always respect platform rules and other users. 