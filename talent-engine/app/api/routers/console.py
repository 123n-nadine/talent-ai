"""Talent Console: login, static app, and the few host-side helpers the browser needs."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from app.api.deps import get_settings_dep
from app.console.auth import COOKIE, check_login, id_token, issue, verify
from app.core.config import Settings

router = APIRouter(tags=["console"])
STATIC = Path(__file__).resolve().parent.parent.parent.parent / "console" / "static"


def _user(request: Request, settings: Settings) -> str | None:
    return verify(settings, request.cookies.get(COOKIE))


@router.get("/console", response_class=HTMLResponse, include_in_schema=False)
def console_index(request: Request, settings: Settings = Depends(get_settings_dep)):
    if not _user(request, settings):
        return RedirectResponse("/console/login", status_code=303)
    return FileResponse(STATIC / "index.html", media_type="text/html")


@router.get("/console/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request, settings: Settings = Depends(get_settings_dep), error: str = ""):
    if _user(request, settings):
        return RedirectResponse("/console", status_code=303)
    html = (STATIC / "login.html").read_text(encoding="utf-8")
    note = "" if settings.console_password else "تسجيل الدخول معطّل: ضع CONSOLE_PASSWORD في .env"
    return HTMLResponse(
        html.replace("{{error}}", "اسم المستخدم أو كلمة المرور غير صحيحة" if error else note)
    )


@router.post("/console/login", include_in_schema=False)
def login(
    request: Request,
    username: str = Form(default=""),
    password: str = Form(default=""),
    settings: Settings = Depends(get_settings_dep),
):
    if not check_login(settings, username, password):
        return RedirectResponse("/console/login?error=1", status_code=303)
    resp = RedirectResponse("/console", status_code=303)
    resp.set_cookie(
        COOKIE,
        issue(settings, username),
        httponly=True,
        samesite="lax",
        max_age=settings.console_session_hours * 3600,
        path="/",
    )
    return resp


@router.post("/console/logout", include_in_schema=False)
def logout():
    resp = RedirectResponse("/console/login", status_code=303)
    resp.delete_cookie(COOKIE, path="/")
    return resp


@router.get("/console/me", include_in_schema=False)
def me(request: Request, settings: Settings = Depends(get_settings_dep)):
    user = _user(request, settings)
    if not user:
        raise HTTPException(status_code=401, detail="not logged in")
    return {"user": user, "tenant": settings.tenant_name}


class IdTokenIn(BaseModel):
    national_id: str = Field(min_length=6, max_length=20)


@router.post("/console/id-token", include_in_schema=False)
def make_id_token(
    data: IdTokenIn, request: Request, settings: Settings = Depends(get_settings_dep)
):
    """Stand-in for the host system: the raw national ID is hashed here and never stored."""
    if not _user(request, settings):
        raise HTTPException(status_code=401, detail="not logged in")
    return {"id_token": id_token(settings, data.national_id)}


@router.get("/console/static/{path:path}", include_in_schema=False)
def static(path: str):
    target = (STATIC / path).resolve()
    if not str(target).startswith(str(STATIC.resolve())) or not target.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(target)


@router.get("/console/health", include_in_schema=False)
def console_health():
    return JSONResponse({"ok": True})
