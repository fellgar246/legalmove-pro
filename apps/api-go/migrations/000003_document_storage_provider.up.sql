ALTER TABLE documents
    ADD COLUMN storage_provider TEXT NOT NULL DEFAULT 'local',
    ADD COLUMN storage_key TEXT;

UPDATE documents
SET storage_key = filename
WHERE storage_key IS NULL;

ALTER TABLE documents
    ALTER COLUMN storage_key SET NOT NULL;

ALTER TABLE documents
    ADD CONSTRAINT documents_storage_provider_check
        CHECK (storage_provider IN ('local', 's3'));
