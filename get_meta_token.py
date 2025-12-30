import requests
import os
import webbrowser
import json

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("="*60)
    print("      ANUBIS META (FACEBOOK/INSTAGRAM) SETUP HELPER")
    print("="*60)

def open_graph_explorer():
    print("\n[STEP 1] Generating a Short-Lived User Token")
    print("1. I will open the Meta Graph API Explorer.")
    print("2. Ensure your correct Facebook App is selected.")
    print("3. In 'User or Page', select 'User Token'.")
    print("4. Add Permissions: pages_show_list, pages_read_engagement, pages_manage_posts, pages_manage_engagement, pages_messaging, instagram_basic, instagram_content_publish, instagram_manage_comments, instagram_manage_messages")
    print("5. Click 'Generate Access Token'.")
    print("6. Copy the token and paste it here.")
    
    input("\nPress Enter to open Graph Explorer...")
    webbrowser.open("https://developers.facebook.com/tools/explorer/")

def get_long_lived_token(app_id, app_secret, short_token):
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token
    }
    
    try:
        res = requests.get(url, params=params)
        data = res.json()
        if "access_token" in data:
            return data["access_token"]
        else:
            print(f"\n[ERROR] Failed to exchange token: {data.get('error', {}).get('message')}")
            return None
    except Exception as e:
        print(f"\n[ERROR] Request failed: {e}")
        return None

def get_pages(access_token):
    url = "https://graph.facebook.com/v19.0/me/accounts"
    params = {
        "access_token": access_token,
        "fields": "id,name,instagram_business_account"
    }
    
    try:
        res = requests.get(url, params=params)
        data = res.json()
        
        if "data" in data:
            return data["data"]
        else:
            print(f"\n[ERROR] API Response: {json.dumps(data, indent=2)}")
            return []
    except Exception as e:
        print(f"\n[ERROR] Failed to fetch pages: {e}")
        return []

def main():
    clear_screen()
    print_header()
    
    print("\nTo proceed, you need your Meta App ID and App Secret from the App Dashboard.")
    app_id = input("Enter App ID: ").strip()
    app_secret = input("Enter App Secret: ").strip()
    
    if not app_id or not app_secret:
        print("[ERROR] App ID and Secret are required.")
        return

    open_graph_explorer()
    
    short_token = input("\nPaste Short-Lived Access Token: ").strip()
    
    if not short_token:
        print("[ERROR] Token required.")
        return

    # Debug the token to see what permissions it ACTUALLY has
    debug_url = "https://graph.facebook.com/v19.0/debug_token"
    app_access_token = f"{app_id}|{app_secret}"
    
    try:
        debug_res = requests.get(debug_url, params={
            "input_token": short_token,
            "access_token": app_access_token
        })
        debug_data = debug_res.json()
        
        if "data" in debug_data:
            scopes = debug_data["data"].get("scopes", [])
            print(f"\n[DEBUG] Token Scopes Verified: {scopes}")
            
            required = ["pages_read_engagement", "pages_manage_engagement", "instagram_manage_comments", "pages_messaging", "instagram_manage_messages"]
            missing = [r for r in required if r not in scopes]
            
            if missing:
                print(f"❌ WARNING: Your token is MISSING these permissions: {missing}")
                print("👉 Did you click 'Generate Access Token' blue button after checking the boxes?")
            else:
                print("✅ Token permissions look correct.")
        else:
            print(f"[DEBUG] Could not verify token scopes: {debug_data}")
            
    except Exception as e:
        print(f"[ERROR] Token debugging failed: {e}")

    print("\n[STEP 2] Exchanging for Long-Lived Token...")
    long_token = get_long_lived_token(app_id, app_secret, short_token)
    
    if not long_token:
        print("Could not retrieve long-lived token. Exiting.")
        return
    
    print(f"\n✅ SUCCESS! Long-Lived Token retrieved.")
    print(f"Token (First 20 chars): {long_token[:20]}...")
    
    print("\n[STEP 3] Fetching Pages and Instagram Accounts...")
    pages = get_pages(long_token)
    
    fb_page_id = None
    ig_user_id = None
    
    if not pages:
        print("\n[WARN] Could not auto-detect pages (Permissions issue?).")
        manual = input(">> Do you want to enter your Page ID manually? (y/n): ").lower()
        if manual == 'y':
            fb_page_id = input("Enter Facebook Page ID: ").strip()
            ig_user_id = input("Enter Instagram Business ID (Optional): ").strip()
        else:
            return
    else:
        print(f"\nFound {len(pages)} Page(s):")
        for idx, page in enumerate(pages):
            ig_info = " (Linked IG: " + page.get('instagram_business_account', {}).get('id', 'None') + ")"
            print(f"[{idx}] {page['name']} (ID: {page['id']}){ig_info}")
            
        choice = input("\nSelect a Page to use (Enter number): ").strip()
        try:
            selected_page = pages[int(choice)]
            fb_page_id = selected_page['id']
            ig_user_id = selected_page.get('instagram_business_account', {}).get('id', '')
        except:
            print("Invalid selection.")
            return

    if not fb_page_id:
        print("No Page ID Configure. Exiting.")
        return
    
    print("\n" + "="*60)
    print("      CONFIGURATION GENERATED")
    print("="*60)
    print("\nCopy these lines into your config.env file:\n")
    
    print(f"META_ACCESS_TOKEN={long_token}")
    print(f"META_PAGE_ID={fb_page_id}")
    if ig_user_id:
        print(f"META_IG_USER_ID={ig_user_id}")
    else:
        print("# META_IG_USER_ID=  <-- No Instagram account linked to this page")
        
    print("\n" + "="*60)
    
    save = input("\nDo you want me to append these to config.env automatically? (y/n): ").lower()
    if save == 'y':
        try:
            with open('config.env', 'a') as f:
                f.write(f"\n\n# Meta API Configuration (Generated by Script)\n")
                f.write(f"META_ACCESS_TOKEN={long_token}\n")
                f.write(f"META_PAGE_ID={fb_page_id}\n")
                if ig_user_id:
                    f.write(f"META_IG_USER_ID={ig_user_id}\n")
            print("✅ Configuration saved to config.env")
        except Exception as e:
            print(f"❌ Failed to write to config.env: {e}")

if __name__ == "__main__":
    main()
