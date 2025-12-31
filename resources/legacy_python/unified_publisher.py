import logging
from typing import List, Optional
from config import logger
from twitter_api import TwitterAPI
from linkedin_api_handler import LinkedInAPIHandler
from meta_api_handler import MetaAPIHandler
from database_manager import DatabaseManager

class UnifiedPublisher:
    """
    Central controller for publishing content via Official APIs ('The Suit').
    Handles distribution to Twitter, LinkedIn, Facebook, and Instagram.
    Now Multi-Tenant/Database Aware.
    """
    
    def __init__(self, user_id: str = "admin"):
        self.user_id = user_id
        self.db_manager = DatabaseManager()
        self.user = self.db_manager.get_user(user_id)
        self.creds = self.user.get("credentials", {}) if self.user else {}

        # 1. Initialize Twitter API
        # TwitterAPI might need refactoring to accept tokens too, but for now we focus on Meta/LinkedIn
        # as requested ("Meta to API only")
        try:
            # TODO: Update TwitterAPI to accept tokens from DB if needed
            self.twitter = TwitterAPI() 
        except Exception as e:
            logger.warning(f"Failed to initialize TwitterAPI: {e}")
            self.twitter = None

        # 2. Initialize LinkedIn
        try:
            li_creds = self.creds.get("linkedin", {})
            if li_creds.get("is_active"):
                self.linkedin = LinkedInAPIHandler(
                    access_token=li_creds.get("access_token"),
                    person_urn=li_creds.get("platform_user_id")
                )
            else:
                self.linkedin = None
        except Exception as e:
            logger.warning(f"Failed to load LinkedIn handler: {e}")
            self.linkedin = None
            
        # 3. Initialize Meta (Facebook/Instagram)
        try:
            meta_creds = self.creds.get("facebook", {}) # FB and IG share the token usually
            if meta_creds.get("is_active"):
                self.meta = MetaAPIHandler(
                    access_token=meta_creds.get("access_token"),
                    page_id=None, # will need to fetch or store this too if it varies
                    ig_user_id=None
                )
            else:
                self.meta = None
        except Exception as e:
            logger.warning(f"Failed to load Meta handler: {e}")
            self.meta = None
            
        logger.info(f"UnifiedPublisher initialized for user {user_id}. Meta Active: {self.meta is not None}")

    async def publish(self, content: str, platforms: List[str] = ["twitter"], media_path: Optional[str] = None):
        """
        Publish content to specified platforms using official APIs.
        """
        results = {}
        
        # 1. Twitter
        if "twitter" in platforms and self.twitter:
            try:
                # TwitterAPI expects list of paths
                media_list = [media_path] if media_path else None
                res = self.twitter.post_tweet(content, media_paths=media_list)
                results["twitter"] = {"success": res is not None, "data": res}
            except Exception as e:
                logger.error(f"Twitter Publish Error: {e}")
                results["twitter"] = {"success": False, "error": str(e)}
        elif "twitter" in platforms:
             results["twitter"] = {"success": False, "error": "TwitterAPI not initialized or inactive"}

        # 2. LinkedIn
        if "linkedin" in platforms:
            if self.linkedin:
                try:
                    # LinkedIn handler takes single path
                    res = self.linkedin.post_commentary(content, media_path=media_path)
                    results["linkedin"] = {"success": res is not None, "id": res}
                except Exception as e:
                    logger.error(f"LinkedIn Publish Error: {e}")
                    results["linkedin"] = {"success": False, "error": str(e)}
            else:
                results["linkedin"] = {"success": False, "error": "LinkedIn not connected"}

        # 3. Facebook
        if "facebook" in platforms:
            if self.meta:
                try:
                    # FB Text Post
                    res = self.meta.post_facebook_text(content)
                    results["facebook"] = {"success": res is not None, "id": res}
                except Exception as e:
                    logger.error(f"Facebook Publish Error: {e}")
                    results["facebook"] = {"success": False, "error": str(e)}
            else:
                results["facebook"] = {"success": False, "error": "Facebook not connected"}

        # 4. Instagram
        if "instagram" in platforms:
            if self.meta:
                 try:
                    if media_path and media_path.startswith("http"):
                        res = self.meta.post_instagram_media(media_path, content)
                        results["instagram"] = {"success": res is not None, "id": res}
                    else:
                        logger.warning("Instagram requires a public URL for image upload. Local path provided.")
                        results["instagram"] = {"success": False, "error": "IG requires public URL"}
                 except Exception as e:
                    logger.error(f"Instagram Publish Error: {e}")
                    results["instagram"] = {"success": False, "error": str(e)}
            else:
                results["instagram"] = {"success": False, "error": "Instagram not connected"}
        
        return results
