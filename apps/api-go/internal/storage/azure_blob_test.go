package storage

import (
	"bytes"
	"context"
	"io"
	"strings"
	"testing"
	"time"

	"github.com/google/uuid"
)

type mockBlobClient struct {
	uploadBlob   func(ctx context.Context, containerName, blobName string, body io.Reader, contentType string, metadata map[string]string) error
	downloadBlob func(ctx context.Context, containerName, blobName string) (io.ReadCloser, error)
	deleteBlob   func(ctx context.Context, containerName, blobName string) error
}

func (m *mockBlobClient) UploadBlob(
	ctx context.Context,
	containerName, blobName string,
	body io.Reader,
	contentType string,
	metadata map[string]string,
) error {
	return m.uploadBlob(ctx, containerName, blobName, body, contentType, metadata)
}

func (m *mockBlobClient) DownloadBlob(ctx context.Context, containerName, blobName string) (io.ReadCloser, error) {
	return m.downloadBlob(ctx, containerName, blobName)
}

func (m *mockBlobClient) DeleteBlob(ctx context.Context, containerName, blobName string) error {
	return m.deleteBlob(ctx, containerName, blobName)
}

func TestAzureBlobStorageSaveUploadMetadata(t *testing.T) {
	t.Parallel()

	objectID := uuid.New()
	var capturedContainer string
	var capturedKey string
	var capturedMetadata map[string]string
	var capturedContentType string

	client := &mockBlobClient{
		uploadBlob: func(_ context.Context, containerName, blobName string, _ io.Reader, contentType string, metadata map[string]string) error {
			capturedContainer = containerName
			capturedKey = blobName
			capturedContentType = contentType
			capturedMetadata = metadata
			return nil
		},
	}

	svc := NewAzureBlobStorageService(client, "lmprodev0001", "documents")
	svc.now = func() time.Time { return time.Date(2026, 6, 25, 0, 0, 0, 0, time.UTC) }

	saved, err := svc.Save(context.Background(), SaveObjectInput{
		Key:          objectID.String() + ".pdf",
		Reader:       strings.NewReader("pdf-content"),
		OriginalName: "contract.pdf",
		ContentType:  "application/pdf",
		SizeBytes:    11,
		DocumentKind: "amendment",
	})
	if err != nil {
		t.Fatalf("Save() error = %v", err)
	}

	if capturedContainer != "documents" {
		t.Fatalf("container = %q, want documents", capturedContainer)
	}
	if !strings.HasPrefix(capturedKey, "documents/amendment/2026/06/") {
		t.Fatalf("unexpected captured key: %q", capturedKey)
	}
	if capturedMetadata["original_filename"] != "contract.pdf" {
		t.Fatalf("metadata original_filename = %q", capturedMetadata["original_filename"])
	}
	if capturedMetadata["document_kind"] != "amendment" {
		t.Fatalf("metadata document_kind = %q", capturedMetadata["document_kind"])
	}
	if capturedContentType != "application/pdf" {
		t.Fatalf("content type = %q", capturedContentType)
	}
	if saved.Provider != StorageProviderAzureBlob {
		t.Fatalf("Provider = %q, want azure_blob", saved.Provider)
	}
	if saved.Key != capturedKey {
		t.Fatalf("saved.Key = %q, capturedKey = %q", saved.Key, capturedKey)
	}
}

func TestAzureBlobStorageOpenAndDelete(t *testing.T) {
	t.Parallel()

	key := "documents/original/2026/06/test.pdf"
	deleted := false

	client := &mockBlobClient{
		downloadBlob: func(_ context.Context, containerName, blobName string) (io.ReadCloser, error) {
			if containerName != "documents" {
				t.Fatalf("container = %q", containerName)
			}
			if blobName != key {
				t.Fatalf("blob = %q, want %q", blobName, key)
			}
			return io.NopCloser(bytes.NewReader([]byte("bytes"))), nil
		},
		deleteBlob: func(_ context.Context, containerName, blobName string) error {
			if blobName != key {
				t.Fatalf("DeleteBlob blob = %q, want %q", blobName, key)
			}
			deleted = true
			return nil
		},
	}

	svc := NewAzureBlobStorageService(client, "account", "documents")

	rc, err := svc.Open(context.Background(), key)
	if err != nil {
		t.Fatalf("Open() error = %v", err)
	}
	raw, err := io.ReadAll(rc)
	_ = rc.Close()
	if err != nil {
		t.Fatalf("ReadAll() error = %v", err)
	}
	if string(raw) != "bytes" {
		t.Fatalf("content = %q", string(raw))
	}

	if err := svc.Delete(context.Background(), key); err != nil {
		t.Fatalf("Delete() error = %v", err)
	}
	if !deleted {
		t.Fatal("expected DeleteBlob to be called")
	}
}

func TestAzureBlobStorageRejectsTraversalKey(t *testing.T) {
	t.Parallel()

	svc := NewAzureBlobStorageService(&mockBlobClient{}, "account", "documents")
	if err := svc.Delete(context.Background(), "../escape.pdf"); err == nil {
		t.Fatal("Delete() should reject traversal keys")
	}
}
