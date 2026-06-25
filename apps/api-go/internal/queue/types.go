package queue

import (
	"context"

	"github.com/google/uuid"
)

type QueueProvider string

const (
	QueueProviderPostgres QueueProvider = "postgres"
	QueueProviderSQS      QueueProvider = "sqs"
)

const DispatchSchemaVersion = "1.0"

type DispatchMessage struct {
	AnalysisID    string `json:"analysis_id"`
	SchemaVersion string `json:"schema_version"`
}

type JobDispatcher interface {
	DispatchAnalysisJob(ctx context.Context, analysisID uuid.UUID) error
}
