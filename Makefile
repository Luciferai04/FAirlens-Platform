.PHONY: setup test-p0 test-p1 test-p2 lint deploy-gate deploy-monitor deploy-console deploy-remediation publish-sdk infra-init infra-plan infra-apply

# ── Setup ──────────────────────────────────────────────────────────
setup:
	python3 -m venv .venv && . .venv/bin/activate && \
	pip install -e "sdk/[dev]" apache-beam[gcp] fairlearn scikit-learn shap ctgan \
	            reportlab google-cloud-aiplatform google-cloud-bigquery \
	            google-cloud-pubsub fastapi uvicorn pyyaml jinja2 \
	            google-generativeai google-cloud-kms google-cloud-spanner \
	            functions-framework google-cloud-firestore google-cloud-monitoring
	cd console/frontend && npm install

# ── Tests ──────────────────────────────────────────────────────────
test-p0:
	pytest sdk/tests/ -v --cov=fairlens --cov-report=term-missing
	pytest scanner/tests/ -v
	pytest gate/tests/ -v

test-p1:
	pytest monitor/tests/ -v
	pytest console/backend/tests/ -v
	pytest remediation/tests/ -v

test-p2:
	pytest compliance/tests/ -v
	pytest explainability/tests/ -v

lint:
	black --check sdk/ scanner/ gate/ monitor/ console/backend/ compliance/ remediation/
	mypy sdk/fairlens/ --ignore-missing-imports

# ── Deploy ─────────────────────────────────────────────────────────
deploy-gate:
	cd gate && docker build -t gcr.io/$$GCP_PROJECT_ID/fairlens-gate:latest . && \
	docker push gcr.io/$$GCP_PROJECT_ID/fairlens-gate:latest
	@echo "Gate image pushed. Add to cloudbuild.yaml or GitHub Actions."

deploy-monitor:
	cd infra && terraform apply -target=module.monitor -auto-approve
	cd monitor && python3 pipeline.py \
	  --runner=DataflowRunner \
	  --project=$$GCP_PROJECT_ID \
	  --region=$$GCP_REGION \
	  --subscription=projects/$$GCP_PROJECT_ID/subscriptions/fairlens-monitor-sub \
	  --model-id=$$VERTEX_ENDPOINT_ID \
	  --sensitive-cols=$$SENSITIVE_COLS \
	  --bq-output=$$GCP_PROJECT_ID:fairlens.equity_scores

deploy-console:
	cd console/backend && gcloud run deploy fairlens-api \
	  --source . --region $$GCP_REGION \
	  --service-account fairlens-sa@$$GCP_PROJECT_ID.iam.gserviceaccount.com \
	  --set-env-vars GCP_PROJECT_ID=$$GCP_PROJECT_ID,BQ_DATASET=fairlens
	cd console/frontend && npm run build && \
	gcloud run deploy fairlens-console --source . --region $$GCP_REGION

deploy-remediation:
	gcloud functions deploy generate-playbook \
	  --gen2 \
	  --runtime=python312 \
	  --region=$$GCP_REGION \
	  --source=remediation/function \
	  --entry-point=generate_playbook \
	  --trigger-topic=fairlens-bias-incidents \
	  --service-account=fairlens-sa@$$GCP_PROJECT_ID.iam.gserviceaccount.com \
	  --set-secrets=GEMINI_API_KEY=gemini-api-key:latest

publish-sdk:
	cd sdk && python3 -m build && twine upload dist/*
	@echo "SDK published to PyPI"

# ── Infrastructure ─────────────────────────────────────────────────
infra-init:
	cd infra && terraform init

infra-plan:
	cd infra && terraform plan -var="project_id=$$GCP_PROJECT_ID"

infra-apply:
	cd infra && terraform apply -var="project_id=$$GCP_PROJECT_ID" -auto-approve
