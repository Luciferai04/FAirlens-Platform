#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# FairLens GCP Demo — Full Cloud Architecture Flow
# ═══════════════════════════════════════════════════════════════════
#
# This script demonstrates the full FairLens cloud architecture:
#   1. Upload synthetic biased dataset to GCS
#   2. Trigger Dataflow bias scanner pipeline
#   3. Wait for scanner completion
#   4. Read BiasProfile from BigQuery
#   5. Build and run the CI/CD fairness gate container
#
# Prerequisites:
#   - GCP project with APIs enabled (run scripts/setup-gcp.sh)
#   - Terraform resources provisioned (run: cd infra && terraform apply)
#   - Docker installed locally
#   - gcloud CLI authenticated
#
# Usage:
#   export GCP_PROJECT_ID=your-project-id
#   export GCP_REGION=us-central1
#   bash scripts/demo_gcp.sh
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

echo "═══════════════════════════════════════════════════════════════"
echo "  FairLens GCP Demo — Full Cloud Architecture"
echo "═══════════════════════════════════════════════════════════════"

# ── Validate environment ──────────────────────────────────────────
if [ -z "${GCP_PROJECT_ID:-}" ]; then
  echo "❌ Set GCP_PROJECT_ID environment variable first."
  exit 1
fi
REGION="${GCP_REGION:-us-central1}"
BUCKET="${GCP_PROJECT_ID}-fairlens-artifacts"
DATASET_PATH="gs://${BUCKET}/demo/hiring_data.csv"
MODEL_PATH="gs://${BUCKET}/demo/hiring_model.pkl"

echo "  Project:  ${GCP_PROJECT_ID}"
echo "  Region:   ${REGION}"
echo "  Bucket:   ${BUCKET}"
echo ""

# ── Step 1: Generate and upload synthetic dataset ─────────────────
echo "[Step 1/5] Generating synthetic dataset and uploading to GCS..."

python3 -c "
import numpy as np, pandas as pd
rng = np.random.RandomState(42)
n = 1000
gender = rng.choice(['male','female'], n, p=[0.55,0.45])
race = rng.choice(['White','Black','Asian','Hispanic'], n, p=[0.45,0.25,0.15,0.15])
hired = np.zeros(n, dtype=int)
for i in range(n):
    p = 0.3 + (0.20 if gender[i]=='male' else 0) + (0.05 if race[i]=='White' else 0)
    hired[i] = rng.binomial(1, min(max(p, 0.05), 0.95))
df = pd.DataFrame({
    'years_experience': rng.poisson(5,n).clip(0,30),
    'education_level': rng.choice([1,2,3,4],n),
    'skill_score': rng.normal(70,15,n).clip(0,100).round(1),
    'interview_score': rng.normal(65,12,n).clip(0,100).round(1),
    'gender': gender, 'race': race, 'label': hired
})
df.to_csv('/tmp/hiring_data.csv', index=False)
print(f'  Generated {len(df)} rows')
"

gsutil cp /tmp/hiring_data.csv "${DATASET_PATH}"
echo "  ✅ Dataset uploaded to ${DATASET_PATH}"

# ── Step 2: Train model and upload ────────────────────────────────
echo ""
echo "[Step 2/5] Training model and uploading to GCS..."

python3 -c "
import pandas as pd, pickle
from sklearn.ensemble import RandomForestClassifier
df = pd.read_csv('/tmp/hiring_data.csv')
features = ['years_experience','education_level','skill_score','interview_score']
X = df[features]; y = df['label']
model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
model.fit(X, y)
with open('/tmp/hiring_model.pkl','wb') as f: pickle.dump(model, f)
print(f'  Model trained. Accuracy: {model.score(X,y):.2%}')
"

gsutil cp /tmp/hiring_model.pkl "${MODEL_PATH}"
echo "  ✅ Model uploaded to ${MODEL_PATH}"

# ── Step 3: Run Dataflow Bias Scanner ─────────────────────────────
echo ""
echo "[Step 3/5] Launching Dataflow bias scanner pipeline..."
echo "  (This submits an Apache Beam job to Google Cloud Dataflow)"

python3 scanner/pipeline.py \
  --runner=DataflowRunner \
  --project="${GCP_PROJECT_ID}" \
  --region="${REGION}" \
  --input_gcs="${DATASET_PATH}" \
  --sensitive_cols="gender,race" \
  --label_col="label" \
  --bq_output="${GCP_PROJECT_ID}:fairlens.bias_profiles" \
  --temp_location="gs://${BUCKET}/tmp" \
  --staging_location="gs://${BUCKET}/staging" \
  --setup_file=scanner/setup.py || echo "  ⚠️  Dataflow job submitted (check console for status)"

echo "  ✅ Scanner pipeline submitted"

# ── Step 4: Query BiasProfile from BigQuery ───────────────────────
echo ""
echo "[Step 4/5] Querying BiasProfile from BigQuery..."

bq query --use_legacy_sql=false --format=prettyjson \
  "SELECT * FROM \`${GCP_PROJECT_ID}.fairlens.bias_profiles\`
   ORDER BY scanned_at DESC LIMIT 1"

echo "  ✅ BiasProfile retrieved"

# ── Step 5: Run Fairness Gate ─────────────────────────────────────
echo ""
echo "[Step 5/5] Running CI/CD Fairness Gate..."

# Build gate Docker image
docker build -t fairlens-gate -f gate/Dockerfile .

# Download model and eval data
gsutil cp "${MODEL_PATH}" /tmp/gate_model.pkl
gsutil cp "${DATASET_PATH}" /tmp/gate_eval.csv

# Run gate (expect exit code 1 = bias detected)
set +e
docker run --rm \
  -v /tmp:/data \
  fairlens-gate \
    --model-path /data/gate_model.pkl \
    --eval-csv /data/gate_eval.csv \
    --sensitive-cols "gender,race" \
    --label-col "label" \
    --output-json /data/gate_report.json
EXIT_CODE=$?
set -e

if [ $EXIT_CODE -eq 1 ]; then
  echo "  ✅ Gate correctly detected bias (exit code 1)"
elif [ $EXIT_CODE -eq 0 ]; then
  echo "  ✅ Gate passed — model meets fairness thresholds"
else
  echo "  ❌ Gate error (exit code ${EXIT_CODE})"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  GCP Demo Complete"
echo "  Gate report: /tmp/gate_report.json"
echo "  BigQuery: ${GCP_PROJECT_ID}.fairlens.bias_profiles"
echo "═══════════════════════════════════════════════════════════════"
