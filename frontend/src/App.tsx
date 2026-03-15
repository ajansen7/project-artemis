import { useState } from 'react';
import type { JobStatus } from './types';
import { useJobs, useAllCounts } from './hooks/useJobs';
import { useCompanies } from './hooks/useCompanies';
import { Header } from './components/Header';
import { StatusFilter } from './components/StatusFilter';
import { JobTable } from './components/JobTable';
import { CompanySidebar } from './components/CompanySidebar';

function App() {
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
    <div className="app">
      <Header counts={allCounts} />
      <div className="app-body">
        <div className="main-content">
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
        </div>
        <CompanySidebar
          companies={companies}
          loading={companiesLoading}
        />
      </div>
    </div>
  );
}

export default App;
