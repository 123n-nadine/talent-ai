from __future__ import annotations

import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from scripts.seed_data import CANDIDATES, JOBS  # noqa: E402

API_KEY = "test-key"


def make_settings(**overrides) -> Settings:
    base = dict(
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        auto_create_schema=True,
        queue_mode="inline",
        ai_provider="fake",
        ocr_provider="fake",
        file_store=tempfile.mkdtemp(prefix="talentai-test-files-"),
        tenant_api_key=API_KEY,
        tenant_name="test",
        callback_url="",
        callback_secret="",
        retry_backoff_s="0",
        max_attempts=3,
        log_level="WARNING",
    )
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def client(settings: Settings):
    app = create_app(settings)
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {API_KEY}", "X-Talent-Actor": "pytest"})
        yield c


@pytest.fixture
def sec_job() -> dict:
    return JOBS["HR-OPN-2026-0011"]


@pytest.fixture
def seeded(client, sec_job):
    """Job 0011 approved and all its demo candidates screened (inline, fake LLM)."""
    r = client.put("/v1/jobs/HR-OPN-2026-0011", json=sec_job)
    assert r.status_code == 200, r.text
    ids = {}
    for cand in [c for c in CANDIDATES if c["job"] == "HR-OPN-2026-0011"]:
        r = client.put(
            f"/v1/candidates/{cand['ref']}",
            json={"id_token": cand["id_token"], "facts": cand["facts"], "answers": cand["answers"]},
        )
        assert r.status_code == 200, r.text
        r = client.post(
            "/v1/screenings", json={"job_ref": "HR-OPN-2026-0011", "candidate_ref": cand["ref"]}
        )
        assert r.status_code == 202, r.text
        ids[cand["ref"]] = r.json()["screening_id"]
    return ids
