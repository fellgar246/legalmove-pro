package analyses

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/google/uuid"
)

type stubDispatcher struct {
	dispatchFn func(ctx context.Context, analysisID uuid.UUID) error
}

func (s *stubDispatcher) DispatchAnalysisJob(ctx context.Context, analysisID uuid.UUID) error {
	if s.dispatchFn == nil {
		return errors.New("dispatchFn not configured")
	}
	return s.dispatchFn(ctx, analysisID)
}

type stubAnalysisRepo struct {
	getDocumentRoleFn   func(ctx context.Context, id uuid.UUID) (string, error)
	createFn            func(ctx context.Context, id, originalDocumentID, amendmentDocumentID uuid.UUID) (AnalysisJob, error)
	markFailedFn        func(ctx context.Context, id uuid.UUID, errorMessage string) error
	listFn              func(ctx context.Context, limit, offset int) ([]AnalysisJob, error)
	getByIDFn           func(ctx context.Context, id uuid.UUID) (AnalysisJob, error)
	getResultByJobIDFn  func(ctx context.Context, jobID uuid.UUID) (AnalysisResult, error)
}

func (s *stubAnalysisRepo) GetDocumentRole(ctx context.Context, id uuid.UUID) (string, error) {
	return s.getDocumentRoleFn(ctx, id)
}

func (s *stubAnalysisRepo) Create(ctx context.Context, id, originalDocumentID, amendmentDocumentID uuid.UUID) (AnalysisJob, error) {
	return s.createFn(ctx, id, originalDocumentID, amendmentDocumentID)
}

func (s *stubAnalysisRepo) MarkFailed(ctx context.Context, id uuid.UUID, errorMessage string) error {
	if s.markFailedFn == nil {
		return errors.New("markFailedFn not configured")
	}
	return s.markFailedFn(ctx, id, errorMessage)
}

func (s *stubAnalysisRepo) List(ctx context.Context, limit, offset int) ([]AnalysisJob, error) {
	if s.listFn == nil {
		return nil, errors.New("listFn not configured")
	}
	return s.listFn(ctx, limit, offset)
}

func (s *stubAnalysisRepo) GetByID(ctx context.Context, id uuid.UUID) (AnalysisJob, error) {
	if s.getByIDFn == nil {
		return AnalysisJob{}, errors.New("getByIDFn not configured")
	}
	return s.getByIDFn(ctx, id)
}

func (s *stubAnalysisRepo) GetResultByJobID(ctx context.Context, jobID uuid.UUID) (AnalysisResult, error) {
	if s.getResultByJobIDFn == nil {
		return AnalysisResult{}, errors.New("getResultByJobIDFn not configured")
	}
	return s.getResultByJobIDFn(ctx, jobID)
}

func buildCreateAnalysisRequest(t *testing.T, originalID, amendmentID uuid.UUID) *http.Request {
	t.Helper()

	body, err := json.Marshal(CreateRequest{
		OriginalDocumentID:  originalID,
		AmendmentDocumentID: amendmentID,
	})
	if err != nil {
		t.Fatalf("json.Marshal() error = %v", err)
	}

	req := httptest.NewRequest(http.MethodPost, "/analyses", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	return req
}

func TestCreateDispatchesJobAfterPersisting(t *testing.T) {
	t.Parallel()

	originalID := uuid.New()
	amendmentID := uuid.New()
	jobID := uuid.New()
	dispatched := false

	repo := &stubAnalysisRepo{
		getDocumentRoleFn: func(_ context.Context, id uuid.UUID) (string, error) {
			if id == originalID {
				return "ORIGINAL", nil
			}
			return "AMENDMENT", nil
		},
		createFn: func(_ context.Context, id, originalDocumentID, amendmentDocumentID uuid.UUID) (AnalysisJob, error) {
			return AnalysisJob{
				ID:                  jobID,
				OriginalDocumentID:  originalDocumentID,
				AmendmentDocumentID: amendmentDocumentID,
				Status:              StatusQueued,
				CreatedAt:           time.Now(),
			}, nil
		},
	}
	dispatcher := &stubDispatcher{
		dispatchFn: func(_ context.Context, analysisID uuid.UUID) error {
			if analysisID != jobID {
				t.Fatalf("analysisID = %s, want %s", analysisID, jobID)
			}
			dispatched = true
			return nil
		},
	}

	handler := &Handler{repo: repo, dispatcher: dispatcher}
	rec := httptest.NewRecorder()
	handler.Create(rec, buildCreateAnalysisRequest(t, originalID, amendmentID))

	if rec.Code != http.StatusCreated {
		t.Fatalf("status = %d, want %d, body=%s", rec.Code, http.StatusCreated, rec.Body.String())
	}
	if !dispatched {
		t.Fatal("expected dispatcher to be called")
	}
}

func TestCreateMarksFailedWhenDispatchFails(t *testing.T) {
	t.Parallel()

	originalID := uuid.New()
	amendmentID := uuid.New()
	jobID := uuid.New()
	markedFailed := false

	repo := &stubAnalysisRepo{
		getDocumentRoleFn: func(_ context.Context, id uuid.UUID) (string, error) {
			if id == originalID {
				return "ORIGINAL", nil
			}
			return "AMENDMENT", nil
		},
		createFn: func(_ context.Context, id, originalDocumentID, amendmentDocumentID uuid.UUID) (AnalysisJob, error) {
			return AnalysisJob{
				ID:                  jobID,
				OriginalDocumentID:  originalDocumentID,
				AmendmentDocumentID: amendmentDocumentID,
				Status:              StatusQueued,
				CreatedAt:           time.Now(),
			}, nil
		},
		markFailedFn: func(_ context.Context, id uuid.UUID, errorMessage string) error {
			if id != jobID {
				t.Fatalf("id = %s, want %s", id, jobID)
			}
			if errorMessage != enqueueFailureMessage {
				t.Fatalf("errorMessage = %q", errorMessage)
			}
			markedFailed = true
			return nil
		},
	}
	dispatcher := &stubDispatcher{
		dispatchFn: func(context.Context, uuid.UUID) error {
			return errors.New("sqs unavailable")
		},
	}

	handler := &Handler{repo: repo, dispatcher: dispatcher}
	rec := httptest.NewRecorder()
	handler.Create(rec, buildCreateAnalysisRequest(t, originalID, amendmentID))

	if rec.Code != http.StatusInternalServerError {
		t.Fatalf("status = %d, want %d, body=%s", rec.Code, http.StatusInternalServerError, rec.Body.String())
	}
	if !markedFailed {
		t.Fatal("expected MarkFailed to be called")
	}
}
