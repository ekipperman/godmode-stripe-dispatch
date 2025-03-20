import logging
from typing import Dict, Any, Optional, List
import hubspot
from shopify import Shopify, Session
import stripe
from datetime import datetime
import asyncio
from aiohttp import ClientSession

logger = logging.getLogger(__name__)

class CRMIntegration:
    def __init__(self, config: Dict[str, Any]):
        """Initialize CRM integration with configuration"""
        self.config = config
        self.crm_config = config["plugins"]["crm"]
        
        # Initialize HubSpot client
        if self.crm_config["hubspot"]["enabled"]:
            self.hubspot_client = hubspot.Client.create(
                access_token=self.crm_config["hubspot"]["api_key"]
            )
        
        # Initialize Shopify client
        if self.crm_config["shopify"]["enabled"]:
            shop_url = self.crm_config["shopify"]["shop_url"]
            access_token = self.crm_config["shopify"]["access_token"]
            self.shopify_session = Session(shop_url, access_token)
            self.shopify_client = Shopify(self.shopify_session)
        
        # Initialize Stripe client
        if self.crm_config["stripe"]["enabled"]:
            stripe.api_key = self.crm_config["stripe"]["secret_key"]
            self.stripe_client = stripe
        
        # Initialize cache for contact data
        self.contact_cache = {}
        self.last_sync = None
        
        logger.info("CRM Integration initialized successfully")

    async def sync_all(self) -> Dict[str, Any]:
        """Synchronize data across all enabled CRM platforms"""
        try:
            sync_tasks = []
            
            if self.crm_config["hubspot"]["enabled"]:
                sync_tasks.append(self._sync_hubspot())
            if self.crm_config["shopify"]["enabled"]:
                sync_tasks.append(self._sync_shopify())
            if self.crm_config["stripe"]["enabled"]:
                sync_tasks.append(self._sync_stripe())
            
            # Run all sync tasks concurrently
            results = await asyncio.gather(*sync_tasks, return_exceptions=True)
            
            # Process results
            success = all(isinstance(r, dict) and r.get("success", False) for r in results)
            
            if success:
                self.last_sync = datetime.now()
            
            return {
                "success": success,
                "timestamp": self.last_sync.isoformat() if self.last_sync else None,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error syncing CRM data: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _sync_hubspot(self) -> Dict[str, Any]:
        """Synchronize data with HubSpot"""
        try:
            # Get all contacts from HubSpot
            contacts = self.hubspot_client.crm.contacts.get_all()
            
            # Update contact cache
            for contact in contacts:
                self.contact_cache[contact.properties["email"]] = {
                    "source": "hubspot",
                    "data": contact.properties
                }
            
            return {
                "success": True,
                "platform": "hubspot",
                "contacts_synced": len(contacts)
            }
            
        except Exception as e:
            logger.error(f"Error syncing with HubSpot: {str(e)}")
            return {
                "success": False,
                "platform": "hubspot",
                "error": str(e)
            }

    async def _sync_shopify(self) -> Dict[str, Any]:
        """Synchronize data with Shopify"""
        try:
            # Get all customers from Shopify
            customers = self.shopify_client.Customer.find()
            
            # Update contact cache
            for customer in customers:
                if customer.email:
                    self.contact_cache[customer.email] = {
                        "source": "shopify",
                        "data": customer.to_dict()
                    }
            
            return {
                "success": True,
                "platform": "shopify",
                "customers_synced": len(customers)
            }
            
        except Exception as e:
            logger.error(f"Error syncing with Shopify: {str(e)}")
            return {
                "success": False,
                "platform": "shopify",
                "error": str(e)
            }

    async def _sync_stripe(self) -> Dict[str, Any]:
        """Synchronize data with Stripe"""
        try:
            # Get all customers from Stripe
            customers = self.stripe_client.Customer.list()
            
            # Update contact cache
            for customer in customers.auto_paging_iter():
                if customer.email:
                    self.contact_cache[customer.email] = {
                        "source": "stripe",
                        "data": customer
                    }
            
            return {
                "success": True,
                "platform": "stripe",
                "customers_synced": len(customers.data)
            }
            
        except Exception as e:
            logger.error(f"Error syncing with Stripe: {str(e)}")
            return {
                "success": False,
                "platform": "stripe",
                "error": str(e)
            }

    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact across all enabled platforms"""
        try:
            creation_tasks = []
            
            if self.crm_config["hubspot"]["enabled"]:
                creation_tasks.append(self._create_hubspot_contact(contact_data))
            if self.crm_config["shopify"]["enabled"]:
                creation_tasks.append(self._create_shopify_customer(contact_data))
            if self.crm_config["stripe"]["enabled"]:
                creation_tasks.append(self._create_stripe_customer(contact_data))
            
            results = await asyncio.gather(*creation_tasks, return_exceptions=True)
            
            success = all(isinstance(r, dict) and r.get("success", False) for r in results)
            
            return {
                "success": success,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error creating contact: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _create_hubspot_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a contact in HubSpot"""
        try:
            properties = {
                "email": contact_data["email"],
                "firstname": contact_data.get("first_name", ""),
                "lastname": contact_data.get("last_name", ""),
                "phone": contact_data.get("phone", "")
            }
            
            contact = self.hubspot_client.crm.contacts.basic_api.create(
                properties=properties
            )
            
            return {
                "success": True,
                "platform": "hubspot",
                "contact_id": contact.id
            }
            
        except Exception as e:
            logger.error(f"Error creating HubSpot contact: {str(e)}")
            return {
                "success": False,
                "platform": "hubspot",
                "error": str(e)
            }

    async def _create_shopify_customer(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customer in Shopify"""
        try:
            customer = self.shopify_client.Customer()
            customer.email = contact_data["email"]
            customer.first_name = contact_data.get("first_name", "")
            customer.last_name = contact_data.get("last_name", "")
            customer.phone = contact_data.get("phone", "")
            customer.save()
            
            return {
                "success": True,
                "platform": "shopify",
                "customer_id": customer.id
            }
            
        except Exception as e:
            logger.error(f"Error creating Shopify customer: {str(e)}")
            return {
                "success": False,
                "platform": "shopify",
                "error": str(e)
            }

    async def _create_stripe_customer(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customer in Stripe"""
        try:
            customer = self.stripe_client.Customer.create(
                email=contact_data["email"],
                name=f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip(),
                phone=contact_data.get("phone", "")
            )
            
            return {
                "success": True,
                "platform": "stripe",
                "customer_id": customer.id
            }
            
        except Exception as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            return {
                "success": False,
                "platform": "stripe",
                "error": str(e)
            }

    async def get_customer_info(self, email: str) -> Dict[str, Any]:
        """Get customer information from all platforms"""
        try:
            # Check cache first
            if email in self.contact_cache:
                return {
                    "success": True,
                    "source": self.contact_cache[email]["source"],
                    "data": self.contact_cache[email]["data"]
                }
            
            # If not in cache, search across platforms
            search_tasks = []
            
            if self.crm_config["hubspot"]["enabled"]:
                search_tasks.append(self._search_hubspot_contact(email))
            if self.crm_config["shopify"]["enabled"]:
                search_tasks.append(self._search_shopify_customer(email))
            if self.crm_config["stripe"]["enabled"]:
                search_tasks.append(self._search_stripe_customer(email))
            
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results
            customer_data = {}
            for result in results:
                if isinstance(result, dict) and result.get("success"):
                    customer_data[result["platform"]] = result["data"]
            
            if customer_data:
                return {
                    "success": True,
                    "data": customer_data
                }
            else:
                return {
                    "success": False,
                    "error": "Customer not found"
                }
            
        except Exception as e:
            logger.error(f"Error getting customer info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _search_hubspot_contact(self, email: str) -> Dict[str, Any]:
        """Search for a contact in HubSpot"""
        try:
            filter_groups = [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}]
            results = self.hubspot_client.crm.contacts.search_api.do_search(
                filter_groups=filter_groups
            )
            
            if results.total > 0:
                return {
                    "success": True,
                    "platform": "hubspot",
                    "data": results.results[0].properties
                }
            else:
                return {
                    "success": False,
                    "platform": "hubspot",
                    "error": "Contact not found"
                }
            
        except Exception as e:
            logger.error(f"Error searching HubSpot contact: {str(e)}")
            return {
                "success": False,
                "platform": "hubspot",
                "error": str(e)
            }

    async def _search_shopify_customer(self, email: str) -> Dict[str, Any]:
        """Search for a customer in Shopify"""
        try:
            customers = self.shopify_client.Customer.search(query=f"email:{email}")
            
            if customers:
                return {
                    "success": True,
                    "platform": "shopify",
                    "data": customers[0].to_dict()
                }
            else:
                return {
                    "success": False,
                    "platform": "shopify",
                    "error": "Customer not found"
                }
            
        except Exception as e:
            logger.error(f"Error searching Shopify customer: {str(e)}")
            return {
                "success": False,
                "platform": "shopify",
                "error": str(e)
            }

    async def _search_stripe_customer(self, email: str) -> Dict[str, Any]:
        """Search for a customer in Stripe"""
        try:
            customers = self.stripe_client.Customer.list(email=email)
            
            if customers.data:
                return {
                    "success": True,
                    "platform": "stripe",
                    "data": customers.data[0]
                }
            else:
                return {
                    "success": False,
                    "platform": "stripe",
                    "error": "Customer not found"
                }
            
        except Exception as e:
            logger.error(f"Error searching Stripe customer: {str(e)}")
            return {
                "success": False,
                "platform": "stripe",
                "error": str(e)
            }

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get the current sync status"""
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "cached_contacts": len(self.contact_cache),
            "platforms": {
                "hubspot": self.crm_config["hubspot"]["enabled"],
                "shopify": self.crm_config["shopify"]["enabled"],
                "stripe": self.crm_config["stripe"]["enabled"]
            }
        }
