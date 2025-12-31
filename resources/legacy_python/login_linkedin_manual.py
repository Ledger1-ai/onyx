from linkedin_scraper import LinkedInScraper
import time

def manual_login():
    print("[INIT] Initializing LinkedIn Browser for Manual Login...")
    print("[WARN]  A browser window will open. Please log in to LinkedIn manually.")
    print("[WARN]  Complete any 2FA or captcha challenges.")
    print("[WARN]  Once you see your Feed, come back here and press ENTER.")
    
    # Initialize with headless=False so user can see it
    scraper = LinkedInScraper(headless=False, use_persistent_profile=True)
    
    # Navigate to login
    scraper.driver.get("https://www.linkedin.com/login")
    
    # Wait for user confirmation
    input("\n[ACTION] Press ENTER after you have successfully logged in and can see your feed...")
    
    if scraper.check_login_status():
        print("\n[SUCCESS] Login verified! Session saved to profile directory.")
        print(f"Directory Profile Location: {scraper.profile_dir}")
        
        # Create a success marker file for the dashboard to check
        import os
        # Save insde profile (legacy)
        marker_path = os.path.join(scraper.profile_dir, "auth_success.marker")
        
        # Save outside profile (safer)
        safe_marker_path = os.path.join("browser_profiles", "linkedin_auth.json")
        
        try:
            with open(marker_path, "w") as f:
                f.write("authenticated")
                
            import json
            with open(safe_marker_path, "w") as f:
                json.dump({"status": "authenticated", "timestamp": time.time()}, f)
                
            print("[INFO] Dashboard authentication marker created.")
        except Exception as e:
            print(f"[WARN] Failed to create marker file: {e}")
            
        print("You can now run the automated bot.")
    else:
        print("\n[FAIL] Login verification failed. Please try again.")

    # Cleanup
    scraper.driver.quit()

if __name__ == "__main__":
    manual_login()
