# Internal embedding service for the talent pool (CPU only; the GPU stays with vLLM under its cap).
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.8.0 \
    && pip install --no-cache-dir "sentence-transformers>=5.0,<6" "transformers>=4.51,<5" "fastapi>=0.115,<1" "uvicorn>=0.30"
WORKDIR /srv
COPY server.py .
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
