package storage

import (
	"bytes"
	"context"
	"io"
	"strings"
	"testing"
	"time"

	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/google/uuid"
)

type mockS3Client struct {
	putObject    func(ctx context.Context, params *s3.PutObjectInput, optFns ...func(*s3.Options)) (*s3.PutObjectOutput, error)
	getObject    func(ctx context.Context, params *s3.GetObjectInput, optFns ...func(*s3.Options)) (*s3.GetObjectOutput, error)
	deleteObject func(ctx context.Context, params *s3.DeleteObjectInput, optFns ...func(*s3.Options)) (*s3.DeleteObjectOutput, error)
}

func (m *mockS3Client) PutObject(ctx context.Context, params *s3.PutObjectInput, optFns ...func(*s3.Options)) (*s3.PutObjectOutput, error) {
	return m.putObject(ctx, params, optFns...)
}

func (m *mockS3Client) GetObject(ctx context.Context, params *s3.GetObjectInput, optFns ...func(*s3.Options)) (*s3.GetObjectOutput, error) {
	return m.getObject(ctx, params, optFns...)
}

func (m *mockS3Client) DeleteObject(ctx context.Context, params *s3.DeleteObjectInput, optFns ...func(*s3.Options)) (*s3.DeleteObjectOutput, error) {
	return m.deleteObject(ctx, params, optFns...)
}

func TestS3StorageSavePutObjectMetadata(t *testing.T) {
	t.Parallel()

	objectID := uuid.New()
	var capturedKey string
	var capturedMetadata map[string]string
	var capturedContentType *string

	client := &mockS3Client{
		putObject: func(_ context.Context, params *s3.PutObjectInput, _ ...func(*s3.Options)) (*s3.PutObjectOutput, error) {
			capturedKey = *params.Key
			capturedMetadata = params.Metadata
			capturedContentType = params.ContentType
			return &s3.PutObjectOutput{}, nil
		},
	}

	svc := NewS3StorageService(client, "legalmove-pro-dev-documents", "dev")
	svc.now = func() time.Time { return time.Date(2026, 5, 30, 0, 0, 0, 0, time.UTC) }

	saved, err := svc.Save(context.Background(), SaveObjectInput{
		Key:          objectID.String() + ".pdf",
		Reader:       strings.NewReader("pdf-content"),
		OriginalName: "contract.pdf",
		ContentType:  "application/pdf",
		SizeBytes:    11,
		DocumentKind: "ORIGINAL",
	})
	if err != nil {
		t.Fatalf("Save() error = %v", err)
	}

	if saved.Provider != StorageProviderS3 {
		t.Fatalf("Provider = %q, want %q", saved.Provider, StorageProviderS3)
	}
	if saved.LocalPath != "" {
		t.Fatalf("LocalPath = %q, want empty", saved.LocalPath)
	}
	if !strings.HasPrefix(capturedKey, "dev/documents/original/2026/05/") {
		t.Fatalf("unexpected captured key: %q", capturedKey)
	}
	if capturedMetadata["original-filename"] != "contract.pdf" {
		t.Fatalf("metadata original-filename = %q", capturedMetadata["original-filename"])
	}
	if capturedMetadata["document-kind"] != "original" {
		t.Fatalf("metadata document-kind = %q", capturedMetadata["document-kind"])
	}
	if capturedContentType == nil || *capturedContentType != "application/pdf" {
		t.Fatalf("content type = %v", capturedContentType)
	}
	if saved.Key != capturedKey {
		t.Fatalf("saved.Key = %q, capturedKey = %q", saved.Key, capturedKey)
	}
}

func TestS3StorageOpenAndDelete(t *testing.T) {
	t.Parallel()

	key := "dev/documents/original/2026/05/test.pdf"
	deleted := false

	client := &mockS3Client{
		getObject: func(_ context.Context, params *s3.GetObjectInput, _ ...func(*s3.Options)) (*s3.GetObjectOutput, error) {
			if *params.Key != key {
				t.Fatalf("GetObject key = %q, want %q", *params.Key, key)
			}
			return &s3.GetObjectOutput{Body: io.NopCloser(bytes.NewReader([]byte("bytes")))}, nil
		},
		deleteObject: func(_ context.Context, params *s3.DeleteObjectInput, _ ...func(*s3.Options)) (*s3.DeleteObjectOutput, error) {
			if *params.Key != key {
				t.Fatalf("DeleteObject key = %q, want %q", *params.Key, key)
			}
			deleted = true
			return &s3.DeleteObjectOutput{}, nil
		},
	}

	svc := NewS3StorageService(client, "bucket", "dev")

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
		t.Fatal("expected DeleteObject to be called")
	}
}

func TestS3StorageRejectsTraversalKeyOnDelete(t *testing.T) {
	t.Parallel()

	svc := NewS3StorageService(&mockS3Client{}, "bucket", "dev")
	if err := svc.Delete(context.Background(), "../escape.pdf"); err == nil {
		t.Fatal("Delete() should reject traversal keys")
	}
}
