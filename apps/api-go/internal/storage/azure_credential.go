package storage

import (
	"fmt"
	"strings"

	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/Azure/azure-sdk-for-go/sdk/azidentity"
)

func NewAzureCredential(clientID string) (azcore.TokenCredential, error) {
	clientID = strings.TrimSpace(clientID)
	if clientID == "" {
		cred, err := azidentity.NewDefaultAzureCredential(nil)
		if err != nil {
			return nil, fmt.Errorf("create azure credential: %w", err)
		}
		return cred, nil
	}

	cred, err := azidentity.NewManagedIdentityCredential(&azidentity.ManagedIdentityCredentialOptions{
		ID: azidentity.ClientID(clientID),
	})
	if err != nil {
		return nil, fmt.Errorf("create managed identity credential: %w", err)
	}
	return cred, nil
}
