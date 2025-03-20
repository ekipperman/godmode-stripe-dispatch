import { useCallback } from 'react';
import { 
  supabaseClient,
  TableName,
  TableRow,
  TableInsert,
  TableUpdate,
  SupabaseResponse,
  SupabaseQueryOptions,
  SupabaseSubscriptionFilter,
  SupabaseSubscriptionPayload
} from '../lib/supabase-client';

export function useSupabase() {
  // Auth operations
  const getSession = useCallback(async () => {
    return await supabaseClient.auth.getSession();
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    return await supabaseClient.auth.signInWithPassword({ email, password });
  }, []);

  const signUp = useCallback(async (email: string, password: string) => {
    return await supabaseClient.auth.signUp({ email, password });
  }, []);

  const signOut = useCallback(async () => {
    return await supabaseClient.auth.signOut();
  }, []);

  // Database operations
  const insert = useCallback(async <T extends TableName>(
    table: T,
    data: TableInsert<T>
  ): Promise<SupabaseResponse<TableRow<T>>> => {
    const { data: result, error } = await supabaseClient
      .from(table)
      .insert(data)
      .select()
      .single();

    return {
      data: result,
      error
    };
  }, []);

  const update = useCallback(async <T extends TableName>(
    table: T,
    id: string,
    data: TableUpdate<T>
  ): Promise<SupabaseResponse<TableRow<T>>> => {
    const { data: result, error } = await supabaseClient
      .from(table)
      .update(data)
      .eq('id', id)
      .select()
      .single();

    return {
      data: result,
      error
    };
  }, []);

  const remove = useCallback(async <T extends TableName>(
    table: T,
    id: string
  ): Promise<SupabaseResponse<null>> => {
    const { error } = await supabaseClient
      .from(table)
      .delete()
      .eq('id', id);

    return {
      data: null,
      error
    };
  }, []);

  const select = useCallback(async <T extends TableName>(
    table: T,
    options: SupabaseQueryOptions = {}
  ): Promise<SupabaseResponse<TableRow<T>[]>> => {
    let query = supabaseClient
      .from(table)
      .select(options.columns || '*');

    if (options.filters) {
      Object.entries(options.filters).forEach(([key, value]) => {
        query = query.eq(key, value);
      });
    }

    if (options.order) {
      query = query.order(
        options.order.column,
        { ascending: options.order.ascending }
      );
    }

    if (options.limit) {
      query = query.limit(options.limit);
    }

    const { data, error } = await query;

    return {
      data,
      error
    };
  }, []);

  // Real-time subscriptions
  const subscribe = useCallback(<T extends TableName>(
    table: T,
    callback: (payload: SupabaseSubscriptionPayload<TableRow<T>>) => void,
    filter?: SupabaseSubscriptionFilter
  ) => {
    const subscription = supabaseClient
      .channel(`public:${table}`)
      .on(
        'postgres_changes',
        {
          event: filter?.event || '*',
          schema: 'public',
          table: table,
          filter: filter?.filter
        },
        (payload) => callback(payload as SupabaseSubscriptionPayload<TableRow<T>>)
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  return {
    auth: supabaseClient.auth,
    getSession,
    signIn,
    signUp,
    signOut,
    insert,
    update,
    remove,
    select,
    subscribe
  };
}

export default useSupabase;
