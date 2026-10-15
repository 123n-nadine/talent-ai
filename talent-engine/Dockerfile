FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    OMP_NUM_THREADS=8

# curl: healthchecks. LibreOffice: DOC/RTF -> PDF. Noto fonts: Arabic rendering. libgl/glib/gomp: PaddleOCR/OpenCV.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl ca-certificates \
        libreoffice-writer libreoffice-core \
        fonts-noto-core fonts-dejavu-core \
        libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.12.5

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --group documents

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
