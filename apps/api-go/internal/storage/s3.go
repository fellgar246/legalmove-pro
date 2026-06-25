package storage

import (
	"context"
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
)

type s3API interface {
	PutObject(ctx context.Context, params *s3.PutObjectInput, optFns ...func(*s3.Options)) (*s3.PutObjectOutput, error)
	GetObject(ctx context.Context, params *s3.GetObjectInput, optFns ...func(*s3.Options)) (*s3.GetObjectOutput, error)
	DeleteObject(ctx context.Context, params *s3.DeleteObjectInput, optFns ...func(*s3.Options)) (*s3.DeleteObjectOutput, error)
}

type S3StorageService struct {
	client s3API
	bucket string
	prefix string
	now    func() time.Time
}

func NewS3StorageService(client s3API, bucket, prefix string) *S3StorageService {
	return &S3StorageService{
		client: client,
		bucket: strings.TrimSpace(bucket),
		prefix: strings.TrimSpace(prefix),
		now:    time.Now,
	}
}

func (s *S3StorageService) Save(ctx context.Context, input SaveObjectInput) (*StoredObject, error) {
	if s.client == nil {
		return nil, fmt.Errorf("s3 client is required")
	}
	if s.bucket == "" {
		return nil, fmt.Errorf("s3 bucket is required")
	}

	objectID, err := objectIDFromKey(input.Key)
	if err != nil {
		return nil, fmt.Errorf("resolve object id: %w", err)
	}

	objectKey := BuildS3ObjectKey(s.prefix, input.DocumentKind, objectID, input.OriginalName, s.now())
	contentType := strings.TrimSpace(input.ContentType)
	if contentType == "" {
		contentType = "application/octet-stream"
	}

	metadata := map[string]string{
		"original-filename": input.OriginalName,
		"document-kind":     normalizeDocumentKind(input.DocumentKind),
	}
	if input.SizeBytes > 0 {
		metadata["size-bytes"] = fmt.Sprintf("%d", input.SizeBytes)
	}

	_, err = s.client.PutObject(ctx, &s3.PutObjectInput{
		Bucket:      aws.String(s.bucket),
		Key:         aws.String(objectKey),
		Body:        input.Reader,
		ContentType: aws.String(contentType),
		Metadata:    metadata,
	})
	if err != nil {
		return nil, mapS3Error("save object", objectKey, err)
	}

	sizeBytes := input.SizeBytes
	if sizeBytes <= 0 {
		sizeBytes = 0
	}

	return &StoredObject{
		Provider:     StorageProviderS3,
		Key:          objectKey,
		LocalPath:    "",
		SizeBytes:    sizeBytes,
		OriginalName: input.OriginalName,
		ContentType:  contentType,
	}, nil
}

func (s *S3StorageService) Open(ctx context.Context, key string) (io.ReadCloser, error) {
	if s.client == nil {
		return nil, fmt.Errorf("s3 client is required")
	}
	if s.bucket == "" {
		return nil, fmt.Errorf("s3 bucket is required")
	}

	objectKey, err := s.resolveObjectKey(key)
	if err != nil {
		return nil, err
	}

	out, err := s.client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(objectKey),
	})
	if err != nil {
		return nil, mapS3Error("open object", objectKey, err)
	}
	if out.Body == nil {
		return nil, fmt.Errorf("open object %q: empty response body", objectKey)
	}
	return out.Body, nil
}

func (s *S3StorageService) Delete(ctx context.Context, key string) error {
	if s.client == nil {
		return fmt.Errorf("s3 client is required")
	}
	if s.bucket == "" {
		return fmt.Errorf("s3 bucket is required")
	}

	objectKey, err := s.resolveObjectKey(key)
	if err != nil {
		return err
	}

	_, err = s.client.DeleteObject(ctx, &s3.DeleteObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(objectKey),
	})
	if err != nil {
		return mapS3Error("delete object", objectKey, err)
	}
	return nil
}

func (s *S3StorageService) resolveObjectKey(key string) (string, error) {
	trimmed := strings.TrimSpace(key)
	if trimmed == "" {
		return "", fmt.Errorf("object key is required")
	}
	if strings.Contains(trimmed, "..") {
		return "", fmt.Errorf("invalid object key %q", key)
	}
	return trimmed, nil
}

func mapS3Error(action, key string, err error) error {
	var notFound *types.NotFound
	var noSuchKey *types.NoSuchKey
	if err != nil {
		switch {
		case strings.Contains(err.Error(), "NoSuchBucket"):
			return fmt.Errorf("%s %q: bucket not found", action, key)
		case strings.Contains(err.Error(), "AccessDenied"):
			return fmt.Errorf("%s %q: access denied", action, key)
		}
	}
	_ = notFound
	_ = noSuchKey
	return fmt.Errorf("%s %q: %w", action, key, err)
}
