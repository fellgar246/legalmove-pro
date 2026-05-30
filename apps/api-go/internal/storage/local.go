package storage

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

type LocalStorageService struct {
	uploadsDir string
}

func NewLocalStorageService(uploadsDir string) *LocalStorageService {
	return &LocalStorageService{uploadsDir: uploadsDir}
}

func (s *LocalStorageService) Save(ctx context.Context, input SaveObjectInput) (*StoredObject, error) {
	_ = ctx

	targetPath, err := s.resolveKeyPath(input.Key)
	if err != nil {
		return nil, err
	}

	dst, err := os.Create(targetPath)
	if err != nil {
		return nil, fmt.Errorf("create object %q: %w", input.Key, err)
	}

	size, copyErr := io.Copy(dst, input.Reader)
	closeErr := dst.Close()
	if copyErr != nil {
		_ = os.Remove(targetPath)
		return nil, fmt.Errorf("write object %q: %w", input.Key, copyErr)
	}
	if closeErr != nil {
		_ = os.Remove(targetPath)
		return nil, fmt.Errorf("close object %q: %w", input.Key, closeErr)
	}

	return &StoredObject{
		Provider:     StorageProviderLocal,
		Key:          input.Key,
		LocalPath:    targetPath,
		SizeBytes:    size,
		OriginalName: input.OriginalName,
		ContentType:  input.ContentType,
	}, nil
}

func (s *LocalStorageService) Open(ctx context.Context, key string) (io.ReadCloser, error) {
	_ = ctx

	targetPath, err := s.resolveKeyPath(key)
	if err != nil {
		return nil, err
	}

	f, err := os.Open(targetPath)
	if err != nil {
		return nil, fmt.Errorf("open object %q: %w", key, err)
	}
	return f, nil
}

func (s *LocalStorageService) Delete(ctx context.Context, key string) error {
	_ = ctx

	targetPath, err := s.resolveKeyPath(key)
	if err != nil {
		return err
	}
	if err := os.Remove(targetPath); err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return fmt.Errorf("delete object %q: %w", key, err)
	}
	return nil
}

func (s *LocalStorageService) resolveKeyPath(key string) (string, error) {
	if s.uploadsDir == "" {
		return "", fmt.Errorf("uploads directory is required")
	}

	trimmed := strings.TrimSpace(key)
	if trimmed == "" {
		return "", fmt.Errorf("object key is required")
	}
	if filepath.IsAbs(trimmed) {
		return "", fmt.Errorf("object key must be relative")
	}

	cleaned := filepath.Clean(trimmed)
	if cleaned == "." || strings.HasPrefix(cleaned, "..") {
		return "", fmt.Errorf("invalid object key %q", key)
	}

	return filepath.Join(s.uploadsDir, cleaned), nil
}
