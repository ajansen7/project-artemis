"use client";

import { useState } from "react";
import AddJobForm from "@/components/AddJobForm";
import KanbanBoard from "@/components/KanbanBoard";
import { Compass } from "lucide-react";

export default function Home() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleJobAdded = () => {
    // Force the Kanban board to refresh its data
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <main className="min-h-screen bg-background flex flex-col p-6 lg:p-10 max-w-screen-2xl mx-auto space-y-8">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-border">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
            <Compass className="w-8 h-8 text-primary" />
            Project Artemis
          </h1>
          <p className="text-muted-foreground mt-2 max-w-xl">
            AI-orchestrated job hunt and career coaching command center.
          </p>
        </div>

        <AddJobForm onJobAdded={handleJobAdded} />
      </header>

      {/* Kanban Board Area */}
      <section className="flex-1 min-h-0 overflow-hidden">
        <KanbanBoard refreshTrigger={refreshTrigger} />
      </section>
    </main>
  );
}
