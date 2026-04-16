import { useState, useEffect, useCallback } from 'react';
import { supabase, getCurrentUserId } from '../lib/supabase';
import type { Contact, OutreachStatus, InteractionType } from '../types';

export function useContacts() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchContacts = useCallback(async () => {
    setLoading(true);
    try {
      const userId = await getCurrentUserId();
      let query = supabase
        .from('contacts')
        .select(`
          *,
          companies(name),
          contact_job_links(job_id, jobs(title, companies(name))),
          contact_interactions(id, interaction_type, notes, occurred_at, created_at)
        `);

      // Filter by current user (RLS will also enforce this)
      if (userId) {
        query = query.eq('user_id', userId);
      }

      const { data, error: err } = await query
        .order('priority', { ascending: true, nullsFirst: false })
        .order('created_at', { ascending: false });

      if (err) throw err;

      // Sort interactions within each contact by most recent first
      const withSortedInteractions = (data || []).map((c: Contact) => ({
        ...c,
        contact_interactions: [...(c.contact_interactions || [])].sort(
          (a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime()
        ),
      }));

      setContacts(withSortedInteractions);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch contacts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  useEffect(() => {
    const channel = supabase
      .channel('contacts-realtime')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'contacts' }, () => { fetchContacts(); })
      .on('postgres_changes', { event: '*', schema: 'public', table: 'contact_interactions' }, () => { fetchContacts(); })
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, [fetchContacts]);

  const updateOutreachStatus = useCallback(async (contactId: string, status: OutreachStatus) => {
    const updateData: Record<string, unknown> = { outreach_status: status };
    if (status === 'sent' || status === 'connected' || status === 'responded') {
      updateData.last_contacted_at = new Date().toISOString();
    }

    const { error: err } = await supabase
      .from('contacts')
      .update(updateData)
      .eq('id', contactId);

    if (err) {
      setError(err.message);
      return false;
    }

    setContacts(prev =>
      prev.map(c => c.id === contactId ? { ...c, outreach_status: status } : c)
    );
    return true;
  }, []);

  const logInteraction = useCallback(async (
    contactId: string,
    interactionType: InteractionType,
    notes?: string
  ) => {
    const { data, error: err } = await supabase
      .from('contact_interactions')
      .insert({ contact_id: contactId, interaction_type: interactionType, notes: notes || null })
      .select()
      .single();

    if (err) {
      setError(err.message);
      return false;
    }

    setContacts(prev =>
      prev.map(c =>
        c.id === contactId
          ? { ...c, contact_interactions: [data, ...(c.contact_interactions || [])] }
          : c
      )
    );
    return true;
  }, []);

  // Group contacts by company name
  const byCompany = contacts.reduce<Record<string, Contact[]>>((acc, c) => {
    const company = c.companies?.name ?? 'Unknown';
    if (!acc[company]) acc[company] = [];
    acc[company].push(c);
    return acc;
  }, {});

  const counts = {
    total: contacts.length,
    personal: contacts.filter(c => c.is_personal_connection).length,
    active: contacts.filter(c =>
      ['sent', 'connected', 'responded', 'meeting_scheduled', 'warm'].includes(c.outreach_status)
    ).length,
  };

  return { contacts, byCompany, counts, loading, error, updateOutreachStatus, logInteraction, refetch: fetchContacts };
}
