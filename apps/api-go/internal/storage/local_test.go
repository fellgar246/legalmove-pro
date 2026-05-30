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
		Key:              "test-object.pdf",
		Body:             strings.NewReader("contract-content"),
		OriginalFilename: "original.pdf",
		ContentType:      "application/pdf",
	}

	saved, err := svc.Save(context.Background(), input)
	if err != nil {
		t.Fatalf("Save() error = %v", err)
	}

	if saved.Provider != ProviderLocal {
		t.Fatalf("Provider = %q, want %q", saved.Provider, ProviderLocal)
	}
	if saved.Key != input.Key {
		t.Fatalf("Key = %q, want %q", saved.Key, input.Key)
	}
	wantPath := filepath.Join(tempDir, "test-object.pdf")
	if saved.StoragePath != wantPath {
		t.Fatalf("StoragePath = %q, want %q", saved.StoragePath, wantPath)
	}
	if saved.Size != int64(len("contract-content")) {
		t.Fatalf("Size = %d, want %d", saved.Size, len("contract-content"))
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
		Key:  "../escape.txt",
		Body: strings.NewReader("x"),
	})
	if err == nil {
		t.Fatalf("Save() should reject traversal keys")
	}
}
