package analyses

import (
	"context"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

var (
	ErrNotFound       = errors.New("analysis job not found")
	ErrResultNotFound = errors.New("analysis result not found")
)

type Repository struct {
	pool *pgxpool.Pool
}

func NewRepository(pool *pgxpool.Pool) *Repository {
	return &Repository{pool: pool}
}

func (r *Repository) GetDocumentRole(ctx context.Context, id uuid.UUID) (string, error) {
	const query = `SELECT document_role FROM documents WHERE id = $1`

	var role string
	err := r.pool.QueryRow(ctx, query, id).Scan(&role)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return "", pgx.ErrNoRows
		}
		return "", fmt.Errorf("get document role: %w", err)
	}

	return role, nil
}

func scanAnalysisJob(row pgx.Row) (AnalysisJob, error) {
	var job AnalysisJob
	err := row.Scan(
		&job.ID,
		&job.OriginalDocumentID,
		&job.AmendmentDocumentID,
		&job.OriginalDocumentFilename,
		&job.AmendmentDocumentFilename,
		&job.Status,
		&job.ErrorMessage,
		&job.StartedAt,
		&job.CompletedAt,
		&job.CreatedAt,
		&job.UpdatedAt,
	)
	return job, err
}

const analysisJobSelect = `
	SELECT aj.id, aj.original_document_id, aj.amendment_document_id,
	       COALESCE(od.original_filename, '') AS original_document_filename,
	       COALESCE(ad.original_filename, '') AS amendment_document_filename,
	       aj.status, aj.error_message, aj.started_at, aj.completed_at,
	       aj.created_at, aj.updated_at
	FROM analysis_jobs aj
	LEFT JOIN documents od ON od.id = aj.original_document_id
	LEFT JOIN documents ad ON ad.id = aj.amendment_document_id`

func (r *Repository) Create(ctx context.Context, id, originalDocumentID, amendmentDocumentID uuid.UUID) (AnalysisJob, error) {
	const query = `
		INSERT INTO analysis_jobs (id, original_document_id, amendment_document_id, status)
		VALUES ($1, $2, $3, 'QUEUED')
		RETURNING id, original_document_id, amendment_document_id, status,
		          error_message, started_at, completed_at, created_at, updated_at`

	var job AnalysisJob
	err := r.pool.QueryRow(ctx, query, id, originalDocumentID, amendmentDocumentID).Scan(
		&job.ID,
		&job.OriginalDocumentID,
		&job.AmendmentDocumentID,
		&job.Status,
		&job.ErrorMessage,
		&job.StartedAt,
		&job.CompletedAt,
		&job.CreatedAt,
		&job.UpdatedAt,
	)
	if err != nil {
		return AnalysisJob{}, fmt.Errorf("insert analysis job: %w", err)
	}

	return job, nil
}

func (r *Repository) GetByID(ctx context.Context, id uuid.UUID) (AnalysisJob, error) {
	query := analysisJobSelect + `
		WHERE aj.id = $1`

	job, err := scanAnalysisJob(r.pool.QueryRow(ctx, query, id))
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return AnalysisJob{}, ErrNotFound
		}
		return AnalysisJob{}, fmt.Errorf("get analysis job: %w", err)
	}

	return job, nil
}

func (r *Repository) List(ctx context.Context, limit, offset int) ([]AnalysisJob, error) {
	query := analysisJobSelect + `
		ORDER BY aj.created_at DESC
		LIMIT $1 OFFSET $2`

	rows, err := r.pool.Query(ctx, query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("list analysis jobs: %w", err)
	}
	defer rows.Close()

	jobs := make([]AnalysisJob, 0, limit)
	for rows.Next() {
		job, err := scanAnalysisJob(rows)
		if err != nil {
			return nil, fmt.Errorf("scan analysis job: %w", err)
		}
		jobs = append(jobs, job)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate analysis jobs: %w", err)
	}

	return jobs, nil
}

func (r *Repository) GetResultByJobID(ctx context.Context, jobID uuid.UUID) (AnalysisResult, error) {
	const query = `
		SELECT id, analysis_job_id, result_json, schema_version, validation_status, created_at
		FROM analysis_results
		WHERE analysis_job_id = $1`

	var result AnalysisResult
	err := r.pool.QueryRow(ctx, query, jobID).Scan(
		&result.ID,
		&result.AnalysisJobID,
		&result.ResultJSON,
		&result.SchemaVersion,
		&result.ValidationStatus,
		&result.CreatedAt,
	)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return AnalysisResult{}, ErrResultNotFound
		}
		return AnalysisResult{}, fmt.Errorf("get analysis result: %w", err)
	}

	return result, nil
}
