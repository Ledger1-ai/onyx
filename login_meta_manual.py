from meta_scraper import MetaScraper
from database_manager import DatabaseManager
from data_models import User, PlatformCredentials
from datetime import datetime
import time

def main():
    print("="*60)
    print("🔐 ANUBIS META LOGIN UTILITY (SaaS Mode)")
    print("="*60)
    print("This tool helps you log in to Facebook/Instagram and saves the SESSION COOKIES to the Database.")
    print("This allows the Bot/Scraper to run as 'you' without a persistent browser profile.")
    print("-" * 60)

    user_id = input("Enter User ID to attach these credentials to (default: admin_user): ").strip() or "admin_user"
    
    print(f"\n📂 Connecting to Database for user: {user_id}...")
    db = DatabaseManager()
    user = db.get_user(user_id)
    
    if not user:
        print(f"⚠️ User '{user_id}' not found. Creating new user record...")
        user = User(user_id=user_id, email=f"{user_id}@example.com", name="Admin")
    
    try:
        scraper = MetaScraper(headless=False)
        
        # Facebook
        if input(">> Log in to Facebook? (y/n): ").lower() == 'y':
            scraper.login_facebook_manual()
        
        # Instagram
        if input(">> Log in to Instagram? (y/n): ").lower() == 'y':
            scraper.login_instagram_manual()
            
        print("\n🍪 Extracting Cookies...")
        cookies = scraper.get_cookies()
        
        if cookies:
            print(f"✅ Captured {len(cookies)} cookies.")
            
            # Save to 'facebook' and 'instagram' credentials
            # In a real scenario, we might want to separate them if domains differ significantly,
            # but usually they are shared or overlapping in the same session.
            
            fb_creds = user.credentials.get("facebook", PlatformCredentials())
            fb_creds.session_cookies = cookies
            fb_creds.is_active = True
            user.credentials["facebook"] = fb_creds
            
            ig_creds = user.credentials.get("instagram", PlatformCredentials())
            ig_creds.session_cookies = cookies # Sharing session for now
            ig_creds.is_active = True
            user.credentials["instagram"] = ig_creds
            
            if db.save_user(user):
                print("💾 SUCCESS: Cookies saved to MongoDB!")
            else:
                print("❌ FAILED to save to MongoDB.")
        else:
            print("⚠️ No cookies captured.")

        print("\n✅ Session setup complete! You can close this window.")
        time.sleep(2)
        scraper.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press ENTER to exit...")

if __name__ == "__main__":
    main()
