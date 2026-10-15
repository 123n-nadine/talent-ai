"""Engine configuration. Values here are DEFAULTS; per-tenant AI/OCR settings live in the DB."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"
    api_port: int = 18000

    database_url: str = "postgresql+psycopg://talentai:talentai@127.0.0.1:18030/talentai"
    auto_create_schema: bool = False  # tests only (SQLite); production uses Alembic
    redis_url: str = "redis://127.0.0.1:18031/0"
    queue_mode: str = "rq"  # rq | inline
    queue_name: str = "talentai:screenings"

    # defaults for a NEW tenant; the effective values are per tenant (see /v1/settings)
    ai_provider: str = "fake"  # fake | local | cloud
    llm_base_url: str = "http://vllm:8000/v1"
    llm_model: str = "qwen3-8b-awq"
    llm_timeout_s: int = 120
    llm_max_retries: int = 2
    cloud_llm_base_url: str = "https://api.openai.com/v1"
    cloud_llm_model: str = ""
    cloud_llm_api_key: str = ""
    ocr_provider: str = "none"  # none | paddle_cpu | paddle_vl | cloud
    ocr_min_confidence: float = 0.80
    embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"
    file_store: str = "./data/files"
    retention_days_default: int = 365
    max_attempts: int = 3
    retry_backoff_s: str = "1,3,9"

    tenant_name: str = "dev"
    tenant_api_key: str = "dev-talentai-key-change-me"
    allowed_facts: str = "nationality,height_cm,weight_kg,age"

    # Talent Console (served under /console on the API port; API key never reaches the browser)
    console_user: str = "nadine"
    console_password: str = ""  # empty = console login disabled
    console_session_secret: str = ""  # empty = derived from the tenant API key
    console_id_token_secret: str = "console-dev-id-token-secret"  # the host's HMAC secret stand-in
    console_session_hours: int = 12

    callback_url: str = ""
    callback_secret: str = ""
    callback_timeout_s: float = 10.0
    callback_max_age_s: int = 300

    profile_schema_version: str = "1.0"
    quote_match_threshold: float = 0.9  # fuzzy ratio for CV quotes after Arabic normalisation

    # documents (phase 2)
    max_upload_mb: int = 10
    pdf_min_text_chars: int = (
        50  # fewer letters/digits than this in a PDF -> treated as scanned -> OCR
    )
    ocr_render_dpi: int = 200
    ocr_threads: int = 8
    fake_ocr_text: str = ""
    fake_ocr_confidence: float = 0.95
    libreoffice_bin: str = "soffice"
    libreoffice_timeout_s: int = 120
    redaction_nlp: bool = True  # English names through Presidio/spaCy when installed

    @property
    def allowed_facts_list(self) -> list[str]:
        return [f.strip() for f in self.allowed_facts.split(",") if f.strip()]

    @property
    def retry_backoff(self) -> list[float]:
        return [float(x) for x in self.retry_backoff_s.split(",") if x.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
