.RECIPEPREFIX = >
# The host's selected buildx builder (sdf-builder, a docker-container builder) has no DNS;
# build with the daemon's default builder instead.
export BUILDX_BUILDER = default
COMPOSE = docker compose -p talentai
.PHONY: env install test lint typecheck up down logs ps migrate revision seed receiver cvs

env:
> uv run python -m scripts.init_env

install:
> uv sync

test:
> uv run pytest -q

lint:
> uv run ruff check . && uv run ruff format --check .

fmt:
> uv run ruff check --fix . && uv run ruff format .

typecheck:
> uv run mypy app

WORKERS ?= 4

up:
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
