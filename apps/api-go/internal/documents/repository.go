package documents

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"
)

type Repository struct {
	pool *pgxpool.Pool
}

func NewRepository(pool *pgxpool.Pool) *Repository {
	return &Repository{pool: pool}
}

func (r *Repository) Create(ctx context.Context, input CreateInput) (Document, error) {
	const query = `
		INSERT INTO documents (
			id, filename, original_filename, mime_type, file_size,
			storage_path, document_role, status
		) VALUES ($1, $2, $3, $4, $5, $6, $7, 'UPLOADED')
		RETURNING id, filename, original_filename, mime_type, file_size,
		          storage_path, document_role, status, created_at, updated_at`

	var doc Document
	err := r.pool.QueryRow(ctx, query,
		input.ID,
		input.Filename,
		input.OriginalFilename,
		input.MimeType,
		input.FileSize,
		input.StoragePath,
		string(input.DocumentRole),
	).Scan(
		&doc.ID,
		&doc.Filename,
		&doc.OriginalFilename,
		&doc.MimeType,
		&doc.FileSize,
		&doc.StoragePath,
		&doc.DocumentRole,
		&doc.Status,
		&doc.CreatedAt,
		&doc.UpdatedAt,
	)
	if err != nil {
		return Document{}, fmt.Errorf("insert document: %w", err)
	}

	return doc, nil
}
