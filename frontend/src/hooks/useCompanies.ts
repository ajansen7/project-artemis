import { useState, useEffect } from 'react';
import { supabase, getCurrentUserId } from '../lib/supabase';
import type { Company } from '../types';

export function useCompanies() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetch() {
      const userId = await getCurrentUserId();
      let query = supabase
        .from('companies')
        .select('id, name, domain, careers_url, is_target, why_target, scout_priority, last_scouted_at')
        .eq('is_target', true);

      // Filter by current user (RLS will also enforce this)
      if (userId) {
        query = query.eq('user_id', userId);
      }

      query = query.order('scout_priority');

      const { data } = await query;

      setCompanies(data || []);
      setLoading(false);
    }
    fetch();
  }, []);

  return { companies, loading };
}
