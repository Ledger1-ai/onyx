import requests
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class MetaAPIHandler:
    """
    Handler for Meta Graph API (Facebook & Instagram).
    Focus: Publishing content to Pages and IG Business Accounts.
    """

    def __init__(self, access_token: Optional[str] = None, page_id: Optional[str] = None, ig_user_id: Optional[str] = None):
        # Allow dynamic injection of credentials (for Multi-Tenant/SaaS)
        # Fallback to environment variables for Single-Tenant dev mode
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")
        self.page_id = page_id or os.getenv("META_PAGE_ID")  # Facebook Page ID
        self.ig_user_id = ig_user_id or os.getenv("META_IG_USER_ID") # Instagram Business Account ID
        self.base_url = "https://graph.facebook.com/v19.0"

    def validate_auth(self) -> bool:
        """Verify that the stored Access Token is valid by pinging /me"""
        if not self.access_token:
            return False
            
        try:
            url = f"{self.base_url}/me"
            params = {"access_token": self.access_token}
            res = requests.get(url, params=params)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Meta Auth Validation Failed: {e}")
            return False

    def post_facebook_text(self, message: str) -> Optional[str]:
        """Post text to Facebook Page"""
        if not self.page_id or not self.access_token:
            logger.error("Missing Meta credentials for Facebook posting.")
            return None
            
        url = f"{self.base_url}/{self.page_id}/feed"
        params = {
            "message": message,
            "access_token": self.access_token
        }
        
        try:
            res = requests.post(url, params=params)
            if res.status_code == 200:
                return res.json().get("id")
            else:
                logger.error(f"FB Post Failed: {res.text}")
                return None
        except Exception as e:
            logger.error(f"FB Post Exception: {e}")
            return None

    def post_instagram_media(self, image_url: str, caption: str) -> Optional[str]:
        """
        Post Image to Instagram.
        Steps: 1. Create Media Container, 2. Publish Container.
        """
        if not self.ig_user_id or not self.access_token:
            logger.error("Missing Meta credentials for Instagram posting.")
            return None

        # 1. Create Container
        container_url = f"{self.base_url}/{self.ig_user_id}/media"
        container_params = {
            "image_url": image_url, # Must be a public URL!
            "caption": caption,
            "access_token": self.access_token
        }
        
        try:
            # Step 1: Container
            res = requests.post(container_url, params=container_params)
            if res.status_code != 200:
                logger.error(f"IG Container Create Failed: {res.text}")
                return None
            
            container_id = res.json().get("id")
            
            # Step 2: Publish
            publish_url = f"{self.base_url}/{self.ig_user_id}/media_publish"
            publish_params = {
                "creation_id": container_id,
                "access_token": self.access_token
            }
            
            pub_res = requests.post(publish_url, params=publish_params)
            if pub_res.status_code == 200:
                logger.info(f"IG Post Successful: {pub_res.json().get('id')}")
                return pub_res.json().get("id")
            else:
                logger.error(f"IG Publish Failed: {pub_res.text}")
                return None
                
        except Exception as e:
            logger.error(f"IG Post Exception: {e}")
            return None

    def post_facebook_image(self, image_path: str, message: str) -> Optional[str]:
        """Post local image file to Facebook Page"""
        if not self.page_id or not self.access_token:
            logger.error("Missing Meta credentials")
            return None

        url = f"{self.base_url}/{self.page_id}/photos"
        params = {
            "message": message,
            "access_token": self.access_token
        }
        
        try:
            # Open file in binary mode
            with open(image_path, 'rb') as img_file:
                files = {'source': img_file}
                res = requests.post(url, params=params, files=files)
            
            if res.status_code == 200:
                return res.json().get("id")
            else:
                logger.error(f"FB Photo Upload Failed: {res.text}")
                return None
        except Exception as e:
            logger.error(f"FB Photo Exception: {e}")
            return None

    def post_facebook_video(self, video_path: str, description: str) -> Optional[str]:
        """Post local video file to Facebook Page (Simple upload < 1GB)"""
        # Note: Large videos require chunked upload. This is for short clips.
        if not self.page_id or not self.access_token:
            return None

        url = f"{self.base_url}/{self.page_id}/videos"
        params = {
            "description": description,
            "access_token": self.access_token
        }
        
        try:
             with open(video_path, 'rb') as vid_file:
                files = {'source': vid_file}
                res = requests.post(url, params=params, files=files)
                
             if res.status_code == 200:
                 return res.json().get("id")
             else:
                 logger.error(f"FB Video Upload Failed: {res.text}")
                 return None
        except Exception as e:
            logger.error(f"FB Video Exception: {e}")
            return None

    def post_instagram_video(self, video_url: str, caption: str) -> Optional[str]:
        """
        Post Video (Reel) to Instagram.
        Steps: 1. Create Container (media_type=REELS), 2. Wait (async), 3. Publish.
        Note: THIS REQUIRES A PUBLIC URL. Local upload not supported directly via this endpoint.
        """
        if not self.ig_user_id or not self.access_token:
            return None

        # 1. Create Container
        container_url = f"{self.base_url}/{self.ig_user_id}/media"
        container_params = {
            "video_url": video_url,
            "caption": caption,
            "media_type": "REELS",
            "access_token": self.access_token
        }
        
        try:
            res = requests.post(container_url, params=container_params)
            if res.status_code != 200:
                logger.error(f"IG Reel Container Failed: {res.text}")
                return None
            
            container_id = res.json().get("id")
            
            # NOTE: Video processing is async. We should ideally poll for status.
            # For simplicity in this v1, we assume short videos / fast APIs or just try publish.
            # Real production logic needs a loop checking ?fields=status_code
            
            import time
            time.sleep(10) # Naive wait for processing
            
            # 2. Publish
            publish_url = f"{self.base_url}/{self.ig_user_id}/media_publish"
            publish_params = {
                "creation_id": container_id,
                "access_token": self.access_token
            }
            
            pub_res = requests.post(publish_url, params=publish_params)
            if pub_res.status_code == 200:
                logger.info(f"IG Reel Published: {pub_res.json().get('id')}")
                return pub_res.json().get("id")
            else:
                logger.error(f"IG Reel Publish Failed (likely processing): {pub_res.text}")
                return None
                
        except Exception as e:
            logger.error(f"IG Reel Exception: {e}")
            return None

    # --- Engagement Methods (Safe API) ---

    def get_facebook_comments(self, post_id: str) -> list:
        """Fetch comments for a Facebook Post"""
        if not self.access_token: return []
        
        url = f"{self.base_url}/{post_id}/comments"
        params = {"access_token": self.access_token, "fields": "id,message,from,created_time,can_reply_privately"}
        
        try:
            res = requests.get(url, params=params)
            if res.status_code == 200:
                return res.json().get("data", [])
            return []
        except Exception:
            return []

    def reply_to_facebook_comment(self, comment_id: str, message: str) -> bool:
        """Reply to a Facebook Comment"""
        if not self.access_token: return False
        
        url = f"{self.base_url}/{comment_id}/comments"
        params = {"message": message, "access_token": self.access_token}
        
        try:
            res = requests.post(url, params=params)
            return res.status_code == 200
        except Exception:
            return False

    def get_instagram_comments(self, media_id: str) -> list:
        """Fetch comments for an Instagram Media Object"""
        if not self.access_token: return []
        
        url = f"{self.base_url}/{media_id}/comments"
        params = {"access_token": self.access_token, "fields": "id,text,from,username,timestamp"} # IG uses 'text' not 'message'
        
        try:
            res = requests.get(url, params=params)
            if res.status_code == 200:
                return res.json().get("data", [])
            return []
        except Exception:
            return []

    def reply_to_instagram_comment(self, comment_id: str, message: str) -> bool:
        """Reply to an Instagram Comment"""
        if not self.access_token: return False
        
        url = f"{self.base_url}/{comment_id}/replies"
        params = {"message": message, "access_token": self.access_token}
        
        try:
            res = requests.post(url, params=params)
            return res.status_code == 200
        except Exception:
            return False

    def get_facebook_insights(self) -> dict:
        """Fetch Facebook Page Insights"""
        if not self.page_id or not self.access_token:
            return {}
        
        # Metrics: page_impressions, page_post_engagements, page_fans (Total Likes), page_views_total
        url = f"{self.base_url}/{self.page_id}/insights"
        params = {
            "metric": "page_impressions,page_post_engagements,page_fans,page_views_total",
            "period": "day",
            "access_token": self.access_token
        }
        
        try:
            res = requests.get(url, params=params)
            data = res.json()
            if "data" in data:
                # Structure: [{"name": "page_impressions", "values": [{"value": 123, ...}]}, ...]
                results = {}
                for item in data["data"]:
                    # Get the most recent value
                    val = item["values"][-1]["value"] if item["values"] else 0
                    results[item["name"]] = val
                return results
            else:
                logger.warning(f"FB Insights Error: {data}")
                return {}
        except Exception as e:
            logger.error(f"FB Insights Exception: {e}")
            return {}

    def get_instagram_insights(self) -> dict:
        """Fetch Instagram Business Insights"""
        if not self.ig_user_id or not self.access_token:
            return {}
            
        # IG Graph API requires different endpoint structure for some user metrics
        # GET /{ig-user-id}?fields=followers_count,media_count
        # Insights: GET /{ig-user-id}/insights?metric=impressions,reach,profile_views&period=day
        
        results = {}
        
        try:
            # 1. Basic Account Info
            user_url = f"{self.base_url}/{self.ig_user_id}"
            user_params = {
                "fields": "followers_count,media_count",
                "access_token": self.access_token
            }
            user_res = requests.get(user_url, params=user_params)
            if user_res.status_code == 200:
                user_data = user_res.json()
                results["followers_count"] = user_data.get("followers_count", 0)
                results["media_count"] = user_data.get("media_count", 0)
            
            # 2. Insights (Requires >100 followers usually? Check limitations)
            # Default to day period
            insights_url = f"{self.base_url}/{self.ig_user_id}/insights"
            insights_params = {
                "metric": "impressions,reach,profile_views",
                "period": "day",
                "access_token": self.access_token
            }
            ins_res = requests.get(insights_url, params=insights_params)
            ins_data = ins_res.json()
            
            if "data" in ins_data:
                for item in ins_data["data"]:
                    val = item["values"][-1]["value"] if item["values"] else 0
                    results[item["name"]] = val
            
            return results
            
        except Exception as e:
            logger.error(f"IG Insights Exception: {e}")
            return results
