ALTER TABLE documents
    DROP CONSTRAINT IF EXISTS documents_storage_provider_check;

ALTER TABLE documents
    ADD CONSTRAINT documents_storage_provider_check
        CHECK (storage_provider IN ('local', 's3'));
