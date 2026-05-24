package analyses

import (
	"encoding/json"
	"time"

	"github.com/google/uuid"
)

type JobStatus string

const (
	StatusQueued       JobStatus = "QUEUED"
	StatusProcessing   JobStatus = "PROCESSING"
	StatusCompleted    JobStatus = "COMPLETED"
	StatusFailed       JobStatus = "FAILED"
	StatusNeedsReview  JobStatus = "NEEDS_REVIEW"
)

type AnalysisJob struct {
	ID                    uuid.UUID
	OriginalDocumentID    uuid.UUID
	AmendmentDocumentID   uuid.UUID
	Status                JobStatus
	ErrorMessage          *string
	StartedAt             *time.Time
	CompletedAt           *time.Time
	CreatedAt             time.Time
	UpdatedAt             time.Time
}

type CreateRequest struct {
	OriginalDocumentID  uuid.UUID `json:"original_document_id"`
	AmendmentDocumentID uuid.UUID `json:"amendment_document_id"`
}

type CreateResponse struct {
	ID                    uuid.UUID `json:"id"`
	OriginalDocumentID    uuid.UUID `json:"original_document_id"`
	AmendmentDocumentID   uuid.UUID `json:"amendment_document_id"`
	Status                JobStatus `json:"status"`
	CreatedAt             time.Time `json:"created_at"`
}

type AnalysisResponse struct {
	ID                    uuid.UUID  `json:"id"`
	OriginalDocumentID    uuid.UUID  `json:"original_document_id"`
	AmendmentDocumentID   uuid.UUID  `json:"amendment_document_id"`
	Status                JobStatus  `json:"status"`
	ErrorMessage          *string    `json:"error_message"`
	StartedAt             *time.Time `json:"started_at"`
	CompletedAt           *time.Time `json:"completed_at"`
	CreatedAt             time.Time  `json:"created_at"`
	UpdatedAt             time.Time  `json:"updated_at"`
}

func ToCreateResponse(job AnalysisJob) CreateResponse {
	return CreateResponse{
		ID:                  job.ID,
		OriginalDocumentID:  job.OriginalDocumentID,
		AmendmentDocumentID: job.AmendmentDocumentID,
		Status:              job.Status,
		CreatedAt:           job.CreatedAt,
	}
}

func ToAnalysisResponse(job AnalysisJob) AnalysisResponse {
	return AnalysisResponse{
		ID:                  job.ID,
		OriginalDocumentID:  job.OriginalDocumentID,
		AmendmentDocumentID: job.AmendmentDocumentID,
		Status:              job.Status,
		ErrorMessage:        job.ErrorMessage,
		StartedAt:           job.StartedAt,
		CompletedAt:         job.CompletedAt,
		CreatedAt:           job.CreatedAt,
		UpdatedAt:           job.UpdatedAt,
	}
}

type AnalysisResult struct {
	ID               uuid.UUID
	AnalysisJobID    uuid.UUID
	ResultJSON       json.RawMessage
	SchemaVersion    string
	ValidationStatus string
	CreatedAt        time.Time
}

type ResultResponse struct {
	AnalysisJobID    uuid.UUID       `json:"analysis_job_id"`
	SchemaVersion    string          `json:"schema_version"`
	ValidationStatus string          `json:"validation_status"`
	CreatedAt        time.Time       `json:"created_at"`
	Result           json.RawMessage `json:"result"`
}

func ToResultResponse(result AnalysisResult) ResultResponse {
	return ResultResponse{
		AnalysisJobID:    result.AnalysisJobID,
		SchemaVersion:    result.SchemaVersion,
		ValidationStatus: result.ValidationStatus,
		CreatedAt:        result.CreatedAt,
		Result:           result.ResultJSON,
	}
}
