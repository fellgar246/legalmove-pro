ALTER TABLE detected_changes
    ADD COLUMN impact_explanation TEXT,
    ADD COLUMN confidence TEXT,
    ADD COLUMN evidence JSONB;
