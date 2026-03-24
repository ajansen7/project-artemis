import { useState, useEffect } from 'react';
import type { JobStatus } from './types';
import { useJobs, useAllCounts } from './hooks/useJobs';
import { useCompanies } from './hooks/useCompanies';
import { Header } from './components/Header';
import { StatusFilter } from './components/StatusFilter';
import { JobTable } from './components/JobTable';
import { CompanySidebar } from './components/CompanySidebar';
import { NetworkingPanel } from './components/NetworkingPanel';
import { EngagementPanel } from './components/EngagementPanel';
import { BlogPanel } from './components/BlogPanel';
import { SchedulePanel } from './components/SchedulePanel';
import { TasksPanel } from './components/TasksPanel';

type View = 'pipeline' | 'networking' | 'engagement' | 'blog' | 'schedules';

const VALID_VIEWS: View[] = ['pipeline', 'networking', 'engagement', 'blog', 'schedules'];

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
  const [view, setView] = useState<View>(() => readLocalStorage('artemis:view', 'pipeline', VALID_VIEWS));
  const [statusFilter, setStatusFilter] = useState<JobStatus | 'all'>(() => readLocalStorage<JobStatus | 'all'>('artemis:statusFilter', 'all'));

  useEffect(() => { localStorage.setItem('artemis:view', view); }, [view]);
  useEffect(() => { localStorage.setItem('artemis:statusFilter', statusFilter); }, [statusFilter]);
  const { jobs, loading, updateStatus, deleteJob, refetch, sortMode, setSortMode, groupByCompany, setGroupByCompany, companyGroups } = useJobs(statusFilter);
  const allCounts = useAllCounts();
  const { companies, loading: companiesLoading } = useCompanies();

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
      <Header counts={allCounts} />
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
