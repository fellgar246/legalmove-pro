package queue

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/google/uuid"
)

type mockServiceBusClient struct {
	sendMessage func(ctx context.Context, body []byte) error
}

func (m *mockServiceBusClient) SendMessage(ctx context.Context, body []byte) error {
	return m.sendMessage(ctx, body)
}

func TestAzureServiceBusJobDispatcherSendsExpectedPayload(t *testing.T) {
	t.Parallel()

	analysisID := uuid.New()
	var capturedBody []byte

	client := &mockServiceBusClient{
		sendMessage: func(_ context.Context, body []byte) error {
			capturedBody = append([]byte(nil), body...)
			return nil
		},
	}

	dispatcher := NewAzureServiceBusJobDispatcher(client)
	if err := dispatcher.DispatchAnalysisJob(context.Background(), analysisID); err != nil {
		t.Fatalf("DispatchAnalysisJob() error = %v", err)
	}

	var payload DispatchMessage
	if err := json.Unmarshal(capturedBody, &payload); err != nil {
		t.Fatalf("json.Unmarshal() error = %v", err)
	}
	if payload.AnalysisID != analysisID.String() {
		t.Fatalf("analysis_id = %q, want %q", payload.AnalysisID, analysisID.String())
	}
	if payload.SchemaVersion != DispatchSchemaVersion {
		t.Fatalf("schema_version = %q, want %q", payload.SchemaVersion, DispatchSchemaVersion)
	}
}
