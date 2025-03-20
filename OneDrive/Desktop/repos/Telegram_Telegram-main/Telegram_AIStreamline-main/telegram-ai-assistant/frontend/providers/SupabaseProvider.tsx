import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { Session } from '@supabase/supabase-js';
import { useSupabase } from '../hooks/useSupabase';

interface SupabaseContextType {
  session: Session | null;
  loading: boolean;
}

const SupabaseContext = createContext<SupabaseContextType>({
  session: null,
  loading: true
});

export const useSupabaseContext = () => {
  const context = useContext(SupabaseContext);
  if (!context) {
    throw new Error('useSupabaseContext must be used within a SupabaseProvider');
  }
  return context;
};

export const SupabaseProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { getSession, auth } = useSupabase();

  useEffect(() => {
    // Check active sessions and sets the user
    const initSession = async () => {
      try {
        const { data: { session: currentSession } } = await getSession();
        setSession(currentSession);
      } catch (error) {
        console.error('Error fetching session:', error);
      } finally {
        setLoading(false);
      }
    };

    initSession();

    // Listen for changes on auth state
    const {
      data: { subscription },
    } = auth.onAuthStateChange(async (_event, session) => {
      setSession(session);
      setLoading(false);

      // Handle authentication state changes
      if (!session && !loading) {
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
  }, [auth, getSession, loading, router]);

  return (
    <SupabaseContext.Provider value={{ session, loading }}>
      {children}
    </SupabaseContext.Provider>
  );
};

export default SupabaseProvider;
