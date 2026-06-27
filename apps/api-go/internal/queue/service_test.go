package queue

import (
	"testing"
)

func TestParseQueueProviderDefaultsToPostgres(t *testing.T) {
	t.Parallel()

	provider, err := ParseQueueProvider("")
	if err != nil {
		t.Fatalf("ParseQueueProvider() error = %v", err)
	}
	if provider != QueueProviderPostgres {
		t.Fatalf("provider = %q, want postgres", provider)
	}
}

func TestParseQueueProviderSupportsSQS(t *testing.T) {
	t.Parallel()

	provider, err := ParseQueueProvider("sqs")
	if err != nil {
		t.Fatalf("ParseQueueProvider() error = %v", err)
	}
	if provider != QueueProviderSQS {
		t.Fatalf("provider = %q, want sqs", provider)
	}
}

func TestParseQueueProviderSupportsAzureServiceBus(t *testing.T) {
	t.Parallel()

	provider, err := ParseQueueProvider("azure_service_bus")
	if err != nil {
		t.Fatalf("ParseQueueProvider() error = %v", err)
	}
	if provider != QueueProviderAzureServiceBus {
		t.Fatalf("provider = %q, want azure_service_bus", provider)
	}
}

func TestParseQueueProviderRejectsUnknown(t *testing.T) {
	t.Parallel()

	_, err := ParseQueueProvider("kafka")
	if err == nil {
		t.Fatal("ParseQueueProvider() expected error")
	}
}

func TestNewDispatcherUsesNoopForPostgres(t *testing.T) {
	t.Parallel()

	dispatcher, err := NewDispatcher(DispatcherConfig{
		Provider: QueueProviderPostgres,
	})
	if err != nil {
		t.Fatalf("NewDispatcher() error = %v", err)
	}
	if _, ok := dispatcher.(*NoopJobDispatcher); !ok {
		t.Fatalf("dispatcher type = %T, want *NoopJobDispatcher", dispatcher)
	}
}

func TestNewDispatcherRequiresSQSConfig(t *testing.T) {
	t.Parallel()

	_, err := NewDispatcher(DispatcherConfig{
		Provider: QueueProviderSQS,
	})
	if err == nil {
		t.Fatal("NewDispatcher() expected error")
	}
}

func TestNewDispatcherRequiresAzureServiceBusConfig(t *testing.T) {
	t.Parallel()

	_, err := NewDispatcher(DispatcherConfig{
		Provider: QueueProviderAzureServiceBus,
	})
	if err == nil {
		t.Fatal("NewDispatcher() expected error")
	}
}
