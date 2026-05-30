package storage

import (
	"context"
	"io"
)

type StorageProvider string

const (
	ProviderLocal StorageProvider = "local"
	ProviderS3    StorageProvider = "s3"
)

type SaveObjectInput struct {
	Key              string
	Body             io.Reader
	OriginalFilename string
	ContentType      string
}

type StoredObject struct {
	Provider         StorageProvider
	Key              string
	StoragePath      string
	Size             int64
	OriginalFilename string
	ContentType      string
}

type StorageService interface {
	Save(ctx context.Context, input SaveObjectInput) (*StoredObject, error)
	Open(ctx context.Context, key string) (io.ReadCloser, error)
	Delete(ctx context.Context, key string) error
}
