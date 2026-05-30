package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/storage"
	"github.com/joho/godotenv"
)

type Config struct {
	AppEnv          string
	APIPort         int
	DatabaseURL     string
	UploadsDir      string
	StorageProvider storage.StorageProvider
}

func Load() (Config, error) {
	_ = godotenv.Load("../../.env", ".env")

	storageProviderRaw := os.Getenv("STORAGE_PROVIDER")
	if strings.TrimSpace(storageProviderRaw) == "" {
		storageProviderRaw = "local"
	}
	storageProvider, err := storage.ParseStorageProvider(storageProviderRaw)
	if err != nil {
		return Config{}, err
	}

	cfg := Config{
		AppEnv:          os.Getenv("APP_ENV"),
		DatabaseURL:     os.Getenv("DATABASE_URL"),
		UploadsDir:      os.Getenv("UPLOADS_DIR"),
		StorageProvider: storageProvider,
	}

	portStr := os.Getenv("API_PORT")
	if portStr == "" {
		return Config{}, fmt.Errorf("API_PORT is required")
	}
	port, err := strconv.Atoi(portStr)
	if err != nil {
		return Config{}, fmt.Errorf("API_PORT must be a valid integer: %w", err)
	}
	cfg.APIPort = port

	if cfg.DatabaseURL == "" {
		return Config{}, fmt.Errorf("DATABASE_URL is required")
	}
	if cfg.UploadsDir == "" {
		return Config{}, fmt.Errorf("UPLOADS_DIR is required")
	}
	if cfg.AppEnv == "" {
		cfg.AppEnv = "local"
	}

	return cfg, nil
}
