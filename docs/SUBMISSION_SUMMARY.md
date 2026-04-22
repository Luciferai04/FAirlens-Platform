# FairLens — Submission Summary

> **Google Solutions Challenge 2026**  
> **Team:** FairLens  
> **SDGs:** SDG 10 (Reduced Inequalities), SDG 16 (Peace, Justice & Strong Institutions)

---

## Problem Statement

AI systems deployed in high-stakes domains (lending, hiring, healthcare) frequently encode historical biases, leading to discriminatory outcomes across race, gender, and age groups. Organizations lack standardized tools to detect, monitor, and remediate these biases in production environments.

## Solution: FairLens

FairLens is an **end-to-end AI fairness governance platform** that provides:

1. **SDK** — Python library computing 8 fairness metrics (DPD, EO, DI, etc.) in a single `fairlens.audit()` call
2. **Scanner** — Apache Beam pipeline detecting 3 types of hidden dataset bias
3. **CI/CD Gate** — Docker container that blocks biased model deployments
4. **Console** — Full-stack governance dashboard (React + FastAPI)
5. **Compliance Engine** — Cryptographically signed audit reports for EU AI Act, EEOC, RBI-SEBI

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  fairlens    │    │   Scanner    │    │  Fairness    │
│  SDK         │───▶│  (Dataflow)  │───▶│  Gate (CI)   │
│  8 metrics   │    │  3 detectors │    │  Pass/Fail   │
└─────────────┘    └──────────────┘    └──────────────┘
       │                                      │
       ▼                                      ▼
┌──────────────────────────────────────────────────────┐
│                  BigQuery (Audit Store)               │
└──────────────────────────────────────────────────────┘
       │                      │                │
       ▼                      ▼                ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Console     │    │   Gemini     │    │  Cloud KMS   │
│  (Cloud Run) │    │  Playbooks   │    │  Signing     │
│  React + API │    │  + SHAP      │    │  + Spanner   │
└──────────────┘    └──────────────┘    └──────────────┘
```

## GCP Services Used

| Service | Purpose |
|---------|---------|
| **BigQuery** | Central audit report store, metric analytics |
| **Cloud Run** | Console frontend + FastAPI backend |
| **Vertex AI** | Model endpoint monitoring, inference |
| **Gemini 1.5 Pro** | Playbook generation, root cause analysis |
| **Cloud KMS** | Cryptographic signing of compliance reports |
| **Pub/Sub** | Event-driven bias scan triggers |
| **Cloud Build** | CI/CD fairness gate integration |
| **Spanner** | Immutable compliance audit ledger |
| **Dataflow** | Apache Beam bias scanner pipeline |

## Key Metrics

| Metric | Value |
|--------|-------|
| Total source files | 124 |
| Test suites | 8 |
| Tests passing | 77/77 ✅ |
| SDK code coverage | 83% |
| Fairness metrics | 8 |
| Scanner detectors | 3 |
| Compliance frameworks | 3 (EU AI Act, EEOC, RBI-SEBI) |
| Demo runtime | 0.2s |

## Impact

FairLens directly addresses SDG 10 and SDG 16 by:
- **Detecting** algorithmic discrimination before it affects real people
- **Blocking** biased models from reaching production via CI/CD gates
- **Generating** legally-compliant audit documentation automatically
- **Empowering** non-technical stakeholders with visual governance dashboards

## Demo

- **Video:** [Link to demo video]
- **Live Console:** [Cloud Run URL]
- **SDK:** `pip install fairlens`
- **GitHub:** [Repository URL]

## Team

- Soumyajit Ghosh — Full-stack development, MLOps, system architecture
