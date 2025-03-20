import { createContext, useContext, useEffect, useState } from 'react';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { useRouter } from 'next/router';

interface SupabaseContextType {
  supabase: SupabaseClient;
  user: any | null;
  loading: boolean;
}

const SupabaseContext = createContext<SupabaseContextType>({
  supabase: createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_KEY!
  ),
  user: null,
  loading: true,
});

export const useSupabase = () => {
  const context = useContext(SupabaseContext);
  if (!context) {
    throw new Error('useSupabase must be used within a SupabaseProvider');
  }
  return context;
};

export const SupabaseProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [supabase] = useState(() =>
    createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_KEY!
    )
  );
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check active sessions and sets the user
    const getSession = async () => {
      const { data: { session }, error } = await supabase.auth.getSession();
      setUser(session?.user ?? null);
      setLoading(false);

      if (error) {
        console.error('Error fetching session:', error.message);
      }
    };

    getSession();

    // Listen for changes on auth state
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      setUser(session?.user ?? null);
      setLoading(false);

      // Handle authentication state changes
      if (!session?.user && !loading) {
        // Redirect to login page if user is not authenticated
        const isAuthPage = router.pathname === '/login' || router.pathname === '/signup';
        if (!isAuthPage) {
          router.push('/login');
        }
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase, loading, router]);

  return (
    <SupabaseContext.Provider value={{ supabase, user, loading }}>
      {children}
    </SupabaseContext.Provider>
  );
};

export default SupabaseProvider;
