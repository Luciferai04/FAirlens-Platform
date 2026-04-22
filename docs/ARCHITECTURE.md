# Architecture

FairLens uses a 5-layer, event-driven architecture built entirely on Google Cloud Platform services.

## Layer Overview

```
Layer 1: Compute    → SDK computes 8 fairness metrics
Layer 2: Profile    → Scanner detects dataset-level bias
Layer 3: Enforce    → Gate blocks biased deployments in CI/CD
Layer 4: Detect     → Monitor catches live inference drift
Layer 5: Act        → Console + Gemini + Compliance respond to incidents
```

## Data Flow (7 Steps)

```
Step 1: Developer calls fairlens.audit(model, X, y, sensitive_cols)
           │
Step 2: SDK computes 8 metrics, returns AuditReport
           │    └──▶ AuditReport written to BigQuery (audit_reports table)
           │
Step 3: Scanner reads training CSV from GCS, runs 3 detectors
           │    └──▶ BiasProfile written to BigQuery (bias_profiles table)
           │
Step 4: Gate runs in CI/CD, loads model + eval data, calls SDK
           │    └──▶ Exit 0 (pass) or Exit 1 (fail, block deployment)
           │
Step 5: Monitor subscribes to Pub/Sub prediction stream
           │    └──▶ Page-Hinkley detects drift → Cloud Monitoring alert
           │    └──▶ If drift detected → publishes to bias-incidents topic
           │
Step 6: Remediation Cloud Function triggered by Pub/Sub
           │    └──▶ Gemini 1.5 Pro generates playbook → Firestore
           │    └──▶ Console displays playbook, requires human approval
           │
Step 7: Compliance generator creates PDF from audit data
                └──▶ PDF signed with Cloud KMS → SHA-256 hash stored
```

## GCP Service Selection Rationale

### BigQuery — Audit Data Warehouse
**Why:** BigQuery provides serverless, petabyte-scale analytics with built-in time partitioning and clustering. Audit reports are time-series data that grow linearly with model count — BigQuery handles this without capacity planning. Its SQL interface allows compliance teams to query audit history directly without engineering support.

### Cloud Pub/Sub — Event Bus
**Why:** Pub/Sub decouples the prediction logging, monitoring, and remediation layers. This is critical because:
- Prediction logging must not add latency to inference (fire-and-forget publishing)
- Multiple consumers (monitor, scanner, remediation) can independently subscribe
- At-least-once delivery guarantees no bias incident is silently dropped
- Dead-letter topics capture failed messages for debugging

### Apache Beam / Dataflow — Batch & Stream Processing
**Why:** Beam provides a unified programming model for both the batch scanner (D2) and streaming monitor (D4). Dataflow autoscales workers based on data volume — the scanner can profile a 10M-row dataset by distributing across hundreds of workers, while the monitor processes real-time prediction streams with sub-minute latency. This eliminates the need to maintain separate batch and streaming infrastructure.

### Gemini 1.5 Pro — Contextual Remediation Intelligence
**Why:** Traditional bias mitigation tools provide generic recommendations ("try reweighting"). Gemini 1.5 Pro generates contextually-aware remediation strategies that consider:
- The specific metric that failed and by how much
- The business domain (hiring vs. lending vs. healthcare)
- The model architecture (tree-based vs. neural network)
- Historical remediation patterns for similar incidents

Its structured JSON output mode (`response_mime_type="application/json"`) ensures machine-parseable playbooks that integrate directly into the engineering workflow.

### Cloud KMS — Tamper-Evident Compliance Artifacts
**Why:** Regulatory frameworks (EU AI Act, EEOC) require that compliance documentation cannot be retroactively modified. KMS asymmetric signing provides:
- Cryptographic proof that a PDF was generated at a specific time
- Non-repudiation: the signing key is managed by GCP, not the document creator
- Verifiability: any party can verify the signature using the public key
- Audit trail: Cloud Audit Logs record every signing operation

### Cloud Run — Serverless API & Console
**Why:** The FastAPI backend and React frontend are stateless services that benefit from Cloud Run's scale-to-zero model. During low traffic (nights, weekends), costs drop to zero. During audit season or incident response, Cloud Run autoscales to handle concurrent requests without infrastructure management.

### Firestore — Playbook Document Store
**Why:** Remediation playbooks are semi-structured documents with nested strategies, code snippets, and approval workflows. Firestore's document model maps naturally to this schema. Real-time listeners enable the Console to display playbook updates instantly without polling.

## Security Model

- **Authentication:** Firebase Auth with Google Identity Platform
- **Authorization:** RBAC with 4 roles: viewer, auditor, admin, owner
- **Data encryption:** All data encrypted at rest (Google-managed keys) and in transit (TLS 1.3)
- **Compliance signing:** Asymmetric RSA-4096 via Cloud KMS
- **Network:** VPC Service Controls for BigQuery and GCS access
