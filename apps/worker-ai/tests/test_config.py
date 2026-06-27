import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import importlib

import pytest

import config as config_module


def test_validate_requires_database_url(monkeypatch):
    monkeypatch.setattr(config_module, "DATABASE_URL", "")
    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        config_module.validate()


def test_validate_openai_config_requires_api_key(monkeypatch):
    monkeypatch.setattr(config_module, "OPENAI_API_KEY", "")
    with pytest.raises(ValueError, match="OPENAI_API_KEY is required to run the AI pipeline"):
        config_module.validate_openai_config()


def test_defaults_when_env_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_VISION_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_TEXT_MODEL", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.delenv("OPENAI_TIMEOUT", raising=False)
    monkeypatch.delenv("VISION_MAX_IMAGE_BYTES", raising=False)
    monkeypatch.delenv("VISION_MAX_DIMENSION", raising=False)

    importlib.reload(config_module)

    assert config_module.OPENAI_VISION_MODEL == "gpt-4o"
    assert config_module.OPENAI_TEXT_MODEL == "gpt-4o"
    assert config_module.LANGFUSE_HOST == "https://cloud.langfuse.com"
    assert config_module.OPENAI_TIMEOUT == 120.0
    assert config_module.VISION_MAX_IMAGE_BYTES == 20971520
    assert config_module.VISION_MAX_DIMENSION == 8192


def test_langfuse_disabled_without_keys(monkeypatch):
    monkeypatch.setattr(config_module, "LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setattr(config_module, "LANGFUSE_SECRET_KEY", "")
    assert config_module.langfuse_enabled() is False


def test_worker_use_mock_result_defaults_false(monkeypatch):
    monkeypatch.delenv("WORKER_USE_MOCK_RESULT", raising=False)
    importlib.reload(config_module)
    assert config_module.WORKER_USE_MOCK_RESULT is False


def test_worker_use_mock_result_parses_true_and_false(monkeypatch):
    monkeypatch.setenv("WORKER_USE_MOCK_RESULT", "true")
    importlib.reload(config_module)
    assert config_module.WORKER_USE_MOCK_RESULT is True

    monkeypatch.setenv("WORKER_USE_MOCK_RESULT", "no")
    importlib.reload(config_module)
    assert config_module.WORKER_USE_MOCK_RESULT is False


def test_queue_provider_defaults_to_postgres(monkeypatch):
    monkeypatch.delenv("QUEUE_PROVIDER", raising=False)
    importlib.reload(config_module)
    assert config_module.QUEUE_PROVIDER == "postgres"


def test_validate_queue_config_requires_sqs_queue_url(monkeypatch):
    monkeypatch.setattr(config_module, "DATABASE_URL", "postgres://example")
    monkeypatch.setattr(config_module, "QUEUE_PROVIDER", "sqs")
    monkeypatch.setattr(config_module, "SQS_QUEUE_URL", "")
    with pytest.raises(ValueError, match="SQS_QUEUE_URL is required"):
        config_module.validate_queue_config()


def test_validate_queue_config_requires_azure_service_bus_settings(monkeypatch):
    monkeypatch.setattr(config_module, "DATABASE_URL", "postgres://example")
    monkeypatch.setattr(config_module, "QUEUE_PROVIDER", "azure_service_bus")
    monkeypatch.setattr(config_module, "AZURE_SERVICE_BUS_NAMESPACE", "")
    monkeypatch.setattr(config_module, "AZURE_SERVICE_BUS_QUEUE_NAME", "analysis-jobs")
    with pytest.raises(ValueError, match="AZURE_SERVICE_BUS_NAMESPACE is required"):
        config_module.validate_queue_config()
