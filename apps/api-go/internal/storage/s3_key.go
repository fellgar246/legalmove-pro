package storage

import (
	"fmt"
	"path/filepath"
	"regexp"
	"strings"
	"time"
	"unicode"

	"github.com/google/uuid"
)

var unsafeFilenameChars = regexp.MustCompile(`[^a-zA-Z0-9._-]+`)

func sanitizeFilename(name string) string {
	base := strings.TrimSpace(filepath.Base(name))
	if base == "" || base == "." {
		return "document"
	}

	ext := filepath.Ext(base)
	stem := strings.TrimSuffix(base, ext)
	stem = unsafeFilenameChars.ReplaceAllString(stem, "_")
	stem = strings.Trim(stem, "._-")
	if stem == "" {
		stem = "document"
	}

	if ext != "" {
		ext = strings.ToLower(ext)
		if !strings.HasPrefix(ext, ".") {
			ext = "." + ext
		}
		for _, r := range ext[1:] {
			if !unicode.IsLetter(r) && !unicode.IsDigit(r) && r != '.' {
				ext = ""
				break
			}
		}
	}

	const maxStemLen = 80
	if len(stem) > maxStemLen {
		stem = stem[:maxStemLen]
	}

	return stem + ext
}

func normalizeDocumentKind(kind string) string {
	kind = strings.ToLower(strings.TrimSpace(kind))
	switch kind {
	case "original", "amendment":
		return kind
	default:
		return "unknown"
	}
}

func BuildS3ObjectKey(prefix, documentKind string, objectID uuid.UUID, originalName string, now time.Time) string {
	kind := normalizeDocumentKind(documentKind)
	safeName := sanitizeFilename(originalName)
	key := fmt.Sprintf(
		"documents/%s/%04d/%02d/%s-%s",
		kind,
		now.UTC().Year(),
		int(now.UTC().Month()),
		objectID.String(),
		safeName,
	)

	prefix = strings.Trim(strings.TrimSpace(prefix), "/")
	if prefix == "" {
		return key
	}
	return prefix + "/" + key
}

func objectIDFromKey(key string) (uuid.UUID, error) {
	stem := strings.TrimSuffix(filepath.Base(key), filepath.Ext(key))
	id, err := uuid.Parse(stem)
	if err != nil {
		return uuid.Nil, fmt.Errorf("invalid object key %q: expected uuid filename", key)
	}
	return id, nil
}
