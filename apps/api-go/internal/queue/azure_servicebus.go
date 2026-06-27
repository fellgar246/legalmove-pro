package queue

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/Azure/azure-sdk-for-go/sdk/messaging/azservicebus"
	"github.com/google/uuid"
)

type serviceBusAPI interface {
	SendMessage(ctx context.Context, body []byte) error
}

type AzureServiceBusJobDispatcher struct {
	client serviceBusAPI
}

func NewAzureServiceBusJobDispatcher(client serviceBusAPI) *AzureServiceBusJobDispatcher {
	return &AzureServiceBusJobDispatcher{client: client}
}

func (d *AzureServiceBusJobDispatcher) DispatchAnalysisJob(ctx context.Context, analysisID uuid.UUID) error {
	if d.client == nil {
		return fmt.Errorf("service bus client is required")
	}

	body, err := json.Marshal(DispatchMessage{
		AnalysisID:    analysisID.String(),
		SchemaVersion: DispatchSchemaVersion,
	})
	if err != nil {
		return fmt.Errorf("marshal dispatch message: %w", err)
	}

	if err := d.client.SendMessage(ctx, body); err != nil {
		return fmt.Errorf("send service bus message: %w", err)
	}

	return nil
}

type azureServiceBusSender struct {
	sender *azservicebus.Sender
}

func NewAzureServiceBusClient(sender *azservicebus.Sender) serviceBusAPI {
	return &azureServiceBusSender{sender: sender}
}

func (s *azureServiceBusSender) SendMessage(ctx context.Context, body []byte) error {
	return s.sender.SendMessage(ctx, &azservicebus.Message{Body: body}, nil)
}
