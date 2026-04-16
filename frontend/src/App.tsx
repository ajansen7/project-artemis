import { useState, useEffect, useRef } from 'react';
import type { JobStatus } from './types';
import { useJobs, useAllCounts } from './hooks/useJobs';
import { useCompanies } from './hooks/useCompanies';
import { useEvents } from './hooks/useEvents';
import { Header } from './components/Header';
import { StatusFilter } from './components/StatusFilter';
import { JobTable } from './components/JobTable';
import { CompanySidebar } from './components/CompanySidebar';
import { NetworkingPanel } from './components/NetworkingPanel';
import { EngagementPanel } from './components/EngagementPanel';
import { BlogPanel } from './components/BlogPanel';
import { SchedulePanel } from './components/SchedulePanel';
import { TasksPanel } from './components/TasksPanel';
import { LoginPage } from './components/LoginPage';
import { PendingApproval } from './components/PendingApproval';
import { AdminPanel } from './components/AdminPanel';
import { useProfile } from './hooks/useProfile';
import { initAuth, onAuthStateChange, syncFromServerSession } from './lib/supabase';

type View = 'pipeline' | 'networking' | 'engagement' | 'blog' | 'schedules' | 'admin';

const VALID_VIEWS: View[] = ['pipeline', 'networking', 'engagement', 'blog', 'schedules', 'admin'];

function readLocalStorage<T>(key: string, fallback: T, valid?: T[]): T {
  try {
    const v = localStorage.getItem(key) as T;
    if (v === null) return fallback;
    if (valid && !valid.includes(v)) return fallback;
    return v;
  } catch {
    return fallback;
  }
}

function App() {
  const [session, setSession] = useState<any>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [view, setView] = useState<View>(() => readLocalStorage('artemis:view', 'pipeline', VALID_VIEWS));
  const [statusFilter, setStatusFilter] = useState<JobStatus | 'all'>(() => readLocalStorage<JobStatus | 'all'>('artemis:statusFilter', 'all'));
  const prevUserIdRef = useRef<string | null>(null);

  useEffect(() => {
    // Initialize auth state
    initAuth().then(async (sess) => {
      if (sess) {
        setSession(sess);
        prevUserIdRef.current = sess.user?.id || null;
      } else {
        // No browser session — try to pick up CLI session
        const cliSess = await syncFromServerSession();
        setSession(cliSess);
        prevUserIdRef.current = cliSess?.user?.id || null;
      }
      setAuthLoading(false);
    });

    // Subscribe to auth state changes
    const listener = onAuthStateChange((sess) => {
      const currentUserId = sess?.user?.id || null;
      const prevUserId = prevUserIdRef.current;

      // Detect user switch or logout: reload page for clean data fetch
      if (prevUserId && currentUserId && prevUserId !== currentUserId) {
        // User switched to a different account
        prevUserIdRef.current = currentUserId;
        window.location.reload();
      } else if (prevUserId && !currentUserId) {
        // User logged out
        window.location.reload();
      } else {
        // First login or session refresh with same user
        prevUserIdRef.current = currentUserId;
        setSession(sess);
      }
    });

    // Periodically check if CLI session has changed while browser is open
    const syncInterval = setInterval(async () => {
      const newSess = await syncFromServerSession(true);
      if (newSess && prevUserIdRef.current !== newSess.user?.id) {
        prevUserIdRef.current = newSess.user?.id || null;
        window.location.reload();
      }
    }, 5000); // Check every 5 seconds

    // Also check when page regains focus (user switches between windows)
    const handleFocus = async () => {
      const newSess = await syncFromServerSession(true);
      if (newSess && prevUserIdRef.current !== newSess.user?.id) {
        prevUserIdRef.current = newSess.user?.id || null;
        window.location.reload();
      }
    };
    window.addEventListener('focus', handleFocus);

    return () => {
      listener?.unsubscribe();
      clearInterval(syncInterval);
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  useEffect(() => { localStorage.setItem('artemis:view', view); }, [view]);
  useEffect(() => { localStorage.setItem('artemis:statusFilter', statusFilter); }, [statusFilter]);

  // Call all hooks unconditionally, at top level
  useEvents();
  const { jobs, loading, updateStatus, deleteJob, refetch, sortMode, setSortMode, groupByCompany, setGroupByCompany, companyGroups } = useJobs(statusFilter);
  const allCounts = useAllCounts();
  const { companies, loading: companiesLoading } = useCompanies();
  const { profile, loading: profileLoading } = useProfile();

  // If not authenticated, show login page
  if (authLoading || profileLoading) {
    return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>Loading...</div>;
  }

  if (!session) {
    return <LoginPage onLoginSuccess={() => {}} />;
  }

  // Gate: user must be approved
  if (profile && profile.status !== 'approved') {
    return (
      <PendingApproval
        email={profile.email}
        status={profile.status as 'pending' | 'blocked'}
        onSignOut={async () => {
          const { supabase } = await import('./lib/supabase');
          await supabase.auth.signOut();
          window.location.reload();
        }}
      />
    );
  }

  const handleStatusChange = async (jobId: string, status: JobStatus, notes?: string) => {
    const ok = await updateStatus(jobId, status, notes);
    if (ok) refetch();
  };

  const handleDelete = async (jobId: string) => {
    const ok = await deleteJob(jobId);
    if (ok) refetch();
  };

  return (
    <>
    <div className="app">
      <Header counts={allCounts} session={session} />
      <div className="app-body">
        <div className="main-content">
          <div className="view-tabs">
            <button
              className={`view-tab ${view === 'pipeline' ? 'active' : ''}`}
              onClick={() => setView('pipeline')}
            >
              Pipeline
            </button>
            <button
              className={`view-tab ${view === 'networking' ? 'active' : ''}`}
              onClick={() => setView('networking')}
            >
              Networking
            </button>
            <button
              className={`view-tab ${view === 'engagement' ? 'active' : ''}`}
              onClick={() => setView('engagement')}
            >
              Engagement
            </button>
            <button
              className={`view-tab ${view === 'blog' ? 'active' : ''}`}
              onClick={() => setView('blog')}
            >
              Blog
            </button>
            <button
              className={`view-tab ${view === 'schedules' ? 'active' : ''}`}
              onClick={() => setView('schedules')}
            >
              Schedules
            </button>
            {profile?.role === 'admin' && (
              <button
                className={`view-tab ${view === 'admin' ? 'active' : ''}`}
                onClick={() => setView('admin')}
              >
                Users
              </button>
            )}
          </div>

          {view === 'pipeline' ? (
            <>
              <StatusFilter
                active={statusFilter}
                counts={allCounts}
                onChange={setStatusFilter}
              />
              <JobTable
                jobs={jobs}
                loading={loading}
                onUpdateStatus={handleStatusChange}
                onDelete={handleDelete}
                onUpdate={refetch}
                sortMode={sortMode}
                onSortChange={setSortMode}
                groupByCompany={groupByCompany}
                onGroupByCompanyChange={setGroupByCompany}
                companyGroups={companyGroups}
              />
            </>
          ) : view === 'networking' ? (
            <NetworkingPanel />
          ) : view === 'engagement' ? (
            <EngagementPanel />
          ) : view === 'blog' ? (
            <BlogPanel />
          ) : view === 'admin' ? (
            <AdminPanel />
          ) : (
            <SchedulePanel />
          )}
        </div>
        <CompanySidebar
          companies={companies}
          loading={companiesLoading}
        />
      </div>
    </div>
    <TasksPanel />
    </>
  );
}

export default App;
