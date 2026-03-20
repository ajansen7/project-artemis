import { useState } from 'react';
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
import { TasksPanel } from './components/TasksPanel';

type View = 'pipeline' | 'networking' | 'engagement' | 'blog';

function App() {
  const [view, setView] = useState<View>('pipeline');
  const [statusFilter, setStatusFilter] = useState<JobStatus | 'all'>('all');
  const { jobs, loading, updateStatus, deleteJob, refetch } = useJobs(statusFilter);
  const allCounts = useAllCounts();
  const { companies, loading: companiesLoading } = useCompanies();

  const handleStatusChange = async (jobId: string, status: JobStatus) => {
    const ok = await updateStatus(jobId, status);
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
              />
            </>
          ) : view === 'networking' ? (
            <NetworkingPanel />
          ) : view === 'engagement' ? (
            <EngagementPanel />
          ) : (
            <BlogPanel />
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
