CREATE TABLE documents (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    storage_path TEXT NOT NULL,
    document_role TEXT NOT NULL CHECK (document_role IN ('ORIGINAL', 'AMENDMENT')),
    status TEXT NOT NULL DEFAULT 'UPLOADED',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY,
    original_document_id UUID NOT NULL REFERENCES documents(id),
    amendment_document_id UUID NOT NULL REFERENCES documents(id),
    status TEXT NOT NULL DEFAULT 'QUEUED',
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE analysis_results (
    id UUID PRIMARY KEY,
    analysis_job_id UUID NOT NULL REFERENCES analysis_jobs(id),
    result_json JSONB NOT NULL,
    schema_version TEXT NOT NULL DEFAULT '1.0',
    validation_status TEXT NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE detected_changes (
    id UUID PRIMARY KEY,
    analysis_job_id UUID NOT NULL REFERENCES analysis_jobs(id),
    change_type TEXT NOT NULL,
    legal_topic TEXT,
    section_reference TEXT,
    before_text TEXT,
    after_text TEXT,
    summary TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    requires_human_review BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX idx_analysis_results_analysis_job_id ON analysis_results(analysis_job_id);
CREATE INDEX idx_detected_changes_analysis_job_id ON detected_changes(analysis_job_id);
