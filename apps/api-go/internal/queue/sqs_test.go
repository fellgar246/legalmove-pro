package queue

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
	"github.com/google/uuid"
)

type mockSQSClient struct {
	sendMessage func(ctx context.Context, params *sqs.SendMessageInput, optFns ...func(*sqs.Options)) (*sqs.SendMessageOutput, error)
}

func (m *mockSQSClient) SendMessage(ctx context.Context, params *sqs.SendMessageInput, optFns ...func(*sqs.Options)) (*sqs.SendMessageOutput, error) {
	return m.sendMessage(ctx, params, optFns...)
}

func TestSQSJobDispatcherSendsExpectedPayload(t *testing.T) {
	t.Parallel()

	analysisID := uuid.New()
	queueURL := "https://sqs.us-east-1.amazonaws.com/123/legalmove-analysis"
	var capturedBody string
	var capturedQueueURL *string

	client := &mockSQSClient{
		sendMessage: func(_ context.Context, params *sqs.SendMessageInput, _ ...func(*sqs.Options)) (*sqs.SendMessageOutput, error) {
			capturedQueueURL = params.QueueUrl
			if params.MessageBody != nil {
				capturedBody = *params.MessageBody
			}
			return &sqs.SendMessageOutput{}, nil
		},
	}

	dispatcher := NewSQSJobDispatcher(client, queueURL)
	if err := dispatcher.DispatchAnalysisJob(context.Background(), analysisID); err != nil {
		t.Fatalf("DispatchAnalysisJob() error = %v", err)
	}

	if capturedQueueURL == nil || aws.ToString(capturedQueueURL) != queueURL {
		t.Fatalf("queue url = %v, want %q", capturedQueueURL, queueURL)
	}

	var payload DispatchMessage
	if err := json.Unmarshal([]byte(capturedBody), &payload); err != nil {
		t.Fatalf("json.Unmarshal() error = %v", err)
	}
	if payload.AnalysisID != analysisID.String() {
		t.Fatalf("analysis_id = %q, want %q", payload.AnalysisID, analysisID.String())
	}
	if payload.SchemaVersion != DispatchSchemaVersion {
		t.Fatalf("schema_version = %q, want %q", payload.SchemaVersion, DispatchSchemaVersion)
	}
}
