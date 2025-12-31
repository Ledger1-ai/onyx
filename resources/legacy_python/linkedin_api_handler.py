import requests
import json
import logging
import os
from datetime import datetime
from typing import Dict, Optional, List, Any

# Configure logging
logger = logging.getLogger(__name__)

class LinkedInAPIHandler:
    """
    Handler for LinkedIn Marketing API v2.
    Focuses on Company Page interactions (The Utility Company).
    """

    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.person_urn = os.getenv("LINKEDIN_PERSON_URN") # urn:li:person:12345
        self.organization_urn = os.getenv("LINKEDIN_ORG_URN") # urn:li:organization:123456
        self.base_url = "https://api.linkedin.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def validate_auth(self) -> bool:
        """Check if we have valid credentials"""
        if not self.access_token or not self.organization_urn:
            logger.warning("LinkedIn credentials missing (ACCESS_TOKEN or ORG_URN).")
            return False
        
        # Test call - Try OIDC /userinfo first (modern), fall back to /me (legacy)
        try:
            # Try OIDC endpoint first
            response = requests.get(f"{self.base_url}/userinfo", headers=self.headers)
            if response.status_code == 200:
                logger.info("LinkedIn API connection successful (OIDC).")
                return True
            
            # Fallback to legacy
            response = requests.get(f"{self.base_url}/me", headers=self.headers)
            if response.status_code == 200:
                logger.info("LinkedIn API connection successful (Legacy).")
                return True
            else:
                logger.error(f"LinkedIn API Auth Check Failed: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"LinkedIn Connection Error: {e}")
            return False

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        Uploads an image to LinkedIn and returns the asset URN.
        Process: Initialize -> Upload -> Verify.
        """
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return None

        # 1. Initialize Upload
        init_url = f"{self.base_url}/assets?action=registerUpload"
        init_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": self.organization_urn,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        }
        
        try:
            res = requests.post(init_url, headers=self.headers, json=init_data)
            if res.status_code != 200:
                logger.error(f"LinkedIn Image Init Failed: {res.text}")
                return None
            
            data = res.json()
            upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset_urn = data['value']['asset']
            
            # 2. Upload Bytes
            with open(image_path, "rb") as f:
                upload_res = requests.put(upload_url, headers={"Authorization": f"Bearer {self.access_token}"}, data=f)
                
            if upload_res.status_code != 201:
                logger.error(f"LinkedIn Image Put Failed: {upload_res.status_code}")
                return None
                
            logger.info(f"LinkedIn Image Uploaded: {asset_urn}")
            return asset_urn
            
        except Exception as e:
            logger.error(f"LinkedIn Upload Exception: {e}")
            return None

    def post_commentary(self, text: str, media_path: Optional[str] = None) -> Optional[str]:
        """
        Post a text update (commentary) to the Company Page.
        Supports optional image attachment.
        """
        if not self.validate_auth():
            logger.error("Cannot post to LinkedIn: Invalid Auth")
            return None

        post_data: Dict[str, Any] = {
            "author": self.organization_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # Handle Media
        if media_path:
            asset_urn = self.upload_image(media_path)
            if asset_urn:
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                    "status": "READY",
                    "description": {"text": "Anubis Generated Content"},
                    "media": asset_urn,
                    "title": {"text": "Official Update"}
                }]

        # Send Request
        try:
            url = f"{self.base_url}/ugcPosts"
            response = requests.post(url, headers=self.headers, json=post_data)
            
            if response.status_code == 201:
                post_id = response.json().get("id")
                logger.info(f"LinkedIn Post Successful: {post_id}")
                return post_id
            else:
                logger.error(f"LinkedIn Post Failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"LinkedIn Post Exception: {e}")
            return None
