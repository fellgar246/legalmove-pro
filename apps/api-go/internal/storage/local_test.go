package storage

import (
	"context"
	"io"
	"path/filepath"
	"strings"
	"testing"
)

func TestLocalStorageSaveOpenDeleteRoundTrip(t *testing.T) {
	t.Parallel()

	tempDir := t.TempDir()
	svc := NewLocalStorageService(tempDir)

	input := SaveObjectInput{
		Key:          "test-object.pdf",
		Reader:       strings.NewReader("contract-content"),
		OriginalName: "original.pdf",
		ContentType:  "application/pdf",
	}

	saved, err := svc.Save(context.Background(), input)
	if err != nil {
		t.Fatalf("Save() error = %v", err)
	}

	if saved.Provider != StorageProviderLocal {
		t.Fatalf("Provider = %q, want %q", saved.Provider, StorageProviderLocal)
	}
	if saved.Key != input.Key {
		t.Fatalf("Key = %q, want %q", saved.Key, input.Key)
	}
	wantPath := filepath.Join(tempDir, "test-object.pdf")
	if saved.LocalPath != wantPath {
		t.Fatalf("LocalPath = %q, want %q", saved.LocalPath, wantPath)
	}
	if saved.SizeBytes != int64(len("contract-content")) {
		t.Fatalf("SizeBytes = %d, want %d", saved.SizeBytes, len("contract-content"))
	}

	rc, err := svc.Open(context.Background(), input.Key)
	if err != nil {
		t.Fatalf("Open() error = %v", err)
	}
	defer rc.Close()

	raw, err := io.ReadAll(rc)
	if err != nil {
		t.Fatalf("ReadAll() error = %v", err)
	}
	if string(raw) != "contract-content" {
		t.Fatalf("content = %q, want %q", string(raw), "contract-content")
	}

	if err := svc.Delete(context.Background(), input.Key); err != nil {
		t.Fatalf("Delete() error = %v", err)
	}

	if _, err := svc.Open(context.Background(), input.Key); err == nil {
		t.Fatalf("Open() after delete should fail")
	}
}

func TestLocalStorageRejectsPathTraversalKey(t *testing.T) {
	t.Parallel()

	tempDir := t.TempDir()
	svc := NewLocalStorageService(tempDir)

	_, err := svc.Save(context.Background(), SaveObjectInput{
		Key:    "../escape.txt",
		Reader: strings.NewReader("x"),
	})
	if err == nil {
		t.Fatalf("Save() should reject traversal keys")
	}
}

func TestLocalStorageRejectsAbsoluteKey(t *testing.T) {
	t.Parallel()

	tempDir := t.TempDir()
	svc := NewLocalStorageService(tempDir)

	_, err := svc.Save(context.Background(), SaveObjectInput{
		Key:    "/etc/passwd",
		Reader: strings.NewReader("x"),
	})
	if err == nil {
		t.Fatalf("Save() should reject absolute keys")
	}
}

func TestLocalStorageRejectsEmptyKey(t *testing.T) {
	t.Parallel()

	tempDir := t.TempDir()
	svc := NewLocalStorageService(tempDir)

	_, err := svc.Save(context.Background(), SaveObjectInput{
		Key:    "   ",
		Reader: strings.NewReader("x"),
	})
	if err == nil {
		t.Fatalf("Save() should reject empty keys")
	}
}
