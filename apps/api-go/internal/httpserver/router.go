package httpserver

import (
	"encoding/json"
	"net/http"

	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/analyses"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/documents"
	"github.com/go-chi/chi/v5"
)

type healthResponse struct {
	Status  string `json:"status"`
	Service string `json:"service"`
}

type Handlers struct {
	Documents *documents.Handler
	Analyses  *analyses.Handler
}

func NewRouter(h Handlers) http.Handler {
	r := chi.NewRouter()
	r.Use(CORSMiddleware("http://localhost:3000"))

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(w).Encode(healthResponse{
			Status:  "ok",
			Service: "legalmove-api",
		})
	})

	r.Post("/documents", h.Documents.Upload)
	r.Post("/analyses", h.Analyses.Create)
	r.Get("/analyses", h.Analyses.List)
	r.Get("/analyses/{id}", h.Analyses.GetByID)
	r.Get("/analyses/{id}/result", h.Analyses.GetResult)

	return r
}
