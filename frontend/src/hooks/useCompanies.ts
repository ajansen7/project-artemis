import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import type { Company } from '../types';

export function useCompanies() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetch() {
      const { data } = await supabase
        .from('companies')
        .select('id, name, domain, careers_url, is_target, why_target, scout_priority, last_scouted_at')
        .eq('is_target', true)
        .order('scout_priority');
      
      setCompanies(data || []);
      setLoading(false);
    }
    fetch();
  }, []);

  return { companies, loading };
}
