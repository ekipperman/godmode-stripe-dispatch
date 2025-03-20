from typing import Dict, Any, Optional
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseConfig:
    def __init__(self):
        """Initialize Supabase client with environment variables"""
        self.url: str = os.getenv("SUPABASE_URL")
        self.key: str = os.getenv("SUPABASE_KEY")
        self.client: Optional[Client] = None
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and key must be set in environment variables")
        
        self.client = create_client(self.url, self.key)

    async def initialize_tables(self):
        """Initialize database tables if they don't exist"""
        # Users table
        await self.client.table("users").execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
                telegram_id TEXT UNIQUE,
                role TEXT DEFAULT 'user',
                settings JSONB DEFAULT '{}'::jsonb
            );
        """)

        # CRM data table
        await self.client.table("crm_data").execute("""
            CREATE TABLE IF NOT EXISTS crm_data (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id),
                type TEXT NOT NULL,
                data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
                status TEXT DEFAULT 'active'
            );
        """)

        # Transactions table
        await self.client.table("transactions").execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id),
                amount DECIMAL NOT NULL,
                currency TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
                metadata JSONB DEFAULT '{}'::jsonb
            );
        """)

        # Campaigns table
        await self.client.table("campaigns").execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id),
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                content JSONB NOT NULL,
                schedule TIMESTAMP WITH TIME ZONE,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
                metrics JSONB DEFAULT '{}'::jsonb
            );
        """)

    async def setup_row_level_security(self):
        """Set up row level security policies"""
        # Users table policies
        await self.client.table("users").execute("""
            ALTER TABLE users ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY "Users can view own data"
                ON users FOR SELECT
                USING (auth.uid() = id);
                
            CREATE POLICY "Users can update own data"
                ON users FOR UPDATE
                USING (auth.uid() = id);
        """)

        # CRM data policies
        await self.client.table("crm_data").execute("""
            ALTER TABLE crm_data ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY "Users can view own CRM data"
                ON crm_data FOR SELECT
                USING (auth.uid() = user_id);
                
            CREATE POLICY "Users can modify own CRM data"
                ON crm_data FOR ALL
                USING (auth.uid() = user_id);
        """)

        # Transactions policies
        await self.client.table("transactions").execute("""
            ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY "Users can view own transactions"
                ON transactions FOR SELECT
                USING (auth.uid() = user_id);
                
            CREATE POLICY "Users can create own transactions"
                ON transactions FOR INSERT
                WITH CHECK (auth.uid() = user_id);
        """)

        # Campaigns policies
        await self.client.table("campaigns").execute("""
            ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY "Users can view own campaigns"
                ON campaigns FOR SELECT
                USING (auth.uid() = user_id);
                
            CREATE POLICY "Users can modify own campaigns"
                ON campaigns FOR ALL
                USING (auth.uid() = user_id);
        """)

    def get_client(self) -> Client:
        """Get the Supabase client instance"""
        if not self.client:
            raise RuntimeError("Supabase client not initialized")
        return self.client

# Create a singleton instance
supabase = SupabaseConfig()
