package queue

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
	"github.com/google/uuid"
)

type sqsAPI interface {
	SendMessage(ctx context.Context, params *sqs.SendMessageInput, optFns ...func(*sqs.Options)) (*sqs.SendMessageOutput, error)
}

type SQSJobDispatcher struct {
	client   sqsAPI
	queueURL string
}

func NewSQSJobDispatcher(client sqsAPI, queueURL string) *SQSJobDispatcher {
	return &SQSJobDispatcher{
		client:   client,
		queueURL: queueURL,
	}
}

func (d *SQSJobDispatcher) DispatchAnalysisJob(ctx context.Context, analysisID uuid.UUID) error {
	if d.client == nil {
		return fmt.Errorf("sqs client is required")
	}
	if d.queueURL == "" {
		return fmt.Errorf("SQS_QUEUE_URL is required")
	}

	body, err := json.Marshal(DispatchMessage{
		AnalysisID:    analysisID.String(),
		SchemaVersion: DispatchSchemaVersion,
	})
	if err != nil {
		return fmt.Errorf("marshal dispatch message: %w", err)
	}

	_, err = d.client.SendMessage(ctx, &sqs.SendMessageInput{
		QueueUrl:    aws.String(d.queueURL),
		MessageBody: aws.String(string(body)),
	})
	if err != nil {
		return fmt.Errorf("send sqs message: %w", err)
	}

	return nil
}

// NewSQSClient wraps the AWS SDK client for injection from main.
func NewSQSClient(client *sqs.Client) sqsAPI {
	return client
}
