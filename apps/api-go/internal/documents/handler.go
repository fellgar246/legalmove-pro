package documents

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/google/uuid"
)

const maxUploadSize = 20 << 20 // 20 MB

type Handler struct {
	repo       *Repository
	uploadsDir string
}

func NewHandler(repo *Repository, uploadsDir string) *Handler {
	return &Handler{
		repo:       repo,
		uploadsDir: uploadsDir,
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
	storagePath := filepath.Join(h.uploadsDir, storedName)

	dst, err := os.Create(storagePath)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to save file")
		return
	}

	fileSize, err := io.Copy(dst, file)
	dst.Close()
	if err != nil {
		os.Remove(storagePath)
		writeError(w, http.StatusInternalServerError, "failed to save file")
		return
	}

	mimeType := header.Header.Get("Content-Type")
	if mimeType == "" {
		mimeType = "application/octet-stream"
	}

	doc, err := h.repo.Create(r.Context(), CreateInput{
		ID:               id,
		Filename:         storedName,
		OriginalFilename: originalFilename,
		MimeType:         mimeType,
		FileSize:         fileSize,
		StoragePath:      storagePath,
		DocumentRole:     role,
	})
	if err != nil {
		os.Remove(storagePath)
		writeError(w, http.StatusInternalServerError, "failed to save document metadata")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(ToResponse(doc))
}
