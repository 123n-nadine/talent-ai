#!/bin/sh
# docker compose for this project with the default builder only (use instead of a plain
# `docker compose build`, which would pick the shell's selected buildx builder).
export BUILDX_BUILDER=default
cd "$(dirname "$0")/.." && exec docker compose -p talentai "$@"
