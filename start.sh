#!/bin/sh
set -e

# Migrations run separately as a pre-deploy step (see scripts/deploy.sh) — avoids
# slow Cloud Run cold starts and migration races across concurrent revisions.
# uvicorn comes from the image's pre-synced venv (on PATH). Not `uv run`: it re-syncs
# the default `dev` group, downloading packages from PyPI on every cold start.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
