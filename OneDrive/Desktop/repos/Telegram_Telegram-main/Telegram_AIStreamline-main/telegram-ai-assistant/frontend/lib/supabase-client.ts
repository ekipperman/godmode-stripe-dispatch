import { createClient } from '@supabase/supabase-js';
import type { Database } from '../types/database-schema';

if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
  throw new Error('Missing environment variable: NEXT_PUBLIC_SUPABASE_URL');
}

if (!process.env.NEXT_PUBLIC_SUPABASE_KEY) {
  throw new Error('Missing environment variable: NEXT_PUBLIC_SUPABASE_KEY');
}

// Create a single supabase client for interacting with your database
const supabaseClient = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_KEY,
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true
    }
  }
);

// Export database types
export type Tables = Database['public']['Tables'];
export type TableName = keyof Tables;
export type TableRow<T extends TableName> = Tables[T]['Row'];
export type TableInsert<T extends TableName> = Tables[T]['Insert'];
export type TableUpdate<T extends TableName> = Tables[T]['Update'];

// Common response type
export interface SupabaseError {
  message: string;
  details?: string;
  hint?: string;
  code?: string;
}

export interface SupabaseResponse<T> {
  data: T | null;
  error: SupabaseError | null;
}

export interface SupabaseQueryOptions {
  columns?: string;
  filters?: Record<string, any>;
  limit?: number;
  order?: {
    column: string;
    ascending?: boolean;
  };
}

export interface SupabaseSubscriptionFilter {
  event?: 'INSERT' | 'UPDATE' | 'DELETE' | '*';
  filter?: string;
}

export interface SupabaseSubscriptionPayload<T> {
  eventType: 'INSERT' | 'UPDATE' | 'DELETE';
  new: T;
  old: T;
}

export { supabaseClient };
