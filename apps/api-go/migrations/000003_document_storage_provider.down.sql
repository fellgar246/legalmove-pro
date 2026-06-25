ALTER TABLE documents
    DROP CONSTRAINT IF EXISTS documents_storage_provider_check;

ALTER TABLE documents
    DROP COLUMN IF EXISTS storage_key,
    DROP COLUMN IF EXISTS storage_provider;
