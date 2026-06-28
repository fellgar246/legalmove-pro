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

func TestLoadAzureBlobRequiresStorageConfig(t *testing.T) {
	setRequiredEnv(t)
	t.Setenv("STORAGE_PROVIDER", "azure_blob")
	t.Setenv("AZURE_STORAGE_ACCOUNT_NAME", "")
	t.Setenv("AZURE_STORAGE_CONTAINER_NAME", "")

	_, err := Load()
	if err == nil {
		t.Fatal("Load() expected error for missing AZURE_STORAGE_ACCOUNT_NAME")
	}
	if !strings.Contains(err.Error(), "AZURE_STORAGE_ACCOUNT_NAME") {
		t.Fatalf("error = %v", err)
	}

	t.Setenv("AZURE_STORAGE_ACCOUNT_NAME", "lmprodev0001")
	_, err = Load()
	if err == nil {
		t.Fatal("Load() expected error for missing AZURE_STORAGE_CONTAINER_NAME")
	}
	if !strings.Contains(err.Error(), "AZURE_STORAGE_CONTAINER_NAME") {
		t.Fatalf("error = %v", err)
	}
}

func TestParseCORSAllowedOriginsDefaultsToLocalhost(t *testing.T) {
	origins := ParseCORSAllowedOrigins("")
	if len(origins) != 1 || origins[0] != "http://localhost:3000" {
		t.Fatalf("ParseCORSAllowedOrigins(\"\") = %v", origins)
	}
}

func TestParseCORSAllowedOriginsSplitsCommaSeparatedValues(t *testing.T) {
	origins := ParseCORSAllowedOrigins("http://localhost:3000, https://app.example.com , ")
	if len(origins) != 2 {
		t.Fatalf("len(origins) = %d, want 2", len(origins))
	}
	if origins[0] != "http://localhost:3000" || origins[1] != "https://app.example.com" {
		t.Fatalf("origins = %v", origins)
	}
}

func TestLoadIncludesCORSAllowedOrigins(t *testing.T) {
	setRequiredEnv(t)
	t.Setenv("STORAGE_PROVIDER", "local")
	t.Setenv("UPLOADS_DIR", t.TempDir())
	t.Setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,https://demo.legalmove.example")

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if len(cfg.CORSAllowedOrigins) != 2 {
		t.Fatalf("CORSAllowedOrigins = %v", cfg.CORSAllowedOrigins)
	}
}

func TestLoadAzureServiceBusRequiresQueueConfig(t *testing.T) {
	setRequiredEnv(t)
	t.Setenv("STORAGE_PROVIDER", "local")
	t.Setenv("UPLOADS_DIR", t.TempDir())
	t.Setenv("QUEUE_PROVIDER", "azure_service_bus")
	t.Setenv("AZURE_SERVICE_BUS_NAMESPACE", "")
	t.Setenv("AZURE_SERVICE_BUS_QUEUE_NAME", "")

	_, err := Load()
	if err == nil {
		t.Fatal("Load() expected error for missing AZURE_SERVICE_BUS_NAMESPACE")
	}
	if !strings.Contains(err.Error(), "AZURE_SERVICE_BUS_NAMESPACE") {
		t.Fatalf("error = %v", err)
	}

	t.Setenv("AZURE_SERVICE_BUS_NAMESPACE", "sb-lmpro-dev")
	_, err = Load()
	if err == nil {
		t.Fatal("Load() expected error for missing AZURE_SERVICE_BUS_QUEUE_NAME")
	}
	if !strings.Contains(err.Error(), "AZURE_SERVICE_BUS_QUEUE_NAME") {
		t.Fatalf("error = %v", err)
	}
}
