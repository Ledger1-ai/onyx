from flask import Blueprint, request, redirect, session, jsonify, url_for
from urllib.parse import urlencode
import requests
import os
import time
from datetime import datetime
import logging
from database_manager import DatabaseManager

# Setup Logging
logger = logging.getLogger(__name__)

# Create Blueprint
oauth_bp = Blueprint('oauth', __name__, url_prefix='/api/auth')

# Initialize DB (Lazy load)
db_manager = DatabaseManager()

# --- Configuration (loaded from env) ---
# In a real SaaS, these would be the "App" credentials
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")

# TODO: Make this dynamic for production
BASE_URL = "http://localhost:8000"

# --- Helper: Get Current User ---
def get_current_user_id():
    # In a real app, this comes from session/JWT
    # For MVP Single-Tenant, we use the centralized default from Config
    from config import Config
    return session.get("user_id", getattr(Config, "DEFAULT_USER_ID", "admin_user"))

# --- STATUS ENDPOINT ---
@oauth_bp.route('/status', methods=['GET'])
def get_auth_status():
    """
    Returns the status of connections for the current user.
    Distinguishes between API (SaaS) and Bot (Selenium).
    """
    user_id = get_current_user_id()
    
    # Check Database for API Tokens
    user = db_manager.get_user(user_id)
    creds = {}
    
    api_status = {
        "linkedin": False,
        "facebook": False,
        "instagram": False,
        "twitter": False
    }
    
    # Bot status - database-driven with filesystem fallback
    bot_status = {
        "linkedin": False,
        "twitter": False,
        "meta": False
    }
    
    if user:
        creds = user.get("credentials", {})
        # API Status
        api_status["linkedin"] = creds.get("linkedin", {}).get("is_active", False)
        api_status["facebook"] = creds.get("facebook", {}).get("is_active", False)
        api_status["instagram"] = creds.get("instagram", {}).get("is_active", False)
        api_status["twitter"] = creds.get("twitter", {}).get("is_active", False)
        
        # Bot Status from database (preferred for multi-tenant)
        bot_status["twitter"] = creds.get("twitter_bot", {}).get("is_active", False)
        bot_status["linkedin"] = creds.get("linkedin_bot", {}).get("is_active", False)

    # Filesystem fallback for bot status (backward compatibility)
    if not bot_status["linkedin"]:
        if os.path.exists("browser_profiles/linkedin_auth.json"):
            bot_status["linkedin"] = True
    
    if not bot_status["twitter"]:
        # Check profile directory (correct path) instead of legacy cookies.pkl
        twitter_profile_dir = "browser_profiles/twitter_automation_profile"
        if os.path.exists(twitter_profile_dir):
            bot_status["twitter"] = True
    
    if not bot_status["meta"]:
        if os.path.exists("browser_profiles/meta_auth.json"):
            bot_status["meta"] = True
    
    # Return response in format expected by frontend:
    # { twitter: { api: bool, bot: bool }, linkedin: { api: bool, bot: bool }, ... }
    return jsonify({
        "twitter": { "api": api_status["twitter"], "bot": bot_status["twitter"] },
        "linkedin": { "api": api_status["linkedin"], "bot": bot_status["linkedin"] },
        "facebook": { "api": api_status["facebook"], "bot": bot_status.get("meta", False) },
        "instagram": { "api": api_status["instagram"], "bot": False }
    })

# --- LINKEDIN OAUTH ---

@oauth_bp.route('/connect/linkedin')
def connect_linkedin():
    if not LINKEDIN_CLIENT_ID:
        return jsonify({"error": "Missing LinkedIn Configuration"}), 500
        
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/api/auth/callback/linkedin",
        "scope": "openid profile email w_member_social w_organization_social",
        "state": "random_state_string" 
    }
    url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return redirect(url)

@oauth_bp.route('/callback/linkedin')
def callback_linkedin():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided", 400
        
    # Exchange for Token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": f"{BASE_URL}/api/auth/callback/linkedin",
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET
    }
    
    res = requests.post(token_url, data=data)
    if res.status_code != 200:
        return f"Error exchanging token: {res.text}", 400
        
    token_data = res.json()
    access_token = token_data.get("access_token")
    
    # Fetch User Details (URN)
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    me_data = me_res.json()
    person_urn = f"urn:li:person:{me_data.get('sub')}"
    
    # Save to DB
    user_id = get_current_user_id()
    db_manager.save_credential(user_id, "linkedin", {
        "access_token": access_token,
        "platform_user_id": person_urn,
        "name": me_data.get("name"),
        "is_active": True,
        "updated_at": datetime.now().isoformat()
    })
    
    return redirect("/") # Redirect back to dashboard

