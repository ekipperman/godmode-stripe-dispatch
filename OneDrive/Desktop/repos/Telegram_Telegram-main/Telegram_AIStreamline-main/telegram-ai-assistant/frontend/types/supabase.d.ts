declare module '@supabase/supabase-js' {
  export interface User {
    id: string;
    email?: string;
    phone?: string;
    app_metadata: {
      provider?: string;
      providers?: string[];
    };
    user_metadata: {
      [key: string]: any;
    };
    aud: string;
    created_at: string;
  }

  export interface Session {
    provider_token?: string | null;
    access_token: string;
    expires_in?: number;
    expires_at?: number;
    refresh_token?: string;
    token_type: string;
    user: User;
  }

  export interface AuthResponse {
    data: {
      user: User | null;
      session: Session | null;
    };
    error: Error | null;
  }

  export interface AuthStateChangeEvent {
    SIGNED_IN: string;
    SIGNED_OUT: string;
    USER_UPDATED: string;
    USER_DELETED: string;
    PASSWORD_RECOVERY: string;
  }

  export interface SupabaseClient {
    auth: {
      getSession(): Promise<AuthResponse>;
      onAuthStateChange(
        callback: (event: AuthStateChangeEvent, session: Session | null) => void
      ): { data: { subscription: { unsubscribe: () => void } } };
    };
    from(table: string): any;
  }

  export function createClient(
    supabaseUrl: string,
    supabaseKey: string,
    options?: any
  ): SupabaseClient;
}
