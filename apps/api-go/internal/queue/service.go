package queue

import (
	"fmt"
	"strings"
)

type DispatcherConfig struct {
	Provider QueueProvider
	AWSRegion string
	QueueURL  string
	SQSClient sqsAPI

	AzureServiceBusNamespace  string
	AzureServiceBusQueueName  string
	ServiceBusClient        serviceBusAPI
}

func ParseQueueProvider(raw string) (QueueProvider, error) {
	switch strings.ToLower(strings.TrimSpace(raw)) {
	case "", "postgres":
		return QueueProviderPostgres, nil
	case "sqs":
		return QueueProviderSQS, nil
	case "azure_service_bus":
		return QueueProviderAzureServiceBus, nil
	default:
		return "", fmt.Errorf("unsupported queue provider: %q", raw)
	}
}

func NewDispatcher(cfg DispatcherConfig) (JobDispatcher, error) {
	switch cfg.Provider {
	case QueueProviderPostgres:
		return NewNoopJobDispatcher(), nil
	case QueueProviderSQS:
		if strings.TrimSpace(cfg.AWSRegion) == "" {
			return nil, fmt.Errorf("AWS_REGION is required when QUEUE_PROVIDER=sqs")
		}
		if strings.TrimSpace(cfg.QueueURL) == "" {
			return nil, fmt.Errorf("SQS_QUEUE_URL is required when QUEUE_PROVIDER=sqs")
		}
		if cfg.SQSClient == nil {
			return nil, fmt.Errorf("sqs client is required when QUEUE_PROVIDER=sqs")
		}
		return NewSQSJobDispatcher(cfg.SQSClient, cfg.QueueURL), nil
	case QueueProviderAzureServiceBus:
		if strings.TrimSpace(cfg.AzureServiceBusNamespace) == "" {
			return nil, fmt.Errorf("AZURE_SERVICE_BUS_NAMESPACE is required when QUEUE_PROVIDER=azure_service_bus")
		}
		if strings.TrimSpace(cfg.AzureServiceBusQueueName) == "" {
			return nil, fmt.Errorf("AZURE_SERVICE_BUS_QUEUE_NAME is required when QUEUE_PROVIDER=azure_service_bus")
		}
		if cfg.ServiceBusClient == nil {
			return nil, fmt.Errorf("service bus client is required when QUEUE_PROVIDER=azure_service_bus")
		}
		return NewAzureServiceBusJobDispatcher(cfg.ServiceBusClient), nil
	default:
		return nil, fmt.Errorf("unsupported queue provider: %q", cfg.Provider)
	}
}
