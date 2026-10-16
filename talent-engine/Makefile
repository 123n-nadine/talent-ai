.RECIPEPREFIX = >
# Images are built ONLY with the Docker daemon's default builder (Nadine, 2026-10-16). The shell's
# selected buildx builder on this server (sdf-builder) is someone else's: never use it or any other.
# `override` wins over the environment and the command line; `builder-check` refuses anything else.
override BUILDX_BUILDER := default
export BUILDX_BUILDER
COMPOSE = docker compose -p talentai
.PHONY: env install test lint typecheck up down logs ps migrate revision seed receiver cvs build builder-check

builder-check:
> @test "$$BUILDX_BUILDER" = "default" || { echo "refusing to build: BUILDX_BUILDER=$$BUILDX_BUILDER (only the default builder is allowed)"; exit 1; }
> @docker buildx inspect default >/dev/null && echo "builder: default"

build: builder-check
> $(COMPOSE) build api embed

env:
> uv run python -m scripts.init_env

# PaddleOCR, Presidio and spaCy too: a plain `uv sync` removes them and two tests skip silently
install:
> uv sync --group documents

test:
> uv run pytest -q

lint:
> uv run ruff check . && uv run ruff format --check .

fmt:
> uv run ruff check --fix . && uv run ruff format .

typecheck:
> uv run mypy app

WORKERS ?= 4

up: builder-check
> $(COMPOSE) up -d --build --scale worker=$(WORKERS)

down:
> $(COMPOSE) down

logs:
> $(COMPOSE) logs -f --tail=100

llm-logs:
> $(COMPOSE) logs -f --tail=100 vllm

gpu:
> nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv

ps:
> $(COMPOSE) ps

migrate:
> uv run alembic upgrade head

revision:
> uv run alembic revision --autogenerate -m "$(m)"

seed:
> uv run python -m scripts.seed

cvs:
> uv run python -m scripts.make_cvs

receiver:
> uv run python -m scripts.callback_receiver
