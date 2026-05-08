#!/bin/sh
set -e

# Migrations run separately as a pre-deploy step (see scripts/deploy.sh) — avoids
# slow Cloud Run cold starts and migration races across concurrent revisions.
exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
