package storage

import (
	"fmt"
	"strings"

	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type ServiceConfig struct {
	Provider   StorageProvider
	UploadsDir string
	AWSRegion  string
	S3Bucket   string
	S3Prefix   string
	S3Client   s3API

	AzureStorageAccountName  string
	AzureStorageContainerName string
	AzureBlobClient          blobAPI
}

func ParseStorageProvider(raw string) (StorageProvider, error) {
	switch strings.ToLower(strings.TrimSpace(raw)) {
	case "", "local":
		return StorageProviderLocal, nil
	case "s3":
		return StorageProviderS3, nil
	case "azure_blob":
		return StorageProviderAzureBlob, nil
	default:
		return "", fmt.Errorf("unsupported storage provider: %q", raw)
	}
}

func NewService(cfg ServiceConfig) (StorageService, error) {
	switch cfg.Provider {
	case StorageProviderLocal:
		if strings.TrimSpace(cfg.UploadsDir) == "" {
			return nil, fmt.Errorf("UPLOADS_DIR is required when STORAGE_PROVIDER=local")
		}
		return NewLocalStorageService(cfg.UploadsDir), nil
	case StorageProviderS3:
		if strings.TrimSpace(cfg.AWSRegion) == "" {
			return nil, fmt.Errorf("AWS_REGION is required when STORAGE_PROVIDER=s3")
		}
		if strings.TrimSpace(cfg.S3Bucket) == "" {
			return nil, fmt.Errorf("S3_BUCKET is required when STORAGE_PROVIDER=s3")
		}
		client := cfg.S3Client
		if client == nil {
			return nil, fmt.Errorf("s3 client is required when STORAGE_PROVIDER=s3")
		}
		return NewS3StorageService(client, cfg.S3Bucket, cfg.S3Prefix), nil
	case StorageProviderAzureBlob:
		if strings.TrimSpace(cfg.AzureStorageAccountName) == "" {
			return nil, fmt.Errorf("AZURE_STORAGE_ACCOUNT_NAME is required when STORAGE_PROVIDER=azure_blob")
		}
		if strings.TrimSpace(cfg.AzureStorageContainerName) == "" {
			return nil, fmt.Errorf("AZURE_STORAGE_CONTAINER_NAME is required when STORAGE_PROVIDER=azure_blob")
		}
		if cfg.AzureBlobClient == nil {
			return nil, fmt.Errorf("azure blob client is required when STORAGE_PROVIDER=azure_blob")
		}
		return NewAzureBlobStorageService(
			cfg.AzureBlobClient,
			cfg.AzureStorageAccountName,
			cfg.AzureStorageContainerName,
		), nil
	default:
		return nil, fmt.Errorf("unsupported storage provider: %q", cfg.Provider)
	}
}

// NewS3Client wraps the AWS SDK client for injection from main.
func NewS3Client(client *s3.Client) s3API {
	return client
}
