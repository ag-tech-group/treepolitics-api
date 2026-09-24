#!/bin/sh
set -e

# Migrations run separately as a pre-deploy step (see scripts/deploy.sh) — avoids
# slow Cloud Run cold starts and migration races across concurrent revisions.
# uvicorn comes from the image's pre-synced venv (on PATH). Not `uv run`: it re-syncs
# the default `dev` group, downloading packages from PyPI on every cold start.
#
# Cloud Run connects from a link-local address (169.254.x.x) and passes the caller's IP
# in X-Forwarded-For. Trust that header only from link-local peers so request.client
# (rate limiting, security logs) is the real caller. uvicorn takes the right-most
# untrusted entry, i.e. the one Cloud Run appended, so callers can't spoof it.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" \
  --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-169.254.0.0/16}"
