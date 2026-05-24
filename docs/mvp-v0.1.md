# LegalMove Pro MVP v0.1

## Goal

Build a local-first platform for comparing an original legal contract against an amendment and producing a structured AI-assisted report for human review.

## Architecture

- Web: Next.js
- API: Go
- Worker: Python
- Database: PostgreSQL
- Local storage: filesystem
- Future storage: S3
- Future queue: SQS
- LLM observability: Langfuse

## First milestone

The first milestone validates the product flow without real AI:

1. Upload original document.
2. Upload amendment document.
3. Create analysis job.
4. Worker processes queued job.
5. Worker stores mock result.
6. API returns result.

## Legal disclaimer

LegalMove Pro provides AI-generated review support. It does not provide definitive legal advice.
All outputs must be reviewed by a qualified human.