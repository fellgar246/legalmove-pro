package analyses

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"

	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/documents"
	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
)

type Handler struct {
	repo *Repository
}

func NewHandler(repo *Repository) *Handler {
	return &Handler{repo: repo}
}

type errorResponse struct {
	Error string `json:"error"`
}

func writeError(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(errorResponse{Error: msg})
}

func (h *Handler) Create(w http.ResponseWriter, r *http.Request) {
	var req CreateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}

	if req.OriginalDocumentID == uuid.Nil {
		writeError(w, http.StatusBadRequest, "original_document_id is required")
		return
	}
	if req.AmendmentDocumentID == uuid.Nil {
		writeError(w, http.StatusBadRequest, "amendment_document_id is required")
		return
	}
	if req.OriginalDocumentID == req.AmendmentDocumentID {
		writeError(w, http.StatusBadRequest, "original and amendment documents must be different")
		return
	}

	originalRole, err := h.repo.GetDocumentRole(r.Context(), req.OriginalDocumentID)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeError(w, http.StatusBadRequest, "original document not found")
			return
		}
		writeError(w, http.StatusInternalServerError, "failed to validate original document")
		return
	}
	if originalRole != string(documents.RoleOriginal) {
		writeError(w, http.StatusBadRequest, "original_document_id must reference a document with role ORIGINAL")
		return
	}

	amendmentRole, err := h.repo.GetDocumentRole(r.Context(), req.AmendmentDocumentID)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeError(w, http.StatusBadRequest, "amendment document not found")
			return
		}
		writeError(w, http.StatusInternalServerError, "failed to validate amendment document")
		return
	}
	if amendmentRole != string(documents.RoleAmendment) {
		writeError(w, http.StatusBadRequest, "amendment_document_id must reference a document with role AMENDMENT")
		return
	}

	job, err := h.repo.Create(r.Context(), uuid.New(), req.OriginalDocumentID, req.AmendmentDocumentID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to create analysis job")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(ToCreateResponse(job))
}

func parseListParams(r *http.Request) (limit, offset int) {
	limit = 20
	offset = 0

	if raw := r.URL.Query().Get("limit"); raw != "" {
		if parsed, err := strconv.Atoi(raw); err == nil && parsed > 0 {
			limit = parsed
		}
	}
	if limit > 100 {
		limit = 100
	}

	if raw := r.URL.Query().Get("offset"); raw != "" {
		if parsed, err := strconv.Atoi(raw); err == nil && parsed >= 0 {
			offset = parsed
		}
	}

	return limit, offset
}

func (h *Handler) List(w http.ResponseWriter, r *http.Request) {
	limit, offset := parseListParams(r)

	jobs, err := h.repo.List(r.Context(), limit, offset)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to list analysis jobs")
		return
	}

	items := make([]AnalysisResponse, 0, len(jobs))
	for _, job := range jobs {
		items = append(items, ToAnalysisResponse(job))
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(ListResponse{
		Items:  items,
		Limit:  limit,
		Offset: offset,
	})
}

func (h *Handler) GetByID(w http.ResponseWriter, r *http.Request) {
	idStr := chi.URLParam(r, "id")
	id, err := uuid.Parse(idStr)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid analysis id")
		return
	}

	job, err := h.repo.GetByID(r.Context(), id)
	if err != nil {
		if errors.Is(err, ErrNotFound) {
			writeError(w, http.StatusNotFound, "analysis job not found")
			return
		}
		writeError(w, http.StatusInternalServerError, "failed to get analysis job")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(ToAnalysisResponse(job))
}

func (h *Handler) GetResult(w http.ResponseWriter, r *http.Request) {
	idStr := chi.URLParam(r, "id")
	id, err := uuid.Parse(idStr)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid analysis id")
		return
	}

	if _, err := h.repo.GetByID(r.Context(), id); err != nil {
		if errors.Is(err, ErrNotFound) {
			writeError(w, http.StatusNotFound, "analysis job not found")
			return
		}
		writeError(w, http.StatusInternalServerError, "failed to get analysis job")
		return
	}

	result, err := h.repo.GetResultByJobID(r.Context(), id)
	if err != nil {
		if errors.Is(err, ErrResultNotFound) {
			writeError(w, http.StatusNotFound, "analysis result not available yet")
			return
		}
		writeError(w, http.StatusInternalServerError, "failed to get analysis result")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(ToResultResponse(result))
}
