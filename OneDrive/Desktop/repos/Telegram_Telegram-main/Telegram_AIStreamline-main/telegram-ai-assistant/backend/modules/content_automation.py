import logging
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime
import json
from pathlib import Path
from sentry_config import capture_exception
from .ai_chatbot import AIChatbot
from .social_media_posting import SocialMediaPosting
from .email_sms_automation import EmailSMSAutomation

logger = logging.getLogger(__name__)

class ContentAutomation:
    def __init__(self, config: Dict[str, Any]):
        """Initialize content automation"""
        self.config = config
        self.ai_chatbot = AIChatbot(config)
        self.social_media = SocialMediaPosting(config)
        self.email_automation = EmailSMSAutomation(config)
        
        # Initialize content tracking
        self.content_tracking: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Content Automation initialized")

    async def generate_website_content(self, website_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate website content using AI"""
        try:
            content = {}
            
            # Generate main sections
            sections = [
                "hero",
                "features",
                "about",
                "services",
                "testimonials",
                "contact"
            ]
            
            for section in sections:
                prompt = self._get_section_prompt(section, website_data)
                response = await self.ai_chatbot.generate_content(prompt)
                
                content[section] = {
                    "title": response["title"],
                    "description": response["description"],
                    "cta": response.get("cta"),
                    "generated_at": datetime.now().isoformat()
                }
            
            # Track content generation
            content_id = f"website_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.content_tracking[content_id] = {
                "type": "website",
                "status": "generated",
                "sections": sections,
                "metadata": website_data,
                "generated_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "content_id": content_id,
                "content": content
            }

        except Exception as e:
            logger.error(f"Error generating website content: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_video_script(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate video script using AI"""
        try:
            # Generate script outline
            outline_prompt = self._get_video_outline_prompt(video_data)
            outline = await self.ai_chatbot.generate_content(outline_prompt)
            
            # Generate full script
            script_prompt = self._get_video_script_prompt(video_data, outline)
            script = await self.ai_chatbot.generate_content(script_prompt)
            
            # Track content generation
            content_id = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.content_tracking[content_id] = {
                "type": "video",
                "status": "generated",
                "metadata": video_data,
                "generated_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "content_id": content_id,
                "content": {
                    "outline": outline,
                    "script": script,
                    "duration_estimate": self._estimate_video_duration(script)
                }
            }

        except Exception as e:
            logger.error(f"Error generating video script: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_podcast_content(self, podcast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate podcast content using AI"""
        try:
            # Generate episode outline
            outline_prompt = self._get_podcast_outline_prompt(podcast_data)
            outline = await self.ai_chatbot.generate_content(outline_prompt)
            
            # Generate talking points
            points_prompt = self._get_podcast_points_prompt(podcast_data, outline)
            talking_points = await self.ai_chatbot.generate_content(points_prompt)
            
            # Generate script
            script_prompt = self._get_podcast_script_prompt(podcast_data, outline, talking_points)
            script = await self.ai_chatbot.generate_content(script_prompt)
            
            # Track content generation
            content_id = f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.content_tracking[content_id] = {
                "type": "podcast",
                "status": "generated",
                "metadata": podcast_data,
                "generated_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "content_id": content_id,
                "content": {
                    "outline": outline,
                    "talking_points": talking_points,
                    "script": script,
                    "duration_estimate": self._estimate_podcast_duration(script)
                }
            }

        except Exception as e:
            logger.error(f"Error generating podcast content: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_blog_post(self, blog_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate blog post using AI"""
        try:
            # Generate outline
            outline_prompt = self._get_blog_outline_prompt(blog_data)
            outline = await self.ai_chatbot.generate_content(outline_prompt)
            
            # Generate sections
            sections = []
            for section in outline["sections"]:
                section_prompt = self._get_blog_section_prompt(blog_data, section)
                section_content = await self.ai_chatbot.generate_content(section_prompt)
                sections.append({
                    "title": section["title"],
                    "content": section_content,
                    "keywords": section.get("keywords", [])
                })
            
            # Generate meta description and tags
            meta_prompt = self._get_blog_meta_prompt(blog_data, sections)
            meta = await self.ai_chatbot.generate_content(meta_prompt)
            
            # Track content generation
            content_id = f"blog_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.content_tracking[content_id] = {
                "type": "blog",
                "status": "generated",
                "metadata": blog_data,
                "generated_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "content_id": content_id,
                "content": {
                    "title": blog_data["title"],
                    "meta_description": meta["description"],
                    "tags": meta["tags"],
                    "sections": sections,
                    "estimated_read_time": self._estimate_read_time(sections)
                }
            }

        except Exception as e:
            logger.error(f"Error generating blog post: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_social_media_content(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate social media content using AI"""
        try:
            content = {}
            platforms = social_data.get("platforms", ["twitter", "linkedin", "facebook"])
            
            for platform in platforms:
                # Generate post variations
                post_prompt = self._get_social_post_prompt(platform, social_data)
                posts = await self.ai_chatbot.generate_content(post_prompt)
                
                # Generate hashtags
                hashtag_prompt = self._get_hashtag_prompt(platform, social_data)
                hashtags = await self.ai_chatbot.generate_content(hashtag_prompt)
                
                content[platform] = {
                    "posts": posts,
                    "hashtags": hashtags,
                    "generated_at": datetime.now().isoformat()
                }
            
            # Track content generation
            content_id = f"social_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.content_tracking[content_id] = {
                "type": "social",
                "status": "generated",
                "platforms": platforms,
                "metadata": social_data,
                "generated_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "content_id": content_id,
                "content": content
            }

        except Exception as e:
            logger.error(f"Error generating social media content: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_email_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email campaign content using AI"""
        try:
            content = {}
            
            # Generate subject lines
            subject_prompt = self._get_email_subject_prompt(campaign_data)
            subject_lines = await self.ai_chatbot.generate_content(subject_prompt)
            
            # Generate email body
            body_prompt = self._get_email_body_prompt(campaign_data)
            body = await self.ai_chatbot.generate_content(body_prompt)
            
            # Generate CTAs
            cta_prompt = self._get_email_cta_prompt(campaign_data)
            ctas = await self.ai_chatbot.generate_content(cta_prompt)
            
            content = {
                "subject_lines": subject_lines,
                "body": body,
                "ctas": ctas,
                "preview_text": body["preview"],
                "generated_at": datetime.now().isoformat()
            }
            
            # Track content generation
            content_id = f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.content_tracking[content_id] = {
                "type": "email",
                "status": "generated",
                "metadata": campaign_data,
                "generated_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "content_id": content_id,
                "content": content
            }

        except Exception as e:
            logger.error(f"Error generating email campaign: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    def _get_section_prompt(self, section: str, data: Dict[str, Any]) -> str:
        """Get prompt for website section"""
        prompts = {
            "hero": f"Create a compelling hero section for {data['business_name']} that highlights {data['value_proposition']}",
            "features": f"List the key features of {data['business_name']}'s {data['product_type']}",
            "about": f"Write an engaging about section for {data['business_name']} focusing on {data['mission']}",
            "services": f"Describe the services offered by {data['business_name']} in detail",
            "testimonials": "Generate placeholder testimonials based on the value proposition",
            "contact": f"Create a contact section for {data['business_name']}"
        }
        return prompts.get(section, "")

    def _get_video_outline_prompt(self, data: Dict[str, Any]) -> str:
        """Get prompt for video outline"""
        return f"Create a video outline for {data['title']} that explains {data['main_points']}"

    def _get_video_script_prompt(self, data: Dict[str, Any], outline: Dict[str, Any]) -> str:
        """Get prompt for video script"""
        return f"Write a video script based on the outline for {data['title']}"

    def _get_podcast_outline_prompt(self, data: Dict[str, Any]) -> str:
        """Get prompt for podcast outline"""
        return f"Create a podcast episode outline for {data['title']} covering {data['topics']}"

    def _get_podcast_points_prompt(self, data: Dict[str, Any], outline: Dict[str, Any]) -> str:
        """Get prompt for podcast talking points"""
        return f"Generate detailed talking points for the podcast episode {data['title']}"

    def _get_podcast_script_prompt(self, data: Dict[str, Any], outline: Dict[str, Any],
                                 points: Dict[str, Any]) -> str:
        """Get prompt for podcast script"""
        return f"Write a podcast script for {data['title']} based on the outline and talking points"

    def _get_blog_outline_prompt(self, data: Dict[str, Any]) -> str:
        """Get prompt for blog outline"""
        return f"Create an outline for a blog post about {data['topic']} targeting {data['audience']}"

    def _get_blog_section_prompt(self, data: Dict[str, Any], section: Dict[str, Any]) -> str:
        """Get prompt for blog section"""
        return f"Write content for the blog section '{section['title']}' about {data['topic']}"

    def _get_blog_meta_prompt(self, data: Dict[str, Any], sections: List[Dict[str, Any]]) -> str:
        """Get prompt for blog meta content"""
        return f"Generate SEO meta description and tags for blog post about {data['topic']}"

    def _get_social_post_prompt(self, platform: str, data: Dict[str, Any]) -> str:
        """Get prompt for social media post"""
        return f"Write {platform} posts about {data['topic']} for {data['audience']}"

    def _get_hashtag_prompt(self, platform: str, data: Dict[str, Any]) -> str:
        """Get prompt for social media hashtags"""
        return f"Generate relevant hashtags for {platform} posts about {data['topic']}"

    def _get_email_subject_prompt(self, data: Dict[str, Any]) -> str:
        """Get prompt for email subject lines"""
        return f"Write email subject lines for {data['campaign_type']} targeting {data['audience']}"

    def _get_email_body_prompt(self, data: Dict[str, Any]) -> str:
        """Get prompt for email body"""
        return f"Write email body content for {data['campaign_type']} campaign"

    def _get_email_cta_prompt(self, data: Dict[str, Any]) -> str:
        """Get prompt for email CTAs"""
        return f"Generate CTAs for {data['campaign_type']} email campaign"

    def _estimate_video_duration(self, script: Dict[str, Any]) -> int:
        """Estimate video duration in minutes"""
        # Assuming average speaking rate of 150 words per minute
        word_count = len(script["content"].split())
        return round(word_count / 150)

    def _estimate_podcast_duration(self, script: Dict[str, Any]) -> int:
        """Estimate podcast duration in minutes"""
        # Assuming average speaking rate of 130 words per minute
        word_count = len(script["content"].split())
        return round(word_count / 130)

    def _estimate_read_time(self, sections: List[Dict[str, Any]]) -> int:
        """Estimate blog post read time in minutes"""
        # Assuming average reading speed of 250 words per minute
        total_words = sum(len(section["content"].split()) for section in sections)
        return round(total_words / 250)
