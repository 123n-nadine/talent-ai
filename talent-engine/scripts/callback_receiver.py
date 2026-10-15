"""Tiny local receiver that verifies the HMAC callback and prints the result (port 18060).

Usage: make receiver  (uv run python -m scripts.callback_receiver)
Set CALLBACK_URL=http://host.docker.internal:18060/callback in .env so the worker container reaches it.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from fastapi import FastAPI, Header, Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from app.core.security import verify_callback  # noqa: E402

load_dotenv()
SECRET = os.environ.get("CALLBACK_SECRET", "dev-callback-secret-change-me")
app = FastAPI(title="callback receiver (test)")
RECEIVED: list[dict] = []


@app.post("/callback")
async def callback(
    request: Request,
    x_talent_signature: str = Header(default=""),
    x_talent_timestamp: str = Header(default=""),
):
    body = await request.body()
    if not verify_callback(SECRET, x_talent_timestamp, body, x_talent_signature):
        print("REJECTED: bad signature or stale timestamp")
        return JSONResponse({"ok": False, "error": "bad signature"}, status_code=401)
    data = await request.json()
    RECEIVED.append(data)
    print(
        f"OK {data.get('candidate_ref')} job={data.get('job_ref')} status={data.get('ai_status')} "
        f"score={data.get('score')} band={data.get('band')} rank={data.get('rank')}"
    )
    return {"ok": True}


@app.get("/received")
def received():
    return {"count": len(RECEIVED), "items": RECEIVED}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("RECEIVER_PORT", "18060")))
