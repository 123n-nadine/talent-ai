"""Talent Console: login, session cookie accepted by the API, id-token helper, static files."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.console.auth import id_token, issue, verify
from app.main import create_app
from tests.conftest import make_settings


def _client(**kw):
    c = TestClient(
        create_app(make_settings(console_user="nadine", console_password="pw-secret", **kw))
    )
    c.__enter__()
    return c


def test_console_requires_login_and_hides_the_api_key():
    c = _client()
    r = c.get("/console", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/console/login"
    assert c.get("/console/login").status_code == 200
    assert c.get("/v1/jobs").status_code == 401  # no cookie, no key
    r = c.post(
        "/console/login", data={"username": "nadine", "password": "wrong"}, follow_redirects=False
    )
    assert r.status_code == 303 and "error" in r.headers["location"]
    r = c.post(
        "/console/login",
        data={"username": "nadine", "password": "pw-secret"},
        follow_redirects=False,
    )
    assert (
        r.status_code == 303
        and r.headers["location"] == "/console"
        and "talent_console" in r.cookies
    )
    page = c.get("/console")
    assert page.status_code == 200 and "app.js" in page.text and "test-key" not in page.text
    js = c.get("/console/static/app.js").text
    assert "Bearer" not in js and "test-key" not in js  # the browser never holds the API key
    assert c.get("/console/me").json()["user"] == "nadine"
    assert c.get("/v1/jobs").status_code == 200  # cookie session acts on the default tenant
    r = c.post("/console/logout", follow_redirects=False)
    assert r.status_code == 303 and c.get("/v1/jobs").status_code == 401
    c.__exit__(None, None, None)


def test_console_actions_are_audited_with_the_user(sec_job):
    c = _client()
    c.post("/console/login", data={"username": "nadine", "password": "pw-secret"})
    assert c.put("/v1/jobs/J-1", json=sec_job).status_code == 200
    ev = c.get("/v1/audit", params={"ref": "J-1"}).json()["events"]
    assert ev and ev[0]["actor"] == "console:nadine"
    c.__exit__(None, None, None)


def test_id_token_helper_matches_hmac_and_needs_login():
    s = make_settings(console_user="u", console_password="p", console_id_token_secret="s3cret")
    c = TestClient(create_app(s))
    with c:
        assert c.post("/console/id-token", json={"national_id": "1234567890"}).status_code == 401
        c.post("/console/login", data={"username": "u", "password": "p"})
        tok = c.post("/console/id-token", json={"national_id": "1234567890"}).json()["id_token"]
        assert tok == id_token(s, "1234567890") and len(tok) == 64 and "1234567890" not in tok


def test_session_token_expiry_and_tamper():
    s = make_settings(console_session_hours=1)
    tok = issue(s, "nadine")
    assert verify(s, tok) == "nadine"
    assert (
        verify(s, tok[:-2] + "zz") is None
        and verify(s, "garbage") is None
        and verify(s, None) is None
    )
    assert verify(make_settings(console_session_secret="other"), tok) is None


def test_login_disabled_without_password():
    c = TestClient(create_app(make_settings(console_password="")))
    with c:
        r = c.post(
            "/console/login", data={"username": "nadine", "password": ""}, follow_redirects=False
        )
        assert r.status_code == 303 and "error" in r.headers["location"]
        assert "معطّل" in c.get("/console/login").text


def test_static_path_traversal_blocked():
    c = _client()
    assert c.get("/console/static/../../.env").status_code in (404, 400)
    assert c.get("/console/static/app.css").status_code == 200
    c.__exit__(None, None, None)


def test_fonts_are_served_locally():
    """The console never calls a third-party font service; the fonts ship with the app."""
    c = _client()
    r = c.get("/console/static/fonts/ibm-plex-sans-arabic-arabic-400-normal.woff2")
    assert r.status_code == 200 and r.headers["content-type"] == "font/woff2"
    for page in ("index.html", "login.html", "app.css"):
        assert "googleapis" not in c.get(f"/console/static/{page}").text
    assert "@font-face" in c.get("/console/static/app.css").text
    c.__exit__(None, None, None)
