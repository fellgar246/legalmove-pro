package storage

import (
	"strings"
	"testing"
)

func TestParseStorageProvider(t *testing.T) {
	t.Parallel()

	tests := []struct {
		raw     string
		want    StorageProvider
		wantErr bool
	}{
		{raw: "", want: StorageProviderLocal},
		{raw: "local", want: StorageProviderLocal},
		{raw: " LOCAL ", want: StorageProviderLocal},
		{raw: "s3", want: StorageProviderS3},
		{raw: "S3", want: StorageProviderS3},
		{raw: "gcs", wantErr: true},
	}

	for _, tt := range tests {
		got, err := ParseStorageProvider(tt.raw)
		if tt.wantErr {
			if err == nil {
				t.Fatalf("ParseStorageProvider(%q) expected error", tt.raw)
			}
			continue
		}
		if err != nil {
			t.Fatalf("ParseStorageProvider(%q) error = %v", tt.raw, err)
		}
		if got != tt.want {
			t.Fatalf("ParseStorageProvider(%q) = %q, want %q", tt.raw, got, tt.want)
		}
	}
}

func TestNewServiceLocal(t *testing.T) {
	t.Parallel()

	svc, err := NewService(StorageProviderLocal, t.TempDir())
	if err != nil {
		t.Fatalf("NewService(local) error = %v", err)
	}
	if svc == nil {
		t.Fatal("NewService(local) returned nil service")
	}
}

func TestNewServiceS3ReturnsNotImplemented(t *testing.T) {
	t.Parallel()

	_, err := NewService(StorageProviderS3, t.TempDir())
	if err == nil {
		t.Fatal("NewService(s3) expected error")
	}
	if !strings.Contains(err.Error(), "not implemented") {
		t.Fatalf("NewService(s3) error = %v, want not implemented message", err)
	}
}

func TestNewServiceUnsupportedProvider(t *testing.T) {
	t.Parallel()

	_, err := NewService(StorageProvider("invalid"), t.TempDir())
	if err == nil {
		t.Fatal("NewService(invalid) expected error")
	}
}
