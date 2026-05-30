package storage

import (
	"fmt"
	"strings"
)

func ParseStorageProvider(raw string) (StorageProvider, error) {
	switch strings.ToLower(strings.TrimSpace(raw)) {
	case "", "local":
		return StorageProviderLocal, nil
	case "s3":
		return StorageProviderS3, nil
	default:
		return "", fmt.Errorf("unsupported storage provider: %q", raw)
	}
}

func NewService(provider StorageProvider, uploadsDir string) (StorageService, error) {
	switch provider {
	case StorageProviderLocal:
		return NewLocalStorageService(uploadsDir), nil
	case StorageProviderS3:
		return nil, fmt.Errorf("storage provider %q is not implemented yet", provider)
	default:
		return nil, fmt.Errorf("unsupported storage provider: %q", provider)
	}
}
