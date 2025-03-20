import logging
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime
import json
from sentry_config import capture_exception

logger = logging.getLogger(__name__)

class BoostIntegration:
    def __init__(self, config: Dict[str, Any]):
        """Initialize Boost.space integration"""
        self.config = config
        self.boost_config = config["plugins"]["boost_integration"]
        self.api_key = self.boost_config["api_key"]
        self.workspace_id = self.boost_config["workspace_id"]
        self.base_url = "https://api.boost.space/v1"
        
        # Initialize sync history
        self.sync_history: List[Dict[str, Any]] = []
        
        # Initialize webhook handlers
        self.webhook_handlers: List[Dict[str, Any]] = []
        
        logger.info("Boost.space Integration initialized")

    async def sync_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync contact to Boost.space"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # Map contact data to Boost.space format
                boost_data = {
                    "workspace_id": self.workspace_id,
                    "contact": {
                        "email": contact_data["email"],
                        "phone": contact_data.get("phone"),
                        "first_name": contact_data.get("first_name"),
                        "last_name": contact_data.get("last_name"),
                        "source": "telegram_assistant",
                        "tags": contact_data.get("tags", []),
                        "custom_fields": contact_data.get("custom_fields", {})
                    }
                }

                url = f"{self.base_url}/contacts"
                async with session.post(url, headers=headers, json=boost_data) as response:
                    result = await response.json()
                    
                    # Record sync
                    self._record_sync("contact", contact_data["email"], result)
                    
                    return {
                        "success": response.status == 200,
                        "contact_id": result.get("id"),
                        "boost_data": result
                    }

        except Exception as e:
            logger.error(f"Error syncing contact to Boost.space: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def create_automation(self, automation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create automation in Boost.space"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # Map automation data to Boost.space format
                boost_data = {
                    "workspace_id": self.workspace_id,
                    "automation": {
                        "name": automation_data["name"],
                        "description": automation_data.get("description"),
                        "trigger": automation_data["trigger"],
                        "actions": automation_data["actions"],
                        "conditions": automation_data.get("conditions", []),
                        "status": "active"
                    }
                }

                url = f"{self.base_url}/automations"
                async with session.post(url, headers=headers, json=boost_data) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "automation_id": result.get("id"),
                        "boost_data": result
                    }

        except Exception as e:
            logger.error(f"Error creating automation in Boost.space: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def enrich_contact(self, email: str) -> Dict[str, Any]:
        """Enrich contact data using Boost.space"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                url = f"{self.base_url}/enrich/contact"
                data = {
                    "workspace_id": self.workspace_id,
                    "email": email
                }
                
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "enriched_data": result
                    }

        except Exception as e:
            logger.error(f"Error enriching contact data: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def track_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track event in Boost.space"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                boost_data = {
                    "workspace_id": self.workspace_id,
                    "event": {
                        "name": event_data["name"],
                        "contact_id": event_data["contact_id"],
                        "properties": event_data.get("properties", {}),
                        "timestamp": event_data.get("timestamp", datetime.now().isoformat())
                    }
                }

                url = f"{self.base_url}/events"
                async with session.post(url, headers=headers, json=boost_data) as response:
                    result = await response.json()
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

    async def create_segment(self, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create contact segment in Boost.space"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                boost_data = {
                    "workspace_id": self.workspace_id,
                    "segment": {
                        "name": segment_data["name"],
                        "description": segment_data.get("description"),
                        "rules": segment_data["rules"]
                    }
                }

                url = f"{self.base_url}/segments"
                async with session.post(url, headers=headers, json=boost_data) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "segment_id": result.get("id")
                    }

        except Exception as e:
            logger.error(f"Error creating segment: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def register_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register webhook in Boost.space"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                boost_data = {
                    "workspace_id": self.workspace_id,
                    "webhook": {
                        "url": webhook_data["url"],
                        "events": webhook_data["events"],
                        "secret": webhook_data.get("secret")
                    }
                }

                url = f"{self.base_url}/webhooks"
                async with session.post(url, headers=headers, json=boost_data) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        self.webhook_handlers.append(result)
                    
                    return {
                        "success": response.status == 200,
                        "webhook_id": result.get("id")
                    }

        except Exception as e:
            logger.error(f"Error registering webhook: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    def _record_sync(self, entity_type: str, identifier: str, result: Dict[str, Any]) -> None:
        """Record sync operation in history"""
        self.sync_history.append({
            "timestamp": datetime.now().isoformat(),
            "entity_type": entity_type,
            "identifier": identifier,
            "result": result
        })

    async def get_sync_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get sync history with optional limit"""
        history = self.sync_history
        if limit:
            history = history[-limit:]
        return history

    async def get_workspace_status(self) -> Dict[str, Any]:
        """Get Boost.space workspace status"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                url = f"{self.base_url}/workspaces/{self.workspace_id}/status"
                async with session.get(url, headers=headers) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "status": result
                    }

        except Exception as e:
            logger.error(f"Error getting workspace status: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }
