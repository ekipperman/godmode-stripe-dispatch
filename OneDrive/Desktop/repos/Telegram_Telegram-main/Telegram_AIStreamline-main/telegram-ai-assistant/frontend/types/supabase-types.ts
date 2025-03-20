export interface SupabaseUser {
  id: string;
  email?: string;
  phone?: string;
  created_at: string;
  updated_at: string;
  last_sign_in_at?: string;
  user_metadata: Record<string, any>;
  app_metadata: Record<string, any>;
}

export interface SupabaseSession {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  user: SupabaseUser;
}

export interface SupabaseAuthResponse {
  session: SupabaseSession | null;
  user: SupabaseUser | null;
  error?: Error;
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

export interface SupabaseSubscriptionPayload<T> {
  new: T;
  old: T;
  eventType: 'INSERT' | 'UPDATE' | 'DELETE';
}

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

export interface SupabaseSubscriptionFilter {
  event?: 'INSERT' | 'UPDATE' | 'DELETE' | '*';
  schema?: string;
  table?: string;
  filter?: string;
}
