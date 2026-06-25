package documents

import (
	"context"
	"encoding/json"
	"net/http"
	"path/filepath"
	"strings"

	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/storage"
	"github.com/google/uuid"
)

const maxUploadSize = 20 << 20 // 20 MB

type Handler struct {
	repo    documentCreator
	storage storage.StorageService
}

type documentCreator interface {
	Create(ctx context.Context, input CreateInput) (Document, error)
}

func NewHandler(repo documentCreator, storageService storage.StorageService) *Handler {
	return &Handler{
		repo:    repo,
		storage: storageService,
	}
}

type errorResponse struct {
	Error string `json:"error"`
}

func writeError(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(errorResponse{Error: msg})
}

func persistStorageFields(saved storage.StoredObject) (storagePath, storageProvider, storageKey, filename string) {
	storageProvider = string(saved.Provider)
	storageKey = saved.Key
	filename = saved.Key

	switch saved.Provider {
	case storage.StorageProviderLocal:
		storagePath = saved.LocalPath
	default:
		storagePath = saved.Key
	}

	return storagePath, storageProvider, storageKey, filename
}

func (h *Handler) Upload(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(maxUploadSize); err != nil {
		if err.Error() == "http: request body too large" {
			writeError(w, http.StatusRequestEntityTooLarge, "file exceeds maximum size of 20MB")
			return
		}
		writeError(w, http.StatusBadRequest, "invalid multipart form")
		return
	}

	roleStr := strings.TrimSpace(r.FormValue("document_role"))
	if roleStr == "" {
		writeError(w, http.StatusBadRequest, "document_role is required")
		return
	}

	role := DocumentRole(roleStr)
	if !role.Valid() {
		writeError(w, http.StatusBadRequest, "document_role must be ORIGINAL or AMENDMENT")
		return
	}

	file, header, err := r.FormFile("file")
	if err != nil {
		writeError(w, http.StatusBadRequest, "file is required")
		return
	}
	defer file.Close()

	originalFilename := strings.TrimSpace(header.Filename)
	if originalFilename == "" {
		writeError(w, http.StatusBadRequest, "filename is required")
		return
	}

	id := uuid.New()
	storedName := id.String() + filepath.Ext(originalFilename)
	savedObject, err := h.storage.Save(r.Context(), storage.SaveObjectInput{
		Key:          storedName,
		Reader:       file,
		OriginalName: originalFilename,
		ContentType:  header.Header.Get("Content-Type"),
		SizeBytes:    header.Size,
		DocumentKind: string(role),
	})
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to save file")
		return
	}

	mimeType := header.Header.Get("Content-Type")
	if mimeType == "" {
		mimeType = "application/octet-stream"
	}

	storagePath, storageProvider, storageKey, filename := persistStorageFields(*savedObject)
	fileSize := savedObject.SizeBytes
	if fileSize <= 0 {
		fileSize = header.Size
	}

	doc, err := h.repo.Create(r.Context(), CreateInput{
		ID:               id,
		Filename:         filename,
		OriginalFilename: originalFilename,
		MimeType:         mimeType,
		FileSize:         fileSize,
		StoragePath:      storagePath,
		StorageProvider:  storageProvider,
		StorageKey:       storageKey,
		DocumentRole:     role,
	})
	if err != nil {
		_ = h.storage.Delete(r.Context(), savedObject.Key)
		writeError(w, http.StatusInternalServerError, "failed to save document metadata")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(ToResponse(doc))
}