# --- META (FACEBOOK) OAUTH ---

@oauth_bp.route('/connect/facebook')
def connect_facebook():
    if not META_APP_ID:
        return jsonify({"error": "Missing Meta Configuration"}), 500
        
    params = {
        "client_id": META_APP_ID,
        "redirect_uri": f"{BASE_URL}/api/auth/callback/facebook",
        "scope": "pages_show_list,pages_read_engagement,pages_manage_posts,pages_manage_engagement,pages_messaging,instagram_basic,instagram_content_publish,instagram_manage_comments,instagram_manage_messages",
        "state": "random_state_string",
        "response_type": "code"
    }
    url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"
    return redirect(url)

@oauth_bp.route('/callback/facebook')
def callback_facebook():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided", 400
        
    # Exchange for User Token
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": META_APP_ID,
        "redirect_uri": f"{BASE_URL}/api/auth/callback/facebook",
        "client_secret": META_APP_SECRET,
        "code": code
    }
    
    res = requests.get(token_url, params=params)
    data = res.json()
    
    if "error" in data:
        return f"Error exchanging token: {data['error']}", 400
        
    short_token = data['access_token']
    
    # Exchange for Long-Lived Token (Crucial for Server-Side)
    exchange_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    exchange_params = {
        "grant_type": "fb_exchange_token",
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "fb_exchange_token": short_token
    }
    
    long_res = requests.get(exchange_url, params=exchange_params)
    long_data = long_res.json()
    long_token = long_data.get('access_token', short_token) # Fallback if fails
    
    # Verify Permissions / Get User ID
    me_res = requests.get("https://graph.facebook.com/me", params={"access_token": long_token})
    me_data = me_res.json()
    
    # Save to DB
    user_id = get_current_user_id()
    db_manager.save_credential(user_id, "facebook", {
        "access_token": long_token,
        "platform_user_id": me_data.get("id"),
        "name": me_data.get("name"),
        "is_active": True,
        "updated_at": datetime.now().isoformat()
    })
    
    # Also mark as Instagram active (since it's the same token usually)
    db_manager.save_credential(user_id, "instagram", {
        "access_token": long_token,
        "is_active": True,
        "linked_via": "facebook"
    })
    
    return redirect("/")
    return redirect("/")

# --- TWITTER OAUTH ---

TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")

@oauth_bp.route('/connect/twitter')
def connect_twitter():
    if not TWITTER_CLIENT_ID:
        return jsonify({"error": "Twitter OAuth not configured. Set TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET environment variables."}), 400
    
    # Twitter OAuth 2.0 PKCE flow usually requires more complex state/verifier handling
    # For MVP, generating a simple state. In production, use session for verifier.
    state = "random_state" # TODO: Secure this
    code_challenge = "challenge" # In real app, compute S256(verifier)
    
    params = {
        "response_type": "code",
        "client_id": TWITTER_CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/api/auth/callback/twitter",
        "scope": "tweet.read tweet.write users.read offline.access",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "plain" 
    }
    url = f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"
    return redirect(url)

@oauth_bp.route('/callback/twitter')
def callback_twitter():
    code = request.args.get('code')
    if not code:
        return "Error: No code", 400
        
    token_url = "https://api.twitter.com/2/oauth2/token"
    auth = (TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": TWITTER_CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/api/auth/callback/twitter",
        "code_verifier": "challenge" # Must match request
    }
    
    res = requests.post(token_url, data=data, auth=auth)
    if res.status_code != 200:
        return f"Error: {res.text}", 400
        
    token_data = res.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    
    # Get User ID
    # user_res = requests.get("https://api.twitter.com/2/users/me", headers={"Authorization": f"Bearer {access_token}"})
    # user_data = user_res.json().get("data", {})
    
    user_id = get_current_user_id()
    db_manager.save_credential(user_id, "twitter", {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "is_active": True,
        "updated_at": datetime.now().isoformat()
    })
    
    return redirect("/")

# --- DISCONNECT ---

@oauth_bp.route('/disconnect/<platform>', methods=['POST'])
def disconnect_platform(platform):
    """
    Disconnects the API credential for the specified platform.
    """
    user_id = get_current_user_id()
    
    # Deactivate in DB
    try:
        db_manager.save_credential(user_id, platform, {
            "access_token": None,
            "is_active": False,
            "updated_at": datetime.now().isoformat()
        })
        return jsonify({"status": "success", "message": f"Disconnected {platform} API"})
    except Exception as e:
        logger.error(f"Error disconnecting {platform}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
