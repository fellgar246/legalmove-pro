package storage

import (
	"context"
	"fmt"
	"io"
	"strings"
	"time"
)

type blobAPI interface {
	UploadBlob(
		ctx context.Context,
		containerName string,
		blobName string,
		body io.Reader,
		contentType string,
		metadata map[string]string,
	) error
	DownloadBlob(ctx context.Context, containerName string, blobName string) (io.ReadCloser, error)
	DeleteBlob(ctx context.Context, containerName string, blobName string) error
}

type AzureBlobStorageService struct {
	client        blobAPI
	accountName   string
	containerName string
	now           func() time.Time
}

func NewAzureBlobStorageService(client blobAPI, accountName, containerName string) *AzureBlobStorageService {
	return &AzureBlobStorageService{
		client:        client,
		accountName:   strings.TrimSpace(accountName),
		containerName: strings.TrimSpace(containerName),
		now:           time.Now,
	}
}

func (s *AzureBlobStorageService) Save(ctx context.Context, input SaveObjectInput) (*StoredObject, error) {
	if s.client == nil {
		return nil, fmt.Errorf("azure blob client is required")
	}
	if s.accountName == "" {
		return nil, fmt.Errorf("AZURE_STORAGE_ACCOUNT_NAME is required")
	}
	if s.containerName == "" {
		return nil, fmt.Errorf("AZURE_STORAGE_CONTAINER_NAME is required")
	}

	objectID, err := objectIDFromKey(input.Key)
	if err != nil {
		return nil, fmt.Errorf("resolve object id: %w", err)
	}

	objectKey := BuildS3ObjectKey("", input.DocumentKind, objectID, input.OriginalName, s.now())
	contentType := strings.TrimSpace(input.ContentType)
	if contentType == "" {
		contentType = "application/octet-stream"
	}

	metadata := map[string]string{
		"original-filename": input.OriginalName,
		"document-kind":     normalizeDocumentKind(input.DocumentKind),
	}
	if input.SizeBytes > 0 {
		metadata["size-bytes"] = fmt.Sprintf("%d", input.SizeBytes)
	}

	if err := s.client.UploadBlob(ctx, s.containerName, objectKey, input.Reader, contentType, metadata); err != nil {
		return nil, fmt.Errorf("save object %q: %w", objectKey, err)
	}

	sizeBytes := input.SizeBytes
	if sizeBytes <= 0 {
		sizeBytes = 0
	}

	return &StoredObject{
		Provider:     StorageProviderAzureBlob,
		Key:          objectKey,
		LocalPath:    "",
		SizeBytes:    sizeBytes,
		OriginalName: input.OriginalName,
		ContentType:  contentType,
	}, nil
}

func (s *AzureBlobStorageService) Open(ctx context.Context, key string) (io.ReadCloser, error) {
	if s.client == nil {
		return nil, fmt.Errorf("azure blob client is required")
	}
	if s.containerName == "" {
		return nil, fmt.Errorf("AZURE_STORAGE_CONTAINER_NAME is required")
	}

	objectKey, err := s.resolveObjectKey(key)
	if err != nil {
		return nil, err
	}

	rc, err := s.client.DownloadBlob(ctx, s.containerName, objectKey)
	if err != nil {
		return nil, fmt.Errorf("open object %q: %w", objectKey, err)
	}
	if rc == nil {
		return nil, fmt.Errorf("open object %q: empty response body", objectKey)
	}
	return rc, nil
}

func (s *AzureBlobStorageService) Delete(ctx context.Context, key string) error {
	if s.client == nil {
		return fmt.Errorf("azure blob client is required")
	}
	if s.containerName == "" {
		return fmt.Errorf("AZURE_STORAGE_CONTAINER_NAME is required")
	}

	objectKey, err := s.resolveObjectKey(key)
	if err != nil {
		return err
	}

	if err := s.client.DeleteBlob(ctx, s.containerName, objectKey); err != nil {
		return fmt.Errorf("delete object %q: %w", objectKey, err)
	}
	return nil
}

func (s *AzureBlobStorageService) resolveObjectKey(key string) (string, error) {
	trimmed := strings.TrimSpace(key)
	if trimmed == "" {
		return "", fmt.Errorf("object key is required")
	}
	if strings.Contains(trimmed, "..") {
		return "", fmt.Errorf("invalid object key %q", key)
	}
	return trimmed, nil
}
