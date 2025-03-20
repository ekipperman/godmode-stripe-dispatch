import logging
from typing import Dict, Any, List, Optional
import tweepy
from linkedin_api import Linkedin
import facebook
import asyncio
from datetime import datetime
import aiohttp
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)

class SocialMediaPosting:
    def __init__(self, config: Dict[str, Any]):
        """Initialize social media posting with configuration"""
        self.config = config
        self.social_config = config["plugins"]["social_media"]
        
        # Initialize Twitter client
        if self.social_config["twitter"]["enabled"]:
            auth = tweepy.OAuthHandler(
                self.social_config["twitter"]["api_key"],
                self.social_config["twitter"]["api_secret"]
            )
            auth.set_access_token(
                self.social_config["twitter"]["access_token"],
                self.social_config["twitter"]["access_token_secret"]
            )
            self.twitter_client = tweepy.API(auth)
            
        # Initialize LinkedIn client
        if self.social_config["linkedin"]["enabled"]:
            self.linkedin_client = Linkedin(
                access_token=self.social_config["linkedin"]["access_token"]
            )
            
        # Initialize Facebook client
        if self.social_config["facebook"]["enabled"]:
            self.facebook_client = facebook.GraphAPI(
                access_token=self.social_config["facebook"]["access_token"],
                version="3.1"
            )
            self.facebook_page_id = self.social_config["facebook"]["page_id"]
        
        # Initialize post history
        self.post_history: List[Dict[str, Any]] = []
        
        logger.info("Social Media Posting initialized successfully")

    async def post_to_all(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to all enabled social media platforms"""
        try:
            posting_tasks = []
            platforms_results = {}
            
            # Prepare content for each platform
            content = post_data["content"]
            media_urls = post_data.get("media_urls", [])
            
            # Download media files if provided
            media_files = []
            if media_urls:
                media_files = await self._download_media_files(media_urls)
            
            # Create posting tasks for enabled platforms
            if self.social_config["twitter"]["enabled"]:
                posting_tasks.append(self._post_to_twitter(content, media_files))
            if self.social_config["linkedin"]["enabled"]:
                posting_tasks.append(self._post_to_linkedin(content, media_files))
            if self.social_config["facebook"]["enabled"]:
                posting_tasks.append(self._post_to_facebook(content, media_files))
            
            # Execute all posting tasks concurrently
            results = await asyncio.gather(*posting_tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, dict):
                    platforms_results[result["platform"]] = result
                else:
                    logger.error(f"Error posting to platform: {str(result)}")
            
            # Clean up downloaded media files
            await self._cleanup_media_files(media_files)
            
            # Record post in history
            self._record_post(content, platforms_results)
            
            return {
                "success": True,
                "platforms": platforms_results
            }
            
        except Exception as e:
            logger.error(f"Error posting to social media: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _download_media_files(self, urls: List[str]) -> List[str]:
        """Download media files from URLs"""
        media_files = []
        try:
            async with aiohttp.ClientSession() as session:
                for url in urls:
                    try:
                        # Create temporary file
                        temp_file = tempfile.NamedTemporaryFile(delete=False)
                        
                        # Download file
                        async with session.get(url) as response:
                            if response.status == 200:
                                content = await response.read()
                                temp_file.write(content)
                                temp_file.close()
                                media_files.append(temp_file.name)
                            else:
                                logger.error(f"Error downloading media from {url}: {response.status}")
                                
                    except Exception as e:
                        logger.error(f"Error downloading media from {url}: {str(e)}")
                        
            return media_files
            
        except Exception as e:
            logger.error(f"Error in media download: {str(e)}")
            return []

    async def _cleanup_media_files(self, file_paths: List[str]) -> None:
        """Clean up downloaded media files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"Error cleaning up media file {file_path}: {str(e)}")

    async def _post_to_twitter(self, content: str, media_files: List[str]) -> Dict[str, Any]:
        """Post content to Twitter"""
        try:
            media_ids = []
            
            # Upload media files if any
            for media_file in media_files:
                media = self.twitter_client.media_upload(media_file)
                media_ids.append(media.media_id)
            
            # Post tweet
            tweet = self.twitter_client.update_status(
                status=content[:280],  # Twitter's character limit
                media_ids=media_ids if media_ids else None
            )
            
            return {
                "success": True,
                "platform": "twitter",
                "post_id": tweet.id_str,
                "url": f"https://twitter.com/i/web/status/{tweet.id_str}"
            }
            
        except Exception as e:
            logger.error(f"Error posting to Twitter: {str(e)}")
            return {
                "success": False,
                "platform": "twitter",
                "error": str(e)
            }

    async def _post_to_linkedin(self, content: str, media_files: List[str]) -> Dict[str, Any]:
        """Post content to LinkedIn"""
        try:
            # Prepare post data
            post_data = {
                "author": "urn:li:person:me",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Add media if provided
            if media_files:
                media_assets = []
                for media_file in media_files:
                    asset = await self._upload_media_to_linkedin(media_file)
                    if asset:
                        media_assets.append(asset)
                
                if media_assets:
                    post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                    post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = media_assets
            
            # Create post
            post = self.linkedin_client.posts.create(post_data)
            
            return {
                "success": True,
                "platform": "linkedin",
                "post_id": post["id"]
            }
            
        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {str(e)}")
            return {
                "success": False,
                "platform": "linkedin",
                "error": str(e)
            }

    async def _post_to_facebook(self, content: str, media_files: List[str]) -> Dict[str, Any]:
        """Post content to Facebook"""
        try:
            post_args = {
                "message": content
            }
            
            # Add media if provided
            if media_files:
                if len(media_files) == 1:
                    # Single photo
                    with open(media_files[0], "rb") as photo:
                        post = self.facebook_client.put_photo(
                            image=photo.read(),
                            message=content,
                            album_path=f"{self.facebook_page_id}/photos"
                        )
                else:
                    # Multiple photos
                    media_ids = []
                    for media_file in media_files:
                        with open(media_file, "rb") as photo:
                            result = self.facebook_client.put_photo(
                                image=photo.read(),
                                album_path=f"{self.facebook_page_id}/photos",
                                published=False
                            )
                            media_ids.append({"media_fbid": result["id"]})
                    
                    post_args["attached_media"] = media_ids
                    post = self.facebook_client.put_object(
                        parent_object=self.facebook_page_id,
                        connection_name="feed",
                        **post_args
                    )
            else:
                # Text-only post
                post = self.facebook_client.put_object(
                    parent_object=self.facebook_page_id,
                    connection_name="feed",
                    **post_args
                )
            
            return {
                "success": True,
                "platform": "facebook",
                "post_id": post["id"],
                "url": f"https://facebook.com/{post['id']}"
            }
            
        except Exception as e:
            logger.error(f"Error posting to Facebook: {str(e)}")
            return {
                "success": False,
                "platform": "facebook",
                "error": str(e)
            }

    async def _upload_media_to_linkedin(self, media_file: str) -> Optional[Dict[str, Any]]:
        """Upload media to LinkedIn"""
        try:
            # Register media upload
            register_upload = self.linkedin_client.media.register_upload({
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": "urn:li:person:me",
                    "serviceRelationships": [{
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }]
                }
            })
            
            # Upload media binary
            with open(media_file, "rb") as f:
                self.linkedin_client.media.upload_media_binary(
                    register_upload["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"],
                    f.read()
                )
            
            return {
                "status": "READY",
                "asset": register_upload["value"]["asset"]
            }
            
        except Exception as e:
            logger.error(f"Error uploading media to LinkedIn: {str(e)}")
            return None

    def _record_post(self, content: str, results: Dict[str, Any]) -> None:
        """Record post in history"""
        self.post_history.append({
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "results": results
        })

    async def get_analytics(self) -> Dict[str, Any]:
        """Get posting analytics"""
        return {
            "total_posts": len(self.post_history),
            "platforms": {
                "twitter": {
                    "enabled": self.social_config["twitter"]["enabled"],
                    "posts": sum(1 for post in self.post_history 
                               if "twitter" in post["results"] and post["results"]["twitter"]["success"])
                },
                "linkedin": {
                    "enabled": self.social_config["linkedin"]["enabled"],
                    "posts": sum(1 for post in self.post_history 
                               if "linkedin" in post["results"] and post["results"]["linkedin"]["success"])
                },
                "facebook": {
                    "enabled": self.social_config["facebook"]["enabled"],
                    "posts": sum(1 for post in self.post_history 
                               if "facebook" in post["results"] and post["results"]["facebook"]["success"])
                }
            },
            "recent_posts": self.post_history[-5:]  # Last 5 posts
        }

    async def get_post_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get post history with optional limit"""
        if limit:
            return self.post_history[-limit:]
        return self.post_history
