package documents

import (
	"time"

	"github.com/google/uuid"
)

type DocumentRole string

const (
	RoleOriginal  DocumentRole = "ORIGINAL"
	RoleAmendment DocumentRole = "AMENDMENT"
)

func (r DocumentRole) Valid() bool {
	return r == RoleOriginal || r == RoleAmendment
}

type Document struct {
	ID               uuid.UUID
	Filename         string
	OriginalFilename string
	MimeType         string
	FileSize         int64
	StoragePath      string
	StorageProvider  string
	StorageKey       string
	DocumentRole     DocumentRole
	Status           string
	CreatedAt        time.Time
	UpdatedAt        time.Time
}

type CreateInput struct {
	ID               uuid.UUID
	Filename         string
	OriginalFilename string
	MimeType         string
	FileSize         int64
	StoragePath      string
	StorageProvider  string
	StorageKey       string
	DocumentRole     DocumentRole
}

type DocumentResponse struct {
	ID               uuid.UUID    `json:"id"`
	Filename         string       `json:"filename"`
	OriginalFilename string       `json:"original_filename"`
	MimeType         string       `json:"mime_type"`
	FileSize         int64        `json:"file_size"`
	DocumentRole     DocumentRole `json:"document_role"`
	Status           string       `json:"status"`
	CreatedAt        time.Time    `json:"created_at"`
}

func ToResponse(d Document) DocumentResponse {
	return DocumentResponse{
		ID:               d.ID,
		Filename:         d.Filename,
		OriginalFilename: d.OriginalFilename,
		MimeType:         d.MimeType,
		FileSize:         d.FileSize,
		DocumentRole:     d.DocumentRole,
		Status:           d.Status,
		CreatedAt:        d.CreatedAt,
	}
}
