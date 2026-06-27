package storage

import (
	"context"
	"fmt"
	"io"
	"strings"

	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/Azure/azure-sdk-for-go/sdk/storage/azblob"
	"github.com/Azure/azure-sdk-for-go/sdk/storage/azblob/blob"
)

type azureBlobSDKClient struct {
	client *azblob.Client
}

func NewAzureBlobClient(client *azblob.Client) blobAPI {
	return &azureBlobSDKClient{client: client}
}

func (c *azureBlobSDKClient) UploadBlob(
	ctx context.Context,
	containerName string,
	blobName string,
	body io.Reader,
	contentType string,
	metadata map[string]string,
) error {
	_, err := c.client.UploadStream(ctx, containerName, blobName, body, &azblob.UploadStreamOptions{
		HTTPHeaders: &blob.HTTPHeaders{
			BlobContentType: &contentType,
		},
		Metadata: metadataToPtrMap(metadata),
	})
	return err
}

func (c *azureBlobSDKClient) DownloadBlob(
	ctx context.Context,
	containerName string,
	blobName string,
) (io.ReadCloser, error) {
	resp, err := c.client.DownloadStream(ctx, containerName, blobName, nil)
	if err != nil {
		return nil, err
	}
	return resp.Body, nil
}

func (c *azureBlobSDKClient) DeleteBlob(ctx context.Context, containerName, blobName string) error {
	_, err := c.client.DeleteBlob(ctx, containerName, blobName, nil)
	return err
}

func NewAzureBlobSDKClient(accountName string, cred azcore.TokenCredential) (*azblob.Client, error) {
	accountName = strings.TrimSpace(accountName)
	if accountName == "" {
		return nil, fmt.Errorf("AZURE_STORAGE_ACCOUNT_NAME is required")
	}
	serviceURL := fmt.Sprintf("https://%s.blob.core.windows.net/", accountName)
	return azblob.NewClient(serviceURL, cred, nil)
}

func metadataToPtrMap(metadata map[string]string) map[string]*string {
	if len(metadata) == 0 {
		return nil
	}
	out := make(map[string]*string, len(metadata))
	for key, value := range metadata {
		val := value
		out[key] = &val
	}
	return out
}
