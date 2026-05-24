ALTER TABLE detected_changes
    DROP COLUMN IF EXISTS evidence,
    DROP COLUMN IF EXISTS confidence,
    DROP COLUMN IF EXISTS impact_explanation;
