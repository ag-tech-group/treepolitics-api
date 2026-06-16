#!/usr/bin/env bash
# Manual deploy of the Treepolitics API to Cloud Run.
#
# Until Phase D (#5) wires up GitHub Actions auto-deploy, run this from a clean
# working tree to ship a new revision. Migrations are NOT applied here — run
# them separately via cloud-sql-proxy (see README "Production Deployment").

set -euo pipefail

PROJECT="treepolitics-prod"
# Deployer's gcloud account. Set GCP_ACCOUNT so no personal email is baked into
# git history and each deployer uses their own identity (we deliberately do NOT
# fall back to the active gcloud account, to avoid deploying as the wrong one).
ACCOUNT="${GCP_ACCOUNT:-}"
if [ -z "${ACCOUNT}" ]; then
  echo "Set GCP_ACCOUNT to the gcloud account to deploy with, e.g.:" >&2
  echo "  GCP_ACCOUNT=you@example.com ./scripts/deploy.sh" >&2
  exit 1
fi
REGION="us-east1"
SERVICE="treepolitics-api"
REPO="api"
RUNTIME_SA="treepolitics-api-runtime@${PROJECT}.iam.gserviceaccount.com"
SQL_INSTANCE="${PROJECT}:${REGION}:treepolitics-db"
TAG="$(git rev-parse --short HEAD)"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/api:${TAG}"

echo "Building ${IMAGE} via Cloud Build..."
gcloud builds submit \
  --tag "${IMAGE}" \
  --account="${ACCOUNT}" \
  --project="${PROJECT}"

echo "Deploying ${SERVICE} (revision pinned to ${TAG})..."
# `^|^` sets `|` as the env-var delimiter so commas inside CORS_ORIGINS survive.
gcloud run deploy "${SERVICE}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --service-account="${RUNTIME_SA}" \
  --add-cloudsql-instances="${SQL_INSTANCE}" \
  --set-env-vars="^|^ENVIRONMENT=production|COOKIE_DOMAIN=.treepolitics.net|FRONTEND_URL=https://treepolitics.net|CORS_ORIGINS=https://treepolitics.net,https://www.treepolitics.net" \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest" \
  --allow-unauthenticated \
  --account="${ACCOUNT}" \
  --project="${PROJECT}"

echo
echo "Deployed. Service URL:"
gcloud run services describe "${SERVICE}" \
  --region="${REGION}" \
  --format="value(status.url)" \
  --account="${ACCOUNT}" \
  --project="${PROJECT}"
