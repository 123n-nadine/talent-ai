.RECIPEPREFIX = >
# The host's selected buildx builder (sdf-builder, a docker-container builder) has no DNS;
# build with the daemon's default builder instead.
export BUILDX_BUILDER = default
COMPOSE = docker compose -p talentai
.PHONY: env install test lint typecheck up down logs ps migrate revision seed receiver

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

up:
> $(COMPOSE) up -d --build

down:
> $(COMPOSE) down

logs:
> $(COMPOSE) logs -f --tail=100

ps:
> $(COMPOSE) ps

migrate:
> uv run alembic upgrade head

revision:
> uv run alembic revision --autogenerate -m "$(m)"

seed:
> uv run python -m scripts.seed

receiver:
> uv run python -m scripts.callback_receiver
