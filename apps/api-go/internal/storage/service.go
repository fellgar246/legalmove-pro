package storage

import "fmt"

func NewService(provider StorageProvider, uploadsDir string) (StorageService, error) {
	switch provider {
	case ProviderLocal:
		return NewLocalStorageService(uploadsDir), nil
	case ProviderS3:
		return nil, fmt.Errorf("storage provider %q is not implemented yet", provider)
	default:
		return nil, fmt.Errorf("unsupported storage provider: %q", provider)
	}
}
