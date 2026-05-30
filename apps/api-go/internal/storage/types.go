package storage

import (
	"context"
	"io"
)

type StorageProvider string

const (
	StorageProviderLocal StorageProvider = "local"
	StorageProviderS3    StorageProvider = "s3"
)

type SaveObjectInput struct {
	Key          string
	Reader       io.Reader
	OriginalName string
	ContentType  string
	SizeBytes    int64
	DocumentKind string
}

type StoredObject struct {
	Provider     StorageProvider
	Key          string
	LocalPath    string
	OriginalName string
	ContentType  string
	SizeBytes    int64
}

type StorageService interface {
	Save(ctx context.Context, input SaveObjectInput) (*StoredObject, error)
	Open(ctx context.Context, key string) (io.ReadCloser, error)
	Delete(ctx context.Context, key string) error
}
