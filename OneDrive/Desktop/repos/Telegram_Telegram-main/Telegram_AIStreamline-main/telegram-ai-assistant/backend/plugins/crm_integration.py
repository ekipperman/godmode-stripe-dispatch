import logging
import aiohttp
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import stripe
import shopify
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInput

logger = logging.getLogger(__name__)

class CRMIntegration:
    def __init__(self, config: Dict[str, Any]):
        """Initialize CRM integration with configuration"""
        self.config = config
        self.crm_config = config["plugins"]["crm"]
        
        # Initialize HubSpot
        if self.crm_config["hubspot"]["enabled"]:
            self.hubspot_client = HubSpot(api_key=self.crm_config["hubspot"]["api_key"])
        
        # Initialize Shopify
        if self.crm_config["shopify"]["enabled"]:
            shopify.ShopifyResource.set_site(
                f"https://{self.crm_config['shopify']['shop_url']}/admin/api/2023-01"
            )
            shopify.Session.setup(
                api_key=self.crm_config["shopify"]["access_token"],
                secret=None
            )
        
        # Initialize Stripe
        if self.crm_config["stripe"]["enabled"]:
            stripe.api_key = self.crm_config["stripe"]["secret_key"]
        
        logger.info("CRM Integration initialized successfully")

    async def sync_all(self) -> Dict[str, Any]:
        """Synchronize data across all enabled CRM platforms"""
        results = {
            "hubspot": None,
            "shopify": None,
            "stripe": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Sync HubSpot
            if self.crm_config["hubspot"]["enabled"]:
                results["hubspot"] = await self.sync_hubspot()
            
            # Sync Shopify
            if self.crm_config["shopify"]["enabled"]:
                results["shopify"] = await self.sync_shopify()
            
            # Sync Stripe
            if self.crm_config["stripe"]["enabled"]:
                results["stripe"] = await self.sync_stripe()
            
            return results
            
        except Exception as e:
            logger.error(f"Error in CRM sync: {str(e)}")
            raise

    async def sync_hubspot(self) -> Dict[str, Any]:
        """Synchronize data with HubSpot"""
        try:
            # Get recent contacts
            contacts = self.hubspot_client.crm.contacts.get_all()
            
            # Get recent deals
            deals = self.hubspot_client.crm.deals.get_all()
            
            return {
                "status": "success",
                "contacts_synced": len(list(contacts)),
                "deals_synced": len(list(deals)),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing HubSpot: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def sync_shopify(self) -> Dict[str, Any]:
        """Synchronize data with Shopify"""
        try:
            # Get recent orders
            orders = shopify.Order.find(
                created_at_min=(datetime.now() - timedelta(days=1)).isoformat()
            )
            
            # Get products
            products = shopify.Product.find()
            
            return {
                "status": "success",
                "orders_synced": len(list(orders)),
                "products_synced": len(list(products)),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing Shopify: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def sync_stripe(self) -> Dict[str, Any]:
        """Synchronize data with Stripe"""
        try:
            # Get recent payments
            payments = stripe.PaymentIntent.list(
                created={
                    'gte': int((datetime.now() - timedelta(days=1)).timestamp())
                }
            )
            
            # Get recent customers
            customers = stripe.Customer.list(
                created={
                    'gte': int((datetime.now() - timedelta(days=1)).timestamp())
                }
            )
            
            return {
                "status": "success",
                "payments_synced": len(payments.data),
                "customers_synced": len(customers.data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing Stripe: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def create_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact across CRM platforms"""
        results = {}
        
        try:
            # Create HubSpot contact
            if self.crm_config["hubspot"]["enabled"]:
                hubspot_contact = await self._create_hubspot_contact(data)
                results["hubspot"] = hubspot_contact
            
            # Create Stripe customer
            if self.crm_config["stripe"]["enabled"]:
                stripe_customer = await self._create_stripe_customer(data)
                results["stripe"] = stripe_customer
            
            return results
            
        except Exception as e:
            logger.error(f"Error creating contact: {str(e)}")
            raise

    async def _create_hubspot_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a contact in HubSpot"""
        try:
            properties = {
                "email": data.get("email"),
                "firstname": data.get("first_name"),
                "lastname": data.get("last_name"),
                "phone": data.get("phone"),
                "company": data.get("company")
            }
            
            contact_input = SimplePublicObjectInput(properties=properties)
            contact = self.hubspot_client.crm.contacts.basic_api.create(
                simple_public_object_input=contact_input
            )
            
            return {
                "status": "success",
                "contact_id": contact.id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating HubSpot contact: {str(e)}")
            raise

    async def _create_stripe_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customer in Stripe"""
        try:
            customer = stripe.Customer.create(
                email=data.get("email"),
                name=f"{data.get('first_name')} {data.get('last_name')}",
                phone=data.get("phone"),
                metadata={
                    "company": data.get("company"),
                    "source": "telegram_bot"
                }
            )
            
            return {
                "status": "success",
                "customer_id": customer.id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            raise

    async def get_customer_info(self, email: str) -> Dict[str, Any]:
        """Get customer information from all CRM platforms"""
        results = {
            "hubspot": None,
            "shopify": None,
            "stripe": None
        }
        
        try:
            # Get HubSpot contact
            if self.crm_config["hubspot"]["enabled"]:
                contact = self.hubspot_client.crm.contacts.basic_api.get_by_id(
                    contact_id=email
                )
                results["hubspot"] = contact.properties
            
            # Get Stripe customer
            if self.crm_config["stripe"]["enabled"]:
                customers = stripe.Customer.list(email=email)
                if customers.data:
                    results["stripe"] = customers.data[0]
            
            # Get Shopify customer
            if self.crm_config["shopify"]["enabled"]:
                customers = shopify.Customer.find(email=email)
                if customers:
                    results["shopify"] = customers[0].to_dict()
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting customer info: {str(e)}")
            raise

    async def get_analytics(self) -> Dict[str, Any]:
        """Get analytics data from all CRM platforms"""
        try:
            analytics = {
                "total_contacts": 0,
                "total_orders": 0,
                "total_revenue": 0,
                "platforms": {
                    "hubspot": None,
                    "shopify": None,
                    "stripe": None
                }
            }
            
            # Get HubSpot analytics
            if self.crm_config["hubspot"]["enabled"]:
                hubspot_analytics = await self._get_hubspot_analytics()
                analytics["platforms"]["hubspot"] = hubspot_analytics
                analytics["total_contacts"] += hubspot_analytics.get("total_contacts", 0)
            
            # Get Shopify analytics
            if self.crm_config["shopify"]["enabled"]:
                shopify_analytics = await self._get_shopify_analytics()
                analytics["platforms"]["shopify"] = shopify_analytics
                analytics["total_orders"] += shopify_analytics.get("total_orders", 0)
                analytics["total_revenue"] += shopify_analytics.get("total_revenue", 0)
            
            # Get Stripe analytics
            if self.crm_config["stripe"]["enabled"]:
                stripe_analytics = await self._get_stripe_analytics()
                analytics["platforms"]["stripe"] = stripe_analytics
                analytics["total_revenue"] += stripe_analytics.get("total_revenue", 0)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            raise

    async def _get_hubspot_analytics(self) -> Dict[str, Any]:
        """Get analytics data from HubSpot"""
        try:
            contacts = self.hubspot_client.crm.contacts.get_all()
            deals = self.hubspot_client.crm.deals.get_all()
            
            return {
                "total_contacts": len(list(contacts)),
                "total_deals": len(list(deals)),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting HubSpot analytics: {str(e)}")
            raise

    async def _get_shopify_analytics(self) -> Dict[str, Any]:
        """Get analytics data from Shopify"""
        try:
            orders = shopify.Order.find()
            total_revenue = sum(float(order.total_price) for order in orders)
            
            return {
                "total_orders": len(list(orders)),
                "total_revenue": total_revenue,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Shopify analytics: {str(e)}")
            raise

    async def _get_stripe_analytics(self) -> Dict[str, Any]:
        """Get analytics data from Stripe"""
        try:
            charges = stripe.Charge.list(
                created={
                    'gte': int((datetime.now() - timedelta(days=30)).timestamp())
                }
            )
            
            total_revenue = sum(charge.amount for charge in charges.data) / 100  # Convert cents to dollars
            
            return {
                "total_charges": len(charges.data),
                "total_revenue": total_revenue,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Stripe analytics: {str(e)}")
            raise
