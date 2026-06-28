package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"

	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/analyses"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/config"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/database"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/documents"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/httpserver"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/queue"
	"github.com/felipegarcia/legalmove-pro/apps/api-go/internal/storage"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("load config: %v", err)
	}

	if err := os.MkdirAll(cfg.UploadsDir, 0o755); err != nil {
		log.Fatalf("create uploads dir: %v", err)
	}

	pool, err := database.NewPostgresPool(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("connect database: %v", err)
	}
	defer pool.Close()

	storageCfg := storage.ServiceConfig{
		Provider:                  cfg.StorageProvider,
		UploadsDir:                cfg.UploadsDir,
		AWSRegion:                 cfg.AWSRegion,
		S3Bucket:                  cfg.S3Bucket,
		S3Prefix:                  cfg.S3Prefix,
		AzureStorageAccountName:   cfg.AzureStorageAccountName,
		AzureStorageContainerName: cfg.AzureStorageContainerName,
	}

	queueCfg := queue.DispatcherConfig{
		Provider:                 cfg.QueueProvider,
		AWSRegion:                cfg.AWSRegion,
		QueueURL:                 cfg.SQSQueueURL,
		AzureServiceBusNamespace: cfg.AzureServiceBusNamespace,
		AzureServiceBusQueueName:   cfg.AzureServiceBusQueueName,
	}

	needsAWS := cfg.StorageProvider == storage.StorageProviderS3 || cfg.QueueProvider == queue.QueueProviderSQS
	if needsAWS {
		awsCfg, err := awsconfig.LoadDefaultConfig(
			context.Background(),
			awsconfig.WithRegion(cfg.AWSRegion),
		)
		if err != nil {
			log.Fatalf("load aws config: %v", err)
		}
		if cfg.StorageProvider == storage.StorageProviderS3 {
			storageCfg.S3Client = storage.NewS3Client(s3.NewFromConfig(awsCfg))
		}
		if cfg.QueueProvider == queue.QueueProviderSQS {
			queueCfg.SQSClient = queue.NewSQSClient(sqs.NewFromConfig(awsCfg))
		}
	}

	needsAzure := cfg.StorageProvider == storage.StorageProviderAzureBlob ||
		cfg.QueueProvider == queue.QueueProviderAzureServiceBus
	if needsAzure {
		azureCred, err := storage.NewAzureCredential(cfg.AzureClientID)
		if err != nil {
			log.Fatalf("load azure credential: %v", err)
		}
		if cfg.StorageProvider == storage.StorageProviderAzureBlob {
			blobClient, err := storage.NewAzureBlobSDKClient(cfg.AzureStorageAccountName, azureCred)
			if err != nil {
				log.Fatalf("init azure blob client: %v", err)
			}
			storageCfg.AzureBlobClient = storage.NewAzureBlobClient(blobClient)
		}
		if cfg.QueueProvider == queue.QueueProviderAzureServiceBus {
			sender, err := queue.NewAzureServiceBusSDKClient(
				cfg.AzureServiceBusNamespace,
				cfg.AzureServiceBusQueueName,
				azureCred,
			)
			if err != nil {
				log.Fatalf("init azure service bus sender: %v", err)
			}
			queueCfg.ServiceBusClient = queue.NewAzureServiceBusClient(sender)
		}
	}

	docRepo := documents.NewRepository(pool)
	storageSvc, err := storage.NewService(storageCfg)
	if err != nil {
		log.Fatalf("init storage: %v", err)
	}
	docHandler := documents.NewHandler(docRepo, storageSvc)

	analysisRepo := analyses.NewRepository(pool)
	jobDispatcher, err := queue.NewDispatcher(queueCfg)
	if err != nil {
		log.Fatalf("init job dispatcher: %v", err)
	}
	analysisHandler := analyses.NewHandler(analysisRepo, jobDispatcher)

	router := httpserver.NewRouter(httpserver.Handlers{
		Documents: docHandler,
		Analyses:  analysisHandler,
	}, cfg.CORSAllowedOrigins)
	addr := fmt.Sprintf(":%d", cfg.APIPort)

	switch cfg.StorageProvider {
	case storage.StorageProviderS3:
		log.Printf(
			"starting legalmove-api on %s (env=%s, storage=s3, bucket=%s, prefix=%s, region=%s, queue=%s)",
			addr,
			cfg.AppEnv,
			cfg.S3Bucket,
			cfg.S3Prefix,
			cfg.AWSRegion,
			cfg.QueueProvider,
		)
	case storage.StorageProviderAzureBlob:
		log.Printf(
			"starting legalmove-api on %s (env=%s, storage=azure_blob, account=%s, container=%s, queue=%s)",
			addr,
			cfg.AppEnv,
			cfg.AzureStorageAccountName,
			cfg.AzureStorageContainerName,
			cfg.QueueProvider,
		)
	default:
		log.Printf(
			"starting legalmove-api on %s (env=%s, storage=local, uploads=%s, queue=%s)",
			addr,
			cfg.AppEnv,
			cfg.UploadsDir,
			cfg.QueueProvider,
		)
	}

	if err := http.ListenAndServe(addr, router); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
