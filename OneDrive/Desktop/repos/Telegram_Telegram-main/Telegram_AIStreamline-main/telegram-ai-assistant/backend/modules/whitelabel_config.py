import logging
from typing import Dict, Any, Optional, List
import json
from pathlib import Path
import aiofiles
import asyncio
from datetime import datetime
import hashlib
from sentry_config import capture_exception

logger = logging.getLogger(__name__)

class WhitelabelConfig:
    def __init__(self, config: Dict[str, Any]):
        """Initialize whitelabel configuration manager"""
        self.config = config
        self.whitelabel_config = config["plugins"]["whitelabel"]
        self.clients_dir = Path(self.whitelabel_config["clients_dir"])
        self.clients_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for client configurations
        self.client_cache: Dict[str, Dict[str, Any]] = {}
        
        # Configuration change history
        self.change_history: List[Dict[str, Any]] = []
        
        # Initialize webhook handlers
        self.webhook_handlers: List[Dict[str, Any]] = []
        
        logger.info("Whitelabel Configuration Manager initialized")

    async def load_client_config(self, client_id: str) -> Dict[str, Any]:
        """Load client-specific configuration"""
        try:
            # Check cache first
            if client_id in self.client_cache:
                return self.client_cache[client_id]
            
            config_path = self.clients_dir / f"{client_id}.json"
            if not config_path.exists():
                return await self.create_default_config(client_id)
            
            async with aiofiles.open(config_path, 'r') as f:
                config = json.loads(await f.read())
                self.client_cache[client_id] = config
                return config
                
        except Exception as e:
            logger.error(f"Error loading client config: {str(e)}")
            capture_exception(e)
            return await self.create_default_config(client_id)

    async def create_default_config(self, client_id: str) -> Dict[str, Any]:
        """Create default client configuration"""
        try:
            default_config = {
                "client_id": client_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "branding": {
                    "company_name": "Default Company",
                    "logo_url": "",
                    "favicon_url": "",
                    "primary_color": "#007bff",
                    "secondary_color": "#6c757d",
                    "accent_color": "#28a745",
                    "font_family": "Arial, sans-serif",
                    "custom_css": ""
                },
                "features": {
                    "ai_chatbot": True,
                    "voice_command": True,
                    "crm_integration": True,
                    "social_media": True,
                    "email_automation": True,
                    "analytics": True,
                    "payment_gateway": True
                },
                "integrations": {
                    "gohighlevel": {
                        "enabled": False,
                        "api_key": "",
                        "location_id": ""
                    },
                    "salesforce": {
                        "enabled": False,
                        "client_id": "",
                        "client_secret": ""
                    },
                    "klaviyo": {
                        "enabled": False,
                        "api_key": "",
                        "list_id": ""
                    }
                },
                "customization": {
                    "telegram_bot_name": f"Assistant_{client_id}",
                    "welcome_message": "Welcome! How can I assist you today?",
                    "email_signature": "Best regards,\nYour AI Assistant",
                    "custom_commands": []
                },
                "security": {
                    "allowed_domains": [],
                    "api_rate_limit": 100,
                    "require_authentication": True
                }
            }
            
            # Save default config
            await self.save_client_config(client_id, default_config)
            return default_config
            
        except Exception as e:
            logger.error(f"Error creating default config: {str(e)}")
            capture_exception(e)
            raise

    async def save_client_config(self, client_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Save client configuration"""
        try:
            config["updated_at"] = datetime.now().isoformat()
            
            config_path = self.clients_dir / f"{client_id}.json"
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(json.dumps(config, indent=2))
            
            # Update cache
            self.client_cache[client_id] = config
            
            # Record change
            self._record_change(client_id, "update_config")
            
            # Notify webhooks
            await self._notify_webhooks(client_id, "config_updated", config)
            
            return config
            
        except Exception as e:
            logger.error(f"Error saving client config: {str(e)}")
            capture_exception(e)
            raise

    async def update_branding(self, client_id: str, branding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update client branding configuration"""
        try:
            config = await self.load_client_config(client_id)
            config["branding"].update(branding_data)
            
            return await self.save_client_config(client_id, config)
            
        except Exception as e:
            logger.error(f"Error updating branding: {str(e)}")
            capture_exception(e)
            raise

    async def update_features(self, client_id: str, features: Dict[str, bool]) -> Dict[str, Any]:
        """Update client feature configuration"""
        try:
            config = await self.load_client_config(client_id)
            config["features"].update(features)
            
            return await self.save_client_config(client_id, config)
            
        except Exception as e:
            logger.error(f"Error updating features: {str(e)}")
            capture_exception(e)
            raise

    async def update_integrations(self, client_id: str, integrations: Dict[str, Any]) -> Dict[str, Any]:
        """Update client integration configuration"""
        try:
            config = await self.load_client_config(client_id)
            config["integrations"].update(integrations)
            
            return await self.save_client_config(client_id, config)
            
        except Exception as e:
            logger.error(f"Error updating integrations: {str(e)}")
            capture_exception(e)
            raise

    async def get_client_theme(self, client_id: str) -> Dict[str, Any]:
        """Get client theme configuration"""
        try:
            config = await self.load_client_config(client_id)
            return {
                "branding": config["branding"],
                "customization": config["customization"]
            }
            
        except Exception as e:
            logger.error(f"Error getting client theme: {str(e)}")
            capture_exception(e)
            raise

    async def register_webhook(self, url: str, events: List[str]) -> str:
        """Register webhook for configuration changes"""
        try:
            webhook_id = hashlib.md5(f"{url}_{','.join(events)}".encode()).hexdigest()
            
            self.webhook_handlers.append({
                "id": webhook_id,
                "url": url,
                "events": events,
                "created_at": datetime.now().isoformat()
            })
            
            return webhook_id
            
        except Exception as e:
            logger.error(f"Error registering webhook: {str(e)}")
            capture_exception(e)
            raise

    async def remove_webhook(self, webhook_id: str) -> bool:
        """Remove registered webhook"""
        try:
            self.webhook_handlers = [h for h in self.webhook_handlers if h["id"] != webhook_id]
            return True
            
        except Exception as e:
            logger.error(f"Error removing webhook: {str(e)}")
            capture_exception(e)
            return False

    async def _notify_webhooks(self, client_id: str, event: str, data: Dict[str, Any]) -> None:
        """Notify registered webhooks of configuration changes"""
        try:
            async with aiohttp.ClientSession() as session:
                for handler in self.webhook_handlers:
                    if event in handler["events"]:
                        try:
                            payload = {
                                "client_id": client_id,
                                "event": event,
                                "timestamp": datetime.now().isoformat(),
                                "data": data
                            }
                            
                            async with session.post(handler["url"], json=payload) as response:
                                if response.status != 200:
                                    logger.warning(f"Webhook notification failed: {handler['url']}")
                                    
                        except Exception as e:
                            logger.error(f"Error notifying webhook: {str(e)}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error in webhook notification: {str(e)}")
            capture_exception(e)

    def _record_change(self, client_id: str, action: str) -> None:
        """Record configuration change in history"""
        self.change_history.append({
            "timestamp": datetime.now().isoformat(),
            "client_id": client_id,
            "action": action
        })

    async def get_change_history(self, client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        if client_id:
            return [c for c in self.change_history if c["client_id"] == client_id]
        return self.change_history

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate client configuration"""
        try:
            required_fields = ["branding", "features", "integrations", "customization", "security"]
            
            # Check required fields
            if not all(field in config for field in required_fields):
                return False
            
            # Validate branding
            if not all(field in config["branding"] for field in ["company_name", "primary_color"]):
                return False
            
            # Validate features
            if not isinstance(config["features"], dict):
                return False
            
            # Validate security
            if not isinstance(config["security"], dict) or "require_authentication" not in config["security"]:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating config: {str(e)}")
            capture_exception(e)
            return False
