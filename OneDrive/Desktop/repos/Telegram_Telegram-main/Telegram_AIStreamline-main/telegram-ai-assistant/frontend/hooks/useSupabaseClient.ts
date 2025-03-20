import { useCallback } from 'react';
import { supabase, Tables, TableRow, TableInsert, TableUpdate, SupabaseResponse } from '../lib/supabase';

export function useSupabaseClient() {
  // Auth operations
  const getSession = useCallback(async () => {
    return await supabase.auth.getSession();
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    return await supabase.auth.signInWithPassword({ email, password });
  }, []);

  const signUp = useCallback(async (email: string, password: string) => {
    return await supabase.auth.signUp({ email, password });
  }, []);

  const signOut = useCallback(async () => {
    return await supabase.auth.signOut();
  }, []);

  // Database operations
  const insert = useCallback(async <T extends keyof Tables>(
    table: T,
    data: TableInsert<T>
  ): Promise<SupabaseResponse<TableRow<T>>> => {
    const { data: result, error } = await supabase
      .from(table)
      .insert(data)
      .select()
      .single();

    return {
      data: result,
      error
    };
  }, []);

  const update = useCallback(async <T extends keyof Tables>(
    table: T,
    id: string,
    data: TableUpdate<T>
  ): Promise<SupabaseResponse<TableRow<T>>> => {
    const { data: result, error } = await supabase
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

  const remove = useCallback(async <T extends keyof Tables>(
    table: T,
    id: string
  ): Promise<SupabaseResponse<null>> => {
    const { error } = await supabase
      .from(table)
      .delete()
      .eq('id', id);

    return {
      data: null,
      error
    };
  }, []);

  const select = useCallback(async <T extends keyof Tables>(
    table: T,
    options: {
      columns?: string;
      filters?: Record<string, any>;
      limit?: number;
      order?: {
        column: string;
        ascending?: boolean;
      };
    } = {}
  ): Promise<SupabaseResponse<TableRow<T>[]>> => {
    let query = supabase
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
  const subscribe = useCallback(<T extends keyof Tables>(
    table: T,
    callback: (payload: {
      eventType: 'INSERT' | 'UPDATE' | 'DELETE';
      new: TableRow<T>;
      old: TableRow<T>;
    }) => void,
    filters?: {
      event?: 'INSERT' | 'UPDATE' | 'DELETE' | '*';
      filter?: string;
    }
  ) => {
    const channel = supabase
      .channel(`public:${table}`)
      .on(
        'postgres_changes',
        {
          event: filters?.event || '*',
          schema: 'public',
          table: table as string,
          filter: filters?.filter
        },
        callback
      )
      .subscribe();

    return () => {
      channel.unsubscribe();
    };
  }, []);

  return {
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

export default useSupabaseClient;
