#!/usr/bin/env bash
# FairLens GCP Setup Script
# Enables all required GCP APIs and configures the project.
#
# Usage:
#   export GCP_PROJECT_ID=your-project-id
#   bash scripts/setup-gcp.sh

set -euo pipefail

if [ -z "${GCP_PROJECT_ID:-}" ]; then
  echo "❌ GCP_PROJECT_ID environment variable is not set."
  echo "   Usage: GCP_PROJECT_ID=your-project-id bash scripts/setup-gcp.sh"
  exit 1
fi

echo "🔧 Setting project to: ${GCP_PROJECT_ID}"
gcloud config set project "${GCP_PROJECT_ID}"
gcloud config set compute/region "${GCP_REGION:-us-central1}"

echo "📦 Enabling required GCP APIs..."
gcloud services enable \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  bigquerystorage.googleapis.com \
  dataflow.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  cloudfunctions.googleapis.com \
  eventarc.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  cloudkms.googleapis.com \
  spanner.googleapis.com \
  binaryauthorization.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  firebase.googleapis.com \
  identitytoolkit.googleapis.com

echo ""
echo "✅ All 18 APIs enabled successfully for project: ${GCP_PROJECT_ID}"
echo ""
echo "Next steps:"
echo "  1. Run: cd infra && terraform init && terraform plan -var=\"project_id=${GCP_PROJECT_ID}\""
echo "  2. Run: terraform apply -var=\"project_id=${GCP_PROJECT_ID}\""
echo "  3. Set up service account: see references/gcp-setup.md Section 2"
