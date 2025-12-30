
import requests
import urllib.parse
import webbrowser
import time
import os
import json

def get_auth_token():
    print("[INIT] LinkedIn API Credential Helper")
    print("=================================")
    print("This script will help you get your ACCESS TOKEN and URNs for the .env file.")
    print("\nYou need your Client ID and Client Secret from: https://www.linkedin.com/developers/apps")
    
    client_id = input("\nEnter Client ID: ").strip()
    client_secret = input("Enter Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("[ERROR] Client ID and Secret are required.")
        return

    redirect_uri = "http://localhost:8000/callback"
    print(f"\n[WARN]  Please ensure '{redirect_uri}' is added to your Redirect URLs in the Developer Portal app settings!")
    input("Press Enter once confirmed...")

    # 1. Authorization Code
    auth_base = "https://www.linkedin.com/oauth/v2/authorization"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email w_member_social", # Add w_organization_social if approved
    }
    auth_url = f"{auth_base}?{urllib.parse.urlencode(params)}"
    
    print(f"\n[NET] Opening browser to authorize...")
    print(f"URL: {auth_url}")
    webbrowser.open(auth_url)
    
    print("\n[INFO] After authorizing, you will be redirected to a 'localhost' URL that might fail to load.")
    print("Look at the URL bar in your browser. It looks like: http://localhost:8000/callback?code=THIS_IS_THE_CODE&state=...")
    auth_code = input("\nPaste the 'code' parameter value here: ").strip()
    
    if not auth_code:
        print("[ERROR] No code provided.")
        return

    # 2. Exchange for Access Token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    print("\n[NET] Exchanging code for Access Token...")
    res = requests.post(token_url, data=data)
    
    if res.status_code != 200:
        print(f"[ERROR] Failed to get token: {res.text}")
        return
        
    token_data = res.json()
    access_token = token_data.get("access_token")
    print(f"\n[SUCCESS] ACCESS TOKEN:\n{access_token}")
    
    # 3. Get User URN (Person URN)
    print("\n[INFO] Fetching User Profile (Person URN)...")
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    
    if me_res.status_code == 200:
        me_data = me_res.json()
        person_urn = f"urn:li:person:{me_data.get('sub')}"
        print(f"[SUCCESS] PERSON URN: {person_urn}")
        print(f"   Name: {me_data.get('name')}")
    else:
        print(f"[WARN]  Could not fetch profile: {me_res.text}")
        person_urn = "urn:li:person:UNKNOWN"

    # 4. Instructions for Org URN
    print("\n[INFO] Organization URN:")
    print("The API cannot easily list organizations you admin without complex permissions.")
    print("To find it manually:")
    print("1. Go to your LinkedIn Company Page as Admin.")
    print("2. Look at the URL: https://www.linkedin.com/company/1234567/admin/...")
    print("3. The number '1234567' is your ID.")
    print("4. Your URN is: urn:li:organization:1234567")

    # 5. Summary
    print("\n\n[INFO] CONFIGURATION SUMMARY (Copy to config.env)")
    print("============================================")
    print(f"LINKEDIN_ACCESS_TOKEN={access_token}")
    print(f"LINKEDIN_PERSON_URN={person_urn}")
    print("LINKEDIN_ORG_URN=urn:li:organization:INSERT_ID_HERE")
    print("============================================")
    
    # Optional: Save to file
    save = input("\nSave to .env? (y/n): ").lower()
    if save == 'y':
        # Simple append
        with open("config.env", "a") as f:
            f.write(f"\n# LinkedIn API credentials added via helper script\n")
            f.write(f"LINKEDIN_ACCESS_TOKEN={access_token}\n")
            f.write(f"LINKEDIN_PERSON_URN={person_urn}\n")
            f.write(f"# LINKEDIN_ORG_URN=urn:li:organization:CHECK_BROWSER_URL\n")
        print("✅ Appended to config.env (Org URN still needs manual entry)")

if __name__ == "__main__":
    get_auth_token()
