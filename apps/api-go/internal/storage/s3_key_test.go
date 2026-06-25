package storage

import (
	"strings"
	"testing"
	"time"

	"github.com/google/uuid"
)

func TestBuildS3ObjectKeyWithPrefix(t *testing.T) {
	t.Parallel()

	id := uuid.MustParse("11111111-1111-1111-1111-111111111111")
	now := time.Date(2026, 5, 30, 12, 0, 0, 0, time.UTC)

	got := BuildS3ObjectKey("dev", "ORIGINAL", id, "Contract Final.pdf", now)
	want := "dev/documents/original/2026/05/11111111-1111-1111-1111-111111111111-Contract_Final.pdf"
	if got != want {
		t.Fatalf("BuildS3ObjectKey() = %q, want %q", got, want)
	}
}

func TestBuildS3ObjectKeyWithoutPrefix(t *testing.T) {
	t.Parallel()

	id := uuid.MustParse("22222222-2222-2222-2222-222222222222")
	now := time.Date(2026, 1, 2, 0, 0, 0, 0, time.UTC)

	got := BuildS3ObjectKey("", "AMENDMENT", id, "../../secret.pdf", now)
	if !strings.HasPrefix(got, "documents/amendment/2026/01/22222222-2222-2222-2222-222222222222-") {
		t.Fatalf("unexpected key prefix: %q", got)
	}
	if strings.Contains(got, "..") {
		t.Fatalf("key must not contain traversal segments: %q", got)
	}
}

func TestSanitizeFilenameRemovesUnsafeCharacters(t *testing.T) {
	t.Parallel()

	got := sanitizeFilename(`../../my contract (v2).PDF`)
	wantSuffix := ".pdf"
	if !strings.HasSuffix(strings.ToLower(got), wantSuffix) {
		t.Fatalf("sanitizeFilename() = %q, want suffix %q", got, wantSuffix)
	}
	if strings.Contains(got, "..") || strings.Contains(got, "/") {
		t.Fatalf("sanitizeFilename() = %q contains path separators", got)
	}
}
