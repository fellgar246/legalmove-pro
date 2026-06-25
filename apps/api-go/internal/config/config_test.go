package config

import (
	"strings"
	"testing"

	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/queue"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/storage"
)

func setRequiredEnv(t *testing.T) {
	t.Helper()
	t.Setenv("API_PORT", "8080")
	t.Setenv("DATABASE_URL", "postgres://legalmove:legalmove@localhost:5432/legalmove?sslmode=disable")
}

func TestLoadDefaultsToLocalProvider(t *testing.T) {
	setRequiredEnv(t)
	t.Setenv("STORAGE_PROVIDER", "")
	t.Setenv("UPLOADS_DIR", t.TempDir())

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if cfg.StorageProvider != storage.StorageProviderLocal {
		t.Fatalf("StorageProvider = %q, want local", cfg.StorageProvider)
	}
}

func TestLoadS3RequiresRegionAndBucket(t *testing.T) {
	setRequiredEnv(t)
	t.Setenv("STORAGE_PROVIDER", "s3")
	t.Setenv("AWS_REGION", "")
	t.Setenv("S3_BUCKET", "")

	_, err := Load()
	if err == nil {
		t.Fatal("Load() expected error for incomplete s3 config")
	}
	if !strings.Contains(err.Error(), "AWS_REGION") {
		t.Fatalf("error = %v", err)
	}

	t.Setenv("AWS_REGION", "us-east-1")
	_, err = Load()
	if err == nil {
		t.Fatal("Load() expected error for missing bucket")
	}
	if !strings.Contains(err.Error(), "S3_BUCKET") {
		t.Fatalf("error = %v", err)
	}
}

func TestLoadS3AllowsMissingUploadsDir(t *testing.T) {
	setRequiredEnv(t)
	t.Setenv("STORAGE_PROVIDER", "s3")
	t.Setenv("AWS_REGION", "us-east-1")
	t.Setenv("S3_BUCKET", "legalmove-pro-dev-documents")
	t.Setenv("UPLOADS_DIR", "")

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if cfg.S3Bucket != "legalmove-pro-dev-documents" {
		t.Fatalf("S3Bucket = %q", cfg.S3Bucket)
	}
	if cfg.UploadsDir == "" {
		t.Fatal("UploadsDir should fallback to temp dir")
	}
}

func TestLoadQueueDefaultsToPostgres(t *testing.T) {
	setRequiredEnv(t)
	t.Setenv("STORAGE_PROVIDER", "local")
	t.Setenv("UPLOADS_DIR", t.TempDir())
	t.Setenv("QUEUE_PROVIDER", "")

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if cfg.QueueProvider != queue.QueueProviderPostgres {
		t.Fatalf("QueueProvider = %q, want postgres", cfg.QueueProvider)
	}
}

func TestLoadSQSRequiresQueueURL(t *testing.T) {
	setRequiredEnv(t)
	t.Setenv("STORAGE_PROVIDER", "local")
	t.Setenv("UPLOADS_DIR", t.TempDir())
	t.Setenv("QUEUE_PROVIDER", "sqs")
	t.Setenv("AWS_REGION", "us-east-1")
	t.Setenv("SQS_QUEUE_URL", "")

	_, err := Load()
	if err == nil {
		t.Fatal("Load() expected error for missing SQS_QUEUE_URL")
	}
	if !strings.Contains(err.Error(), "SQS_QUEUE_URL") {
		t.Fatalf("error = %v", err)
	}
}
