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

	svc, err := NewService(ServiceConfig{
		Provider:   StorageProviderLocal,
		UploadsDir: t.TempDir(),
	})
	if err != nil {
		t.Fatalf("NewService(local) error = %v", err)
	}
	if svc == nil {
		t.Fatal("NewService(local) returned nil service")
	}
}

func TestNewServiceS3RequiresClientAndConfig(t *testing.T) {
	t.Parallel()

	_, err := NewService(ServiceConfig{
		Provider:  StorageProviderS3,
		AWSRegion: "us-east-1",
		S3Bucket:  "bucket",
	})
	if err == nil {
		t.Fatal("NewService(s3) without client expected error")
	}
	if !strings.Contains(err.Error(), "s3 client is required") {
		t.Fatalf("error = %v", err)
	}

	_, err = NewService(ServiceConfig{
		Provider: StorageProviderS3,
		S3Client: &mockS3Client{},
	})
	if err == nil {
		t.Fatal("NewService(s3) without region expected error")
	}
	if !strings.Contains(err.Error(), "AWS_REGION") {
		t.Fatalf("error = %v", err)
	}

	_, err = NewService(ServiceConfig{
		Provider:  StorageProviderS3,
		AWSRegion: "us-east-1",
		S3Client:  &mockS3Client{},
	})
	if err == nil {
		t.Fatal("NewService(s3) without bucket expected error")
	}
	if !strings.Contains(err.Error(), "S3_BUCKET") {
		t.Fatalf("error = %v", err)
	}
}

func TestNewServiceS3WithMockClient(t *testing.T) {
	t.Parallel()

	svc, err := NewService(ServiceConfig{
		Provider:  StorageProviderS3,
		AWSRegion: "us-east-1",
		S3Bucket:  "bucket",
		S3Prefix:  "dev",
		S3Client:  &mockS3Client{},
	})
	if err != nil {
		t.Fatalf("NewService(s3) error = %v", err)
	}
	if svc == nil {
		t.Fatal("NewService(s3) returned nil service")
	}
}

func TestNewServiceUnsupportedProvider(t *testing.T) {
	t.Parallel()

	_, err := NewService(ServiceConfig{
		Provider:   StorageProvider("invalid"),
		UploadsDir: t.TempDir(),
	})
	if err == nil {
		t.Fatal("NewService(invalid) expected error")
	}
}

func TestNewServiceLocalRequiresUploadsDir(t *testing.T) {
	t.Parallel()

	_, err := NewService(ServiceConfig{Provider: StorageProviderLocal})
	if err == nil {
		t.Fatal("expected error for missing uploads dir")
	}
	if !strings.Contains(err.Error(), "UPLOADS_DIR") {
		t.Fatalf("error = %v", err)
	}
}
