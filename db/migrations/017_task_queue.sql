-- Migration 017: Task queue for unified orchestrator
-- Replaces in-memory TaskManager. The orchestrator polls this table
-- for queued work; the API inserts rows instead of spawning tmux windows.

CREATE TABLE task_queue (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    skill           TEXT NOT NULL,               -- skill command (e.g. 'scout', 'inbox')
    skill_args      TEXT,                        -- optional args passed to the skill
    source          TEXT NOT NULL DEFAULT 'api', -- api, telegram, schedule, cli
    status          TEXT NOT NULL DEFAULT 'queued', -- queued, running, complete, failed
    schedule_id     UUID REFERENCES scheduled_jobs(id) ON DELETE SET NULL,
    output_summary  TEXT,                        -- summary written by orchestrator on completion
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ
);

CREATE INDEX idx_task_queue_status ON task_queue(status);
CREATE INDEX idx_task_queue_created ON task_queue(created_at);
