package queue

import (
	"context"

	"github.com/google/uuid"
)

type NoopJobDispatcher struct{}

func NewNoopJobDispatcher() *NoopJobDispatcher {
	return &NoopJobDispatcher{}
}

func (d *NoopJobDispatcher) DispatchAnalysisJob(_ context.Context, _ uuid.UUID) error {
	return nil
}
