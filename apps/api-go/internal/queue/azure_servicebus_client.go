package queue

import (
	"fmt"
	"strings"

	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/Azure/azure-sdk-for-go/sdk/messaging/azservicebus"
)

func NewAzureServiceBusSDKClient(
	namespace string,
	queueName string,
	cred azcore.TokenCredential,
) (*azservicebus.Sender, error) {
	namespace = strings.TrimSpace(namespace)
	queueName = strings.TrimSpace(queueName)
	if namespace == "" {
		return nil, fmt.Errorf("AZURE_SERVICE_BUS_NAMESPACE is required")
	}
	if queueName == "" {
		return nil, fmt.Errorf("AZURE_SERVICE_BUS_QUEUE_NAME is required")
	}

	client, err := azservicebus.NewClient(
		fmt.Sprintf("%s.servicebus.windows.net", namespace),
		cred,
		nil,
	)
	if err != nil {
		return nil, fmt.Errorf("create service bus client: %w", err)
	}

	sender, err := client.NewSender(queueName, nil)
	if err != nil {
		return nil, fmt.Errorf("create service bus sender: %w", err)
	}

	return sender, nil
}
