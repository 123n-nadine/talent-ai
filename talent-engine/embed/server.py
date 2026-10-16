"""Internal embedding service (compose network only): Qwen3-Embedding-0.6B on CPU behind an
OpenAI-compatible POST /v1/embeddings. Loaded once at start; weights in the talentai_models volume."""

from __future__ import annotations

import os
import time

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

MODEL = os.environ.get("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
torch.set_num_threads(int(os.environ.get("EMBED_THREADS", "4")))
_t0 = time.time()
model = SentenceTransformer(MODEL, device="cpu")
LOAD_S = round(time.time() - _t0, 1)
app = FastAPI(title="talentai-embed")


class EmbeddingsIn(BaseModel):
    input: list[str] | str
    model: str | None = None


@app.get("/health")
def health():
    return {
        "ok": True,
        "model": MODEL,
        "dim": model.get_sentence_embedding_dimension(),
        "load_s": LOAD_S,
    }


@app.post("/v1/embeddings")
def embeddings(data: EmbeddingsIn):
    texts = [data.input] if isinstance(data.input, str) else data.input
    if not texts or len(texts) > 64:
        raise HTTPException(status_code=422, detail="1 to 64 texts per request")
    t0 = time.time()
    vecs = model.encode(texts, normalize_embeddings=True, batch_size=8, convert_to_numpy=True)
    return {
        "object": "list",
        "model": MODEL,
        "data": [
            {"object": "embedding", "index": i, "embedding": v.tolist()} for i, v in enumerate(vecs)
        ],
        "usage": {"prompt_tokens": 0, "total_tokens": 0, "ms": int((time.time() - t0) * 1000)},
    }
