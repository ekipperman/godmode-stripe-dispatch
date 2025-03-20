from typing import Dict, Any, List, Optional
from datetime import datetime
from .supabase_config import supabase

class DatabaseService:
    def __init__(self):
        """Initialize database service with Supabase client"""
        self.client = supabase.get_client()

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        response = await self.client.table("users").insert(user_data).execute()
        return response.data[0] if response.data else None

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        response = await self.client.table("users").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None

    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data"""
        response = await self.client.table("users").update(user_data).eq("id", user_id).execute()
        return response.data[0] if response.data else None

    async def create_crm_entry(self, crm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new CRM entry"""
        response = await self.client.table("crm_data").insert(crm_data).execute()
        return response.data[0] if response.data else None

    async def get_crm_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all CRM data for a user"""
        response = await self.client.table("crm_data").select("*").eq("user_id", user_id).execute()
        return response.data if response.data else []

    async def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new transaction"""
        response = await self.client.table("transactions").insert(transaction_data).execute()
        return response.data[0] if response.data else None

    async def get_transactions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all transactions for a user"""
        response = await self.client.table("transactions").select("*").eq("user_id", user_id).execute()
        return response.data if response.data else []

    async def update_transaction(self, transaction_id: str, status: str) -> Dict[str, Any]:
        """Update transaction status"""
        response = await self.client.table("transactions").update({
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", transaction_id).execute()
        return response.data[0] if response.data else None

    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new marketing campaign"""
        response = await self.client.table("campaigns").insert(campaign_data).execute()
        return response.data[0] if response.data else None

    async def get_campaigns(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get campaigns for a user, optionally filtered by status"""
        query = self.client.table("campaigns").select("*").eq("user_id", user_id)
        if status:
            query = query.eq("status", status)
        response = await query.execute()
        return response.data if response.data else []

    async def update_campaign(self, campaign_id: str, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update campaign data"""
        campaign_data["updated_at"] = datetime.utcnow().isoformat()
        response = await self.client.table("campaigns").update(campaign_data).eq("id", campaign_id).execute()
        return response.data[0] if response.data else None

    async def update_campaign_metrics(self, campaign_id: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Update campaign metrics"""
        response = await self.client.table("campaigns").update({
            "metrics": metrics,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", campaign_id).execute()
        return response.data[0] if response.data else None

    async def get_analytics(self, user_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get analytics data for a user within a date range"""
        transactions = await self.client.table("transactions").select("*").eq("user_id", user_id).gte("created_at", start_date).lte("created_at", end_date).execute()
        campaigns = await self.client.table("campaigns").select("*").eq("user_id", user_id).gte("created_at", start_date).lte("created_at", end_date).execute()
        crm_data = await self.client.table("crm_data").select("*").eq("user_id", user_id).gte("created_at", start_date).lte("created_at", end_date).execute()

        return {
            "transactions": transactions.data if transactions.data else [],
            "campaigns": campaigns.data if campaigns.data else [],
            "crm_data": crm_data.data if crm_data.data else []
        }

# Create a singleton instance
db_service = DatabaseService()
