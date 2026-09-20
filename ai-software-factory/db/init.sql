CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS workflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), trace_id TEXT UNIQUE NOT NULL,
  source_issue_key TEXT NOT NULL, story_issue_key TEXT, ux_issue_key TEXT,
  status TEXT NOT NULL DEFAULT 'QUEUED', source_revision TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_workflow_source_revision ON workflows(source_issue_key, source_revision) WHERE source_revision IS NOT NULL;
CREATE TABLE IF NOT EXISTS executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  agent_id TEXT NOT NULL, status TEXT NOT NULL, input_summary TEXT, output_summary TEXT, error TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(), finished_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  issue_key TEXT NOT NULL, asked_by TEXT NOT NULL, requested_agent TEXT, question TEXT NOT NULL,
  blocking BOOLEAN NOT NULL DEFAULT true, status TEXT NOT NULL DEFAULT 'OPEN', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  answered_by TEXT NOT NULL, answer TEXT NOT NULL, confidence NUMERIC(4,3), created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  issue_key TEXT NOT NULL, decision TEXT NOT NULL, rationale TEXT, source_question_id UUID REFERENCES questions(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS evidence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  issue_key TEXT NOT NULL, source_type TEXT NOT NULL, source_ref TEXT NOT NULL, excerpt TEXT, valid_as_of DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  issue_key TEXT NOT NULL, kind TEXT NOT NULL, path TEXT NOT NULL, checksum TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), event_key TEXT UNIQUE NOT NULL, event_type TEXT NOT NULL,
  issue_key TEXT, payload JSONB NOT NULL DEFAULT '{}'::jsonb, processed_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
