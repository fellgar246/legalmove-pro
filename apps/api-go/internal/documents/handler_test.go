package documents

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/storage"
	"github.com/google/uuid"
)

type stubRepo struct {
	createFn func(ctx context.Context, input CreateInput) (Document, error)
}

func (s *stubRepo) Create(ctx context.Context, input CreateInput) (Document, error) {
	if s.createFn == nil {
		return Document{}, errors.New("createFn not configured")
	}
	return s.createFn(ctx, input)
}

func buildMultipartUploadRequest(t *testing.T, role, filename string, content []byte) *http.Request {
	t.Helper()

	var body bytes.Buffer
	writer := multipart.NewWriter(&body)

	if err := writer.WriteField("document_role", role); err != nil {
		t.Fatalf("WriteField() error = %v", err)
	}
	part, err := writer.CreateFormFile("file", filename)
	if err != nil {
		t.Fatalf("CreateFormFile() error = %v", err)
	}
	if _, err := part.Write(content); err != nil {
		t.Fatalf("part.Write() error = %v", err)
	}
	if err := writer.Close(); err != nil {
		t.Fatalf("writer.Close() error = %v", err)
	}

	req := httptest.NewRequest(http.MethodPost, "/documents", &body)
	req.Header.Set("Content-Type", writer.FormDataContentType())
	return req
}

func TestUploadPersistsStoragePathCompatibleWithWorker(t *testing.T) {
	t.Parallel()

	uploadsDir := t.TempDir()
	storageSvc := storage.NewLocalStorageService(uploadsDir)

	var captured CreateInput
	repo := &stubRepo{
		createFn: func(_ context.Context, input CreateInput) (Document, error) {
			captured = input
			return Document{
				ID:               input.ID,
				Filename:         input.Filename,
				OriginalFilename: input.OriginalFilename,
				MimeType:         input.MimeType,
				FileSize:         input.FileSize,
				StoragePath:      input.StoragePath,
				DocumentRole:     input.DocumentRole,
				Status:           "UPLOADED",
				CreatedAt:        time.Now(),
			}, nil
		},
	}
	handler := NewHandler(repo, storageSvc)

	req := buildMultipartUploadRequest(t, "ORIGINAL", "contract.pdf", []byte("hello-contract"))
	rr := httptest.NewRecorder()
	handler.Upload(rr, req)

	if rr.Code != http.StatusCreated {
		t.Fatalf("status = %d, want %d, body=%s", rr.Code, http.StatusCreated, rr.Body.String())
	}

	if captured.OriginalFilename != "contract.pdf" {
		t.Fatalf("OriginalFilename = %q, want %q", captured.OriginalFilename, "contract.pdf")
	}
	if filepath.Ext(captured.Filename) != ".pdf" {
		t.Fatalf("Filename ext = %q, want .pdf", filepath.Ext(captured.Filename))
	}
	if captured.StoragePath != filepath.Join(uploadsDir, captured.Filename) {
		t.Fatalf(
			"StoragePath = %q, want %q",
			captured.StoragePath,
			filepath.Join(uploadsDir, captured.Filename),
		)
	}

	rawFile, err := os.ReadFile(captured.StoragePath)
	if err != nil {
		t.Fatalf("ReadFile(%q) error = %v", captured.StoragePath, err)
	}
	if string(rawFile) != "hello-contract" {
		t.Fatalf("stored file content = %q, want %q", string(rawFile), "hello-contract")
	}

	var resp DocumentResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &resp); err != nil {
		t.Fatalf("json.Unmarshal() error = %v", err)
	}
	if resp.DocumentRole != RoleOriginal {
		t.Fatalf("DocumentRole = %q, want %q", resp.DocumentRole, RoleOriginal)
	}
}

func TestUploadDeletesFileWhenRepositoryFails(t *testing.T) {
	t.Parallel()

	uploadsDir := t.TempDir()
	storageSvc := storage.NewLocalStorageService(uploadsDir)

	repo := &stubRepo{
		createFn: func(_ context.Context, _ CreateInput) (Document, error) {
			return Document{}, errors.New("db insert failed")
		},
	}
	handler := NewHandler(repo, storageSvc)

	req := buildMultipartUploadRequest(t, "AMENDMENT", "amendment.png", []byte("amendment-content"))
	rr := httptest.NewRecorder()
	handler.Upload(rr, req)

	if rr.Code != http.StatusInternalServerError {
		t.Fatalf(
			"status = %d, want %d, body=%s",
			rr.Code,
			http.StatusInternalServerError,
			rr.Body.String(),
		)
	}

	entries, err := os.ReadDir(uploadsDir)
	if err != nil {
		t.Fatalf("ReadDir() error = %v", err)
	}
	if len(entries) != 0 {
		t.Fatalf("uploads dir should be empty after rollback, found %d files", len(entries))
	}
}

func TestUploadFailsWhenFileMissing(t *testing.T) {
	t.Parallel()

	uploadsDir := t.TempDir()
	storageSvc := storage.NewLocalStorageService(uploadsDir)

	repo := &stubRepo{
		createFn: func(_ context.Context, _ CreateInput) (Document, error) {
			t.Fatalf("repository should not be called")
			return Document{}, nil
		},
	}
	handler := NewHandler(repo, storageSvc)

	var body bytes.Buffer
	writer := multipart.NewWriter(&body)
	if err := writer.WriteField("document_role", "ORIGINAL"); err != nil {
		t.Fatalf("WriteField() error = %v", err)
	}
	if err := writer.Close(); err != nil {
		t.Fatalf("writer.Close() error = %v", err)
	}

	req := httptest.NewRequest(http.MethodPost, "/documents", &body)
	req.Header.Set("Content-Type", writer.FormDataContentType())
	rr := httptest.NewRecorder()
	handler.Upload(rr, req)

	if rr.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want %d", rr.Code, http.StatusBadRequest)
	}
}

func TestUploadGeneratesUUIDBasedFilename(t *testing.T) {
	t.Parallel()

	uploadsDir := t.TempDir()
	storageSvc := storage.NewLocalStorageService(uploadsDir)

	var captured CreateInput
	repo := &stubRepo{
		createFn: func(_ context.Context, input CreateInput) (Document, error) {
			captured = input
			return Document{
				ID:               input.ID,
				Filename:         input.Filename,
				OriginalFilename: input.OriginalFilename,
				MimeType:         input.MimeType,
				FileSize:         input.FileSize,
				StoragePath:      input.StoragePath,
				DocumentRole:     input.DocumentRole,
				Status:           "UPLOADED",
				CreatedAt:        time.Now(),
			}, nil
		},
	}
	handler := NewHandler(repo, storageSvc)

	req := buildMultipartUploadRequest(t, "ORIGINAL", "contract.jpeg", []byte("bytes"))
	rr := httptest.NewRecorder()
	handler.Upload(rr, req)

	if rr.Code != http.StatusCreated {
		t.Fatalf("status = %d, want %d", rr.Code, http.StatusCreated)
	}

	base := captured.Filename[:len(captured.Filename)-len(filepath.Ext(captured.Filename))]
	if _, err := uuid.Parse(base); err != nil {
		t.Fatalf("filename stem should be UUID, got %q (err=%v)", base, err)
	}
	if filepath.Ext(captured.Filename) != ".jpeg" {
		t.Fatalf("Filename ext = %q, want .jpeg", filepath.Ext(captured.Filename))
	}
}
