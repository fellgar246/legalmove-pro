# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --create-home app \
    && mkdir -p /tmp/legalmove-documents \
    && chown app:app /tmp/legalmove-documents

WORKDIR /app

COPY --from=builder /install /usr/local
COPY src ./src

RUN chown -R app:app /app

USER app

ENV PYTHONPATH=src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOCUMENT_TEMP_DIR=/tmp/legalmove-documents

CMD ["python", "src/main.py"]
