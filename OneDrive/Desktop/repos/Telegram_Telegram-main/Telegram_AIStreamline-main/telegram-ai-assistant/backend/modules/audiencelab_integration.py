import logging
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime
import json
from sentry_config import capture_exception

logger = logging.getLogger(__name__)

class AudienceLabIntegration:
    def __init__(self, config: Dict[str, Any]):
        """Initialize AudienceLab integration"""
        self.config = config
        self.audiencelab_config = config["plugins"]["audiencelab_integration"]
        self.api_key = self.audiencelab_config["api_key"]
        self.workspace_id = self.audiencelab_config["workspace_id"]
        self.base_url = "https://api.audiencelab.io/v1"
        self.superpixel_id = self.audiencelab_config["superpixel_id"]
        
        # Initialize tracking history
        self.tracking_history: List[Dict[str, Any]] = []
        
        logger.info("AudienceLab Integration initialized")

    async def identify_visitor(self, visitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify and enrich visitor data using SuperPixel"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "workspace_id": self.workspace_id,
                    "superpixel_id": self.superpixel_id,
                    "visitor": {
                        "anonymous_id": visitor_data.get("anonymous_id"),
                        "ip_address": visitor_data.get("ip_address"),
                        "user_agent": visitor_data.get("user_agent"),
                        "referrer": visitor_data.get("referrer"),
                        "page_url": visitor_data.get("page_url"),
                        "custom_data": visitor_data.get("custom_data", {})
                    }
                }

                url = f"{self.base_url}/identify"
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    
                    # Record identification
                    self._record_tracking("identify", visitor_data.get("anonymous_id"), result)
                    
                    return {
                        "success": response.status == 200,
                        "visitor_id": result.get("visitor_id"),
                        "enriched_data": result.get("enriched_data")
                    }

        except Exception as e:
            logger.error(f"Error identifying visitor: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def create_segment(self, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create dynamic audience segment"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "workspace_id": self.workspace_id,
                    "segment": {
                        "name": segment_data["name"],
                        "description": segment_data.get("description"),
                        "rules": segment_data["rules"],
                        "dynamic": True,
                        "update_frequency": segment_data.get("update_frequency", "realtime")
                    }
                }

                url = f"{self.base_url}/segments"
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "segment_id": result.get("id"),
                        "audience_size": result.get("audience_size")
                    }

        except Exception as e:
            logger.error(f"Error creating segment: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def track_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track visitor event"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "workspace_id": self.workspace_id,
                    "superpixel_id": self.superpixel_id,
                    "event": {
                        "visitor_id": event_data["visitor_id"],
                        "event_name": event_data["event_name"],
                        "properties": event_data.get("properties", {}),
                        "timestamp": event_data.get("timestamp", datetime.now().isoformat())
                    }
                }

                url = f"{self.base_url}/events"
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    
                    # Record event
                    self._record_tracking("event", event_data["visitor_id"], result)
                    
                    return {
                        "success": response.status == 200,
                        "event_id": result.get("id")
                    }

        except Exception as e:
            logger.error(f"Error tracking event: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def match_profiles(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Match visitor profiles with existing data"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "workspace_id": self.workspace_id,
                    "match": {
                        "visitor_id": match_data["visitor_id"],
                        "identifiers": match_data["identifiers"],
                        "confidence_threshold": match_data.get("confidence_threshold", 0.8)
                    }
                }

                url = f"{self.base_url}/match"
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "matches": result.get("matches", []),
                        "confidence_scores": result.get("confidence_scores", {})
                    }

        except Exception as e:
            logger.error(f"Error matching profiles: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_segment_members(self, segment_id: str) -> Dict[str, Any]:
        """Get members of a segment"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                url = f"{self.base_url}/segments/{segment_id}/members"
                async with session.get(url, headers=headers) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "members": result.get("members", []),
                        "total_count": result.get("total_count", 0)
                    }

        except Exception as e:
            logger.error(f"Error getting segment members: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_visitor_profile(self, visitor_id: str) -> Dict[str, Any]:
        """Get enriched visitor profile"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                url = f"{self.base_url}/visitors/{visitor_id}/profile"
                async with session.get(url, headers=headers) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "profile": result
                    }

        except Exception as e:
            logger.error(f"Error getting visitor profile: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    def _record_tracking(self, action_type: str, identifier: str, result: Dict[str, Any]) -> None:
        """Record tracking action in history"""
        self.tracking_history.append({
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "identifier": identifier,
            "result": result
        })

    async def get_tracking_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get tracking history with optional limit"""
        history = self.tracking_history
        if limit:
            history = history[-limit:]
        return history

    async def get_superpixel_status(self) -> Dict[str, Any]:
        """Get SuperPixel status and statistics"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                url = f"{self.base_url}/superpixels/{self.superpixel_id}/status"
                async with session.get(url, headers=headers) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "status": result.get("status"),
                        "stats": result.get("stats", {})
                    }

        except Exception as e:
            logger.error(f"Error getting SuperPixel status: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }
