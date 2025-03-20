import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import tweepy
from linkedin_api import Linkedin
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page

logger = logging.getLogger(__name__)

class SocialMediaAutomation:
    def __init__(self, config: Dict[str, Any]):
        """Initialize social media automation with configuration"""
        self.config = config
        self.social_config = config["plugins"]["social_media"]
        
        # Initialize social media clients
        self._init_linkedin()
        self._init_twitter()
        self._init_facebook()
        
        logger.info("Social Media Automation initialized successfully")

    def _init_linkedin(self):
        """Initialize LinkedIn API client"""
        if self.social_config["linkedin"]["enabled"]:
            try:
                self.linkedin = Linkedin()
                self.linkedin.authenticate(
                    access_token=self.social_config["linkedin"]["access_token"]
                )
                logger.info("LinkedIn client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing LinkedIn client: {str(e)}")
                self.linkedin = None

    def _init_twitter(self):
        """Initialize Twitter API client"""
        if self.social_config["twitter"]["enabled"]:
            try:
                auth = tweepy.OAuthHandler(
                    self.social_config["twitter"]["api_key"],
                    self.social_config["twitter"]["api_secret"]
                )
                auth.set_access_token(
                    self.social_config["twitter"]["access_token"],
                    self.social_config["twitter"]["access_token_secret"]
                )
                self.twitter = tweepy.API(auth)
                logger.info("Twitter client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Twitter client: {str(e)}")
                self.twitter = None

    def _init_facebook(self):
        """Initialize Facebook API client"""
        if self.social_config["facebook"]["enabled"]:
            try:
                FacebookAdsApi.init(access_token=self.social_config["facebook"]["access_token"])
                self.facebook_page = Page(self.social_config["facebook"]["page_id"])
                logger.info("Facebook client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Facebook client: {str(e)}")
                self.facebook_page = None

    async def post_to_all(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to all enabled social media platforms"""
        results = {
            "linkedin": None,
            "twitter": None,
            "facebook": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Post to LinkedIn
            if self.social_config["linkedin"]["enabled"] and self.linkedin:
                results["linkedin"] = await self.post_to_linkedin(content)
            
            # Post to Twitter
            if self.social_config["twitter"]["enabled"] and self.twitter:
                results["twitter"] = await self.post_to_twitter(content)
            
            # Post to Facebook
            if self.social_config["facebook"]["enabled"] and self.facebook_page:
                results["facebook"] = await self.post_to_facebook(content)
            
            return results
            
        except Exception as e:
            logger.error(f"Error posting to social media: {str(e)}")
            raise

    async def post_to_linkedin(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to LinkedIn"""
        try:
            # Prepare post content
            post_data = {
                "author": "urn:li:person:" + self.social_config["linkedin"]["profile_id"],
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content["text"]
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Add media if provided
            if content.get("media"):
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {"status": "READY", "originalUrl": media_url}
                    for media_url in content["media"]
                ]
            
            # Post to LinkedIn
            response = self.linkedin.make_post(post_data)
            
            return {
                "status": "success",
                "post_id": response["id"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def post_to_twitter(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Twitter"""
        try:
            # Post text content
            if len(content["text"]) > 280:
                # Split into thread if content exceeds Twitter's character limit
                tweets = self._split_into_thread(content["text"])
                previous_tweet_id = None
                tweet_ids = []
                
                for tweet_text in tweets:
                    tweet = self.twitter.update_status(
                        status=tweet_text,
                        in_reply_to_status_id=previous_tweet_id
                    )
                    tweet_ids.append(tweet.id)
                    previous_tweet_id = tweet.id
                
                result = {
                    "status": "success",
                    "tweet_ids": tweet_ids,
                    "is_thread": True
                }
            else:
                # Single tweet
                tweet = self.twitter.update_status(status=content["text"])
                result = {
                    "status": "success",
                    "tweet_id": tweet.id,
                    "is_thread": False
                }
            
            # Add media if provided
            if content.get("media"):
                media_ids = []
                for media_url in content["media"]:
                    media = self.twitter.media_upload(media_url)
                    media_ids.append(media.media_id)
                
                # Update tweet with media
                self.twitter.update_status(
                    status=content["text"],
                    media_ids=media_ids
                )
                result["media_ids"] = media_ids
            
            result["timestamp"] = datetime.now().isoformat()
            return result
            
        except Exception as e:
            logger.error(f"Error posting to Twitter: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def post_to_facebook(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Facebook"""
        try:
            post_data = {
                "message": content["text"]
            }
            
            # Add media if provided
            if content.get("media"):
                post_data["attachments"] = [
                    {"url": media_url} for media_url in content["media"]
                ]
            
            # Post to Facebook
            response = self.facebook_page.create_feed_post(
                fields=[],
                params=post_data
            )
            
            return {
                "status": "success",
                "post_id": response["id"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error posting to Facebook: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _split_into_thread(self, text: str, max_length: int = 280) -> List[str]:
        """Split long text into a thread of tweets"""
        words = text.split()
        tweets = []
        current_tweet = ""
        
        for word in words:
            if len(current_tweet) + len(word) + 1 <= max_length:
                current_tweet += " " + word if current_tweet else word
            else:
                tweets.append(current_tweet)
                current_tweet = word
        
        if current_tweet:
            tweets.append(current_tweet)
        
        # Add thread numbering
        return [f"({i+1}/{len(tweets)}) {tweet}" for i, tweet in enumerate(tweets)]

    async def get_analytics(self) -> Dict[str, Any]:
        """Get analytics from all social media platforms"""
        analytics = {
            "linkedin": None,
            "twitter": None,
            "facebook": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Get LinkedIn analytics
            if self.social_config["linkedin"]["enabled"] and self.linkedin:
                analytics["linkedin"] = await self._get_linkedin_analytics()
            
            # Get Twitter analytics
            if self.social_config["twitter"]["enabled"] and self.twitter:
                analytics["twitter"] = await self._get_twitter_analytics()
            
            # Get Facebook analytics
            if self.social_config["facebook"]["enabled"] and self.facebook_page:
                analytics["facebook"] = await self._get_facebook_analytics()
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting social media analytics: {str(e)}")
            raise

    async def _get_linkedin_analytics(self) -> Dict[str, Any]:
        """Get LinkedIn post analytics"""
        try:
            # Get recent posts
            posts = self.linkedin.get_profile_posts()
            
            # Get engagement metrics
            metrics = {
                "total_posts": len(posts),
                "total_likes": sum(post.get("numLikes", 0) for post in posts),
                "total_comments": sum(post.get("numComments", 0) for post in posts),
                "total_shares": sum(post.get("numShares", 0) for post in posts)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting LinkedIn analytics: {str(e)}")
            raise

    async def _get_twitter_analytics(self) -> Dict[str, Any]:
        """Get Twitter analytics"""
        try:
            # Get user timeline
            tweets = self.twitter.user_timeline(count=100)
            
            # Get engagement metrics
            metrics = {
                "total_tweets": len(tweets),
                "total_likes": sum(tweet.favorite_count for tweet in tweets),
                "total_retweets": sum(tweet.retweet_count for tweet in tweets),
                "total_replies": sum(1 for tweet in tweets if tweet.in_reply_to_status_id is not None)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting Twitter analytics: {str(e)}")
            raise

    async def _get_facebook_analytics(self) -> Dict[str, Any]:
        """Get Facebook Page analytics"""
        try:
            # Get page insights
            insights = self.facebook_page.get_insights(
                fields=[
                    'page_impressions',
                    'page_engaged_users',
                    'page_posts_impressions'
                ]
            )
            
            metrics = {
                "impressions": insights[0]["values"][0]["value"],
                "engaged_users": insights[1]["values"][0]["value"],
                "post_impressions": insights[2]["values"][0]["value"]
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting Facebook analytics: {str(e)}")
            raise
