package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/analyses"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/config"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/database"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/documents"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/httpserver"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/storage"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("load config: %v", err)
	}

	if err := os.MkdirAll(cfg.UploadsDir, 0o755); err != nil {
		log.Fatalf("create uploads dir: %v", err)
	}

	pool, err := database.NewPostgresPool(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("connect database: %v", err)
	}
	defer pool.Close()

	docRepo := documents.NewRepository(pool)
	storageSvc, err := storage.NewService(cfg.StorageProvider, cfg.UploadsDir)
	if err != nil {
		log.Fatalf("init storage: %v", err)
	}
	docHandler := documents.NewHandler(docRepo, storageSvc)

	analysisRepo := analyses.NewRepository(pool)
	analysisHandler := analyses.NewHandler(analysisRepo)

	router := httpserver.NewRouter(httpserver.Handlers{
		Documents: docHandler,
		Analyses:  analysisHandler,
	})
	addr := fmt.Sprintf(":%d", cfg.APIPort)

	log.Printf(
		"starting legalmove-api on %s (env=%s, storage=%s)",
		addr,
		cfg.AppEnv,
		cfg.StorageProvider,
	)
	if err := http.ListenAndServe(addr, router); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
