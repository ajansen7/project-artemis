import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import { API_BASE } from '../lib/api';
import type { BlogPost, BlogPostStatus } from '../types';

export function useBlogPosts() {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    try {
      const { data, error: err } = await supabase
        .from('blog_posts')
        .select('*')
        .order('created_at', { ascending: false });

      if (err) throw err;
      setPosts(data || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch blog posts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  useEffect(() => {
    const channel = supabase
      .channel('blog-realtime')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'blog_posts' }, () => { fetchPosts(); })
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, [fetchPosts]);

  const updateStatus = useCallback(async (id: string, status: BlogPostStatus) => {
    if (status === 'published') return false; // published is managed by the blogger skill only
    const { error: err } = await supabase
      .from('blog_posts')
      .update({ status })
      .eq('id', id);

    if (err) {
      setError(err.message);
      return false;
    }

    setPosts(prev => prev.map(p => p.id === id ? { ...p, status } : p));
    return true;
  }, []);

  const updatePost = useCallback(async (
    id: string,
    updates: { content?: string; notes?: string; status?: BlogPostStatus }
  ) => {
    const res = await fetch(`${API_BASE}/api/blog-posts/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Save failed' }));
      setError(err.detail || 'Save failed');
      return false;
    }
    setPosts(prev => prev.map(p => p.id === id ? { ...p, ...updates } : p));
    return true;
  }, []);

  const counts = {
    total: posts.length,
    ideas: posts.filter(p => p.status === 'idea').length,
    drafts: posts.filter(p => p.status === 'draft').length,
    inReview: posts.filter(p => p.status === 'review').length,
    published: posts.filter(p => p.status === 'published').length,
  };

  return { posts, counts, loading, error, updateStatus, updatePost, refetch: fetchPosts };
}
