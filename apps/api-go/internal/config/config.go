package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/queue"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/storage"
	"github.com/joho/godotenv"
)

type Config struct {
	AppEnv             string
	APIPort            int
	CORSAllowedOrigins []string
	DatabaseURL        string
	UploadsDir      string
	StorageProvider storage.StorageProvider
	QueueProvider   queue.QueueProvider
	AWSRegion       string
	S3Bucket        string
	S3Prefix        string
	SQSQueueURL     string

	AzureStorageAccountName   string
	AzureStorageContainerName string
	AzureServiceBusNamespace  string
	AzureServiceBusQueueName  string
	AzureClientID             string
}

func Load() (Config, error) {
	_ = godotenv.Load("../../.env", ".env")

	storageProviderRaw := os.Getenv("STORAGE_PROVIDER")
	if strings.TrimSpace(storageProviderRaw) == "" {
		storageProviderRaw = "local"
	}
	storageProvider, err := storage.ParseStorageProvider(storageProviderRaw)
	if err != nil {
		return Config{}, err
	}

	queueProviderRaw := os.Getenv("QUEUE_PROVIDER")
	if strings.TrimSpace(queueProviderRaw) == "" {
		queueProviderRaw = "postgres"
	}
	queueProvider, err := queue.ParseQueueProvider(queueProviderRaw)
	if err != nil {
		return Config{}, err
	}

	cfg := Config{
		AppEnv:             os.Getenv("APP_ENV"),
		CORSAllowedOrigins: ParseCORSAllowedOrigins(os.Getenv("CORS_ALLOWED_ORIGINS")),
		DatabaseURL:        os.Getenv("DATABASE_URL"),
		UploadsDir:                os.Getenv("UPLOADS_DIR"),
		StorageProvider:           storageProvider,
		QueueProvider:             queueProvider,
		AWSRegion:                 strings.TrimSpace(os.Getenv("AWS_REGION")),
		S3Bucket:                  strings.TrimSpace(os.Getenv("S3_BUCKET")),
		S3Prefix:                  strings.Trim(strings.TrimSpace(os.Getenv("S3_PREFIX")), "/"),
		SQSQueueURL:               strings.TrimSpace(os.Getenv("SQS_QUEUE_URL")),
		AzureStorageAccountName:   strings.TrimSpace(os.Getenv("AZURE_STORAGE_ACCOUNT_NAME")),
		AzureStorageContainerName: strings.TrimSpace(os.Getenv("AZURE_STORAGE_CONTAINER_NAME")),
		AzureServiceBusNamespace:  strings.TrimSpace(os.Getenv("AZURE_SERVICE_BUS_NAMESPACE")),
		AzureServiceBusQueueName:  strings.TrimSpace(os.Getenv("AZURE_SERVICE_BUS_QUEUE_NAME")),
		AzureClientID:             strings.TrimSpace(os.Getenv("AZURE_CLIENT_ID")),
	}

	portStr := os.Getenv("API_PORT")
	if portStr == "" {
		return Config{}, fmt.Errorf("API_PORT is required")
	}
	port, err := strconv.Atoi(portStr)
	if err != nil {
		return Config{}, fmt.Errorf("API_PORT must be a valid integer: %w", err)
	}
	cfg.APIPort = port

	if cfg.DatabaseURL == "" {
		return Config{}, fmt.Errorf("DATABASE_URL is required")
	}
	if cfg.AppEnv == "" {
		cfg.AppEnv = "local"
	}

	switch cfg.StorageProvider {
	case storage.StorageProviderLocal:
		if cfg.UploadsDir == "" {
			return Config{}, fmt.Errorf("UPLOADS_DIR is required when STORAGE_PROVIDER=local")
		}
	case storage.StorageProviderS3:
		if cfg.AWSRegion == "" {
			return Config{}, fmt.Errorf("AWS_REGION is required when STORAGE_PROVIDER=s3")
		}
		if cfg.S3Bucket == "" {
			return Config{}, fmt.Errorf("S3_BUCKET is required when STORAGE_PROVIDER=s3")
		}
		if cfg.UploadsDir == "" {
			cfg.UploadsDir = os.TempDir()
		}
	case storage.StorageProviderAzureBlob:
		if cfg.AzureStorageAccountName == "" {
			return Config{}, fmt.Errorf("AZURE_STORAGE_ACCOUNT_NAME is required when STORAGE_PROVIDER=azure_blob")
		}
		if cfg.AzureStorageContainerName == "" {
			return Config{}, fmt.Errorf("AZURE_STORAGE_CONTAINER_NAME is required when STORAGE_PROVIDER=azure_blob")
		}
		if cfg.UploadsDir == "" {
			cfg.UploadsDir = os.TempDir()
		}
	default:
		return Config{}, fmt.Errorf("unsupported storage provider: %q", cfg.StorageProvider)
	}

	switch cfg.QueueProvider {
	case queue.QueueProviderPostgres:
		// No additional queue configuration required.
	case queue.QueueProviderSQS:
		if cfg.AWSRegion == "" {
			return Config{}, fmt.Errorf("AWS_REGION is required when QUEUE_PROVIDER=sqs")
		}
		if cfg.SQSQueueURL == "" {
			return Config{}, fmt.Errorf("SQS_QUEUE_URL is required when QUEUE_PROVIDER=sqs")
		}
	case queue.QueueProviderAzureServiceBus:
		if cfg.AzureServiceBusNamespace == "" {
			return Config{}, fmt.Errorf("AZURE_SERVICE_BUS_NAMESPACE is required when QUEUE_PROVIDER=azure_service_bus")
		}
		if cfg.AzureServiceBusQueueName == "" {
			return Config{}, fmt.Errorf("AZURE_SERVICE_BUS_QUEUE_NAME is required when QUEUE_PROVIDER=azure_service_bus")
		}
	default:
		return Config{}, fmt.Errorf("unsupported queue provider: %q", cfg.QueueProvider)
	}

	return cfg, nil
}

// ParseCORSAllowedOrigins reads a comma-separated list of browser origins.
// Defaults to the local Next.js dev server when unset or empty.
func ParseCORSAllowedOrigins(raw string) []string {
	const defaultOrigin = "http://localhost:3000"

	if strings.TrimSpace(raw) == "" {
		return []string{defaultOrigin}
	}

	parts := strings.Split(raw, ",")
	origins := make([]string, 0, len(parts))
	for _, part := range parts {
		origin := strings.TrimSpace(part)
		if origin != "" {
			origins = append(origins, origin)
		}
	}
	if len(origins) == 0 {
		return []string{defaultOrigin}
	}
	return origins
}
