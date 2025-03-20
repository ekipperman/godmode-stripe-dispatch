import logging
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime
import json
from sentry_config import capture_exception

logger = logging.getLogger(__name__)

class ExtendedCRMIntegration:
    def __init__(self, config: Dict[str, Any]):
        """Initialize extended CRM integration with multiple platforms"""
        self.config = config
        self.crm_config = config["plugins"]["crm_integration"]
        
        # Initialize platforms
        self.platforms = {
            "gohighlevel": self._init_gohighlevel() if self.crm_config["gohighlevel"]["enabled"] else None,
            "salesforce": self._init_salesforce() if self.crm_config["salesforce"]["enabled"] else None,
            "klaviyo": self._init_klaviyo() if self.crm_config["klaviyo"]["enabled"] else None,
            "hubspot": self._init_hubspot() if self.crm_config["hubspot"]["enabled"] else None
        }
        
        # Initialize sync history
        self.sync_history: List[Dict[str, Any]] = []
        
        logger.info("Extended CRM Integration initialized")

    def _init_gohighlevel(self) -> Dict[str, Any]:
        """Initialize GoHighLevel client"""
        return {
            "api_key": self.crm_config["gohighlevel"]["api_key"],
            "location_id": self.crm_config["gohighlevel"]["location_id"],
            "base_url": "https://api.gohighlevel.com/v1/"
        }

    def _init_salesforce(self) -> Dict[str, Any]:
        """Initialize Salesforce client"""
        return {
            "client_id": self.crm_config["salesforce"]["client_id"],
            "client_secret": self.crm_config["salesforce"]["client_secret"],
            "username": self.crm_config["salesforce"]["username"],
            "password": self.crm_config["salesforce"]["password"],
            "security_token": self.crm_config["salesforce"]["security_token"],
            "base_url": "https://login.salesforce.com/services/oauth2/token"
        }

    def _init_klaviyo(self) -> Dict[str, Any]:
        """Initialize Klaviyo client"""
        return {
            "api_key": self.crm_config["klaviyo"]["api_key"],
            "private_key": self.crm_config["klaviyo"]["private_key"],
            "base_url": "https://a.klaviyo.com/api/v2/"
        }

    def _init_hubspot(self) -> Dict[str, Any]:
        """Initialize HubSpot client"""
        return {
            "api_key": self.crm_config["hubspot"]["api_key"],
            "base_url": "https://api.hubapi.com/crm/v3/"
        }

    async def sync_contact(self, contact_data: Dict[str, Any], platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """Sync contact across specified or all enabled platforms"""
        try:
            if not platforms:
                platforms = [p for p, config in self.platforms.items() if config]

            results = {}
            for platform in platforms:
                if platform not in self.platforms or not self.platforms[platform]:
                    continue

                method = getattr(self, f"_sync_{platform}_contact", None)
                if method:
                    results[platform] = await method(contact_data)

            # Record sync
            self._record_sync("contact", contact_data.get("email"), platforms, results)

            return {
                "success": True,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error syncing contact: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _sync_gohighlevel_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync contact to GoHighLevel"""
        try:
            config = self.platforms["gohighlevel"]
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                }
                
                # Map contact data to GoHighLevel format
                ghl_data = {
                    "email": contact_data["email"],
                    "phone": contact_data.get("phone"),
                    "firstName": contact_data.get("first_name"),
                    "lastName": contact_data.get("last_name"),
                    "name": f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip(),
                    "locationId": config["location_id"],
                    "tags": contact_data.get("tags", []),
                    "source": "telegram_assistant"
                }

                url = f"{config['base_url']}contacts/"
                async with session.post(url, headers=headers, json=ghl_data) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "contact_id": result.get("id")
                    }

        except Exception as e:
            logger.error(f"Error syncing to GoHighLevel: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _sync_salesforce_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync contact to Salesforce"""
        try:
            config = self.platforms["salesforce"]
            async with aiohttp.ClientSession() as session:
                # Get access token
                token_data = {
                    "grant_type": "password",
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "username": config["username"],
                    "password": f"{config['password']}{config['security_token']}"
                }
                
                async with session.post(config["base_url"], data=token_data) as response:
                    auth = await response.json()
                    access_token = auth["access_token"]
                    instance_url = auth["instance_url"]

                # Map contact data to Salesforce format
                sf_data = {
                    "Email": contact_data["email"],
                    "Phone": contact_data.get("phone"),
                    "FirstName": contact_data.get("first_name"),
                    "LastName": contact_data.get("last_name"),
                    "LeadSource": "Telegram Assistant"
                }

                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }

                url = f"{instance_url}/services/data/v52.0/sobjects/Contact"
                async with session.post(url, headers=headers, json=sf_data) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 201,
                        "contact_id": result.get("id")
                    }

        except Exception as e:
            logger.error(f"Error syncing to Salesforce: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _sync_klaviyo_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync contact to Klaviyo"""
        try:
            config = self.platforms["klaviyo"]
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Klaviyo-API-Key {config['private_key']}",
                    "Content-Type": "application/json"
                }
                
                # Map contact data to Klaviyo format
                klaviyo_data = {
                    "token": config["api_key"],
                    "properties": {
                        "$email": contact_data["email"],
                        "$phone_number": contact_data.get("phone"),
                        "$first_name": contact_data.get("first_name"),
                        "$last_name": contact_data.get("last_name"),
                        "Source": "Telegram Assistant"
                    }
                }

                url = f"{config['base_url']}list/{config.get('list_id', '')}/members"
                async with session.post(url, headers=headers, json=klaviyo_data) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "contact_id": result.get("id")
                    }

        except Exception as e:
            logger.error(f"Error syncing to Klaviyo: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _sync_hubspot_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync contact to HubSpot"""
        try:
            config = self.platforms["hubspot"]
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                }
                
                # Map contact data to HubSpot format
                hs_data = {
                    "properties": {
                        "email": contact_data["email"],
                        "phone": contact_data.get("phone"),
                        "firstname": contact_data.get("first_name"),
                        "lastname": contact_data.get("last_name"),
                        "source": "telegram_assistant"
                    }
                }

                url = f"{config['base_url']}objects/contacts"
                async with session.post(url, headers=headers, json=hs_data) as response:
                    result = await response.json()
                    return {
                        "success": response.status == 201,
                        "contact_id": result.get("id")
                    }

        except Exception as e:
            logger.error(f"Error syncing to HubSpot: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    def _record_sync(self, entity_type: str, identifier: str, platforms: List[str], results: Dict[str, Any]) -> None:
        """Record sync operation in history"""
        self.sync_history.append({
            "timestamp": datetime.now().isoformat(),
            "entity_type": entity_type,
            "identifier": identifier,
            "platforms": platforms,
            "results": results
        })

    async def get_sync_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get sync history with optional limit"""
        history = self.sync_history
        if limit:
            history = history[-limit:]
        return history

    async def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all platforms"""
        status = {}
        for platform, config in self.platforms.items():
            if not config:
                status[platform] = {"enabled": False}
                continue

            try:
                method = getattr(self, f"_check_{platform}_status", None)
                if method:
                    status[platform] = await method()
                else:
                    status[platform] = {"enabled": True, "status": "unknown"}
            except Exception as e:
                logger.error(f"Error checking {platform} status: {str(e)}")
                capture_exception(e)
                status[platform] = {
                    "enabled": True,
                    "status": "error",
                    "error": str(e)
                }

        return status

    async def _check_gohighlevel_status(self) -> Dict[str, Any]:
        """Check GoHighLevel platform status"""
        try:
            config = self.platforms["gohighlevel"]
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config['api_key']}"
                }
                url = f"{config['base_url']}locations/{config['location_id']}"
                async with session.get(url, headers=headers) as response:
                    return {
                        "enabled": True,
                        "status": "active" if response.status == 200 else "error",
                        "response_code": response.status
                    }
        except Exception as e:
            return {
                "enabled": True,
                "status": "error",
                "error": str(e)
            }

    async def _check_salesforce_status(self) -> Dict[str, Any]:
        """Check Salesforce platform status"""
        try:
            config = self.platforms["salesforce"]
            async with aiohttp.ClientSession() as session:
                token_data = {
                    "grant_type": "password",
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "username": config["username"],
                    "password": f"{config['password']}{config['security_token']}"
                }
                async with session.post(config["base_url"], data=token_data) as response:
                    return {
                        "enabled": True,
                        "status": "active" if response.status == 200 else "error",
                        "response_code": response.status
                    }
        except Exception as e:
            return {
                "enabled": True,
                "status": "error",
                "error": str(e)
            }

    async def _check_klaviyo_status(self) -> Dict[str, Any]:
        """Check Klaviyo platform status"""
        try:
            config = self.platforms["klaviyo"]
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Klaviyo-API-Key {config['private_key']}"
                }
                url = f"{config['base_url']}metrics"
                async with session.get(url, headers=headers) as response:
                    return {
                        "enabled": True,
                        "status": "active" if response.status == 200 else "error",
                        "response_code": response.status
                    }
        except Exception as e:
            return {
                "enabled": True,
                "status": "error",
                "error": str(e)
            }

    async def _check_hubspot_status(self) -> Dict[str, Any]:
        """Check HubSpot platform status"""
        try:
            config = self.platforms["hubspot"]
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config['api_key']}"
                }
                url = f"{config['base_url']}objects/contacts"
                async with session.get(url, headers=headers) as response:
                    return {
                        "enabled": True,
                        "status": "active" if response.status == 200 else "error",
                        "response_code": response.status
                    }
        except Exception as e:
            return {
                "enabled": True,
                "status": "error",
                "error": str(e)
            }
