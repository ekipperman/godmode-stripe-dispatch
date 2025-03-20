import { createClient } from '@supabase/supabase-js';

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
    },
    db: {
      schema: 'public'
    },
    global: {
      headers: {
        'x-application-name': 'telegram-ai-assistant'
      }
    }
  }
);

export default supabaseClient;

// Helper types for better TypeScript support
export type SupabaseClient = typeof supabaseClient;
export type SupabaseResponse<T> = Awaited<ReturnType<typeof supabaseClient.from<T>>>;
export type SupabaseError = Awaited<ReturnType<typeof supabaseClient.from>>['error'];
