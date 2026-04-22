# FairLens — Enterprise AI Bias Detection & Governance Platform

**One-line pitch:** FairLens is a developer-first, GCP-native platform that detects, monitors, and remediates bias in production ML systems — turning AI fairness from an afterthought into an automated, auditable pipeline.

<p align="center">
  <img src="https://img.shields.io/badge/SDG%2010-Reduced%20Inequalities-e5243b?style=for-the-badge" alt="SDG 10" />
  <img src="https://img.shields.io/badge/SDG%2016-Peace%20%26%20Justice-00689d?style=for-the-badge" alt="SDG 16" />
  <img src="https://img.shields.io/badge/Google%20Cloud-Solutions%20Challenge-4285F4?style=for-the-badge&logo=google-cloud" alt="Solutions Challenge" />
</p>

---

## 🌍 SDG Alignment

### SDG 10 — Reduced Inequalities
Algorithmic decision systems in hiring, lending, and healthcare disproportionately impact marginalized communities. FairLens directly addresses this by embedding fairness metrics into the ML lifecycle — ensuring AI systems treat all demographic groups equitably.

### SDG 16 — Peace, Justice, and Strong Institutions
The EU AI Act mandates bias auditing for high-risk AI. EEOC guidelines require adverse impact analysis. FairLens automates compliance with these frameworks, generating tamper-evident, KMS-signed PDF reports that stand up to regulatory scrutiny.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FairLens 5-Layer Architecture                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ SDK     │───▶│ Scanner  │───▶│  Gate    │───▶│ Monitor  │  │
│  │ (PyPI)  │    │(Dataflow)│    │ (CI/CD)  │    │(Streaming│  │
│  └────┬────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘  │
│       │              │               │               │         │
│  Layer 1:        Layer 2:        Layer 3:        Layer 4:      │
│  Compute         Profile         Enforce         Detect        │
│  8 fairness      3 dataset       Block biased    Page-Hinkley  │
│  metrics         detectors       deployments     drift detect  │
│       │              │               │               │         │
│       └──────────────┴───────┬───────┴───────────────┘         │
│                              │                                  │
│                    ┌─────────▼──────────┐                      │
│                    │   Layer 5: Act     │                      │
│                    │  ┌──────────────┐  │                      │
│                    │  │   Console    │  │  React + FastAPI     │
│                    │  │  (Cloud Run) │  │                      │
│                    │  └──────┬───────┘  │                      │
│                    │         │          │                      │
│                    │  ┌──────▼───────┐  │                      │
│                    │  │   Gemini     │  │  Remediation         │
│                    │  │  Remediation │  │  Playbooks           │
│                    │  └──────┬───────┘  │                      │
│                    │         │          │                      │
│                    │  ┌──────▼───────┐  │                      │
│                    │  │  Compliance  │  │  EU AI Act / EEOC    │
│                    │  │  (KMS-signed)│  │  PDF Reports         │
│                    │  └──────────────┘  │                      │
│                    └────────────────────┘                      │
│                                                                 │
│  ── GCP Services ──────────────────────────────────────────    │
│  BigQuery · Pub/Sub · Dataflow · Cloud Run · Cloud Functions   │
│  Gemini 1.5 Pro · Cloud KMS · Artifact Registry · Firestore   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Clone and setup
git clone https://github.com/your-org/fairlens.git && cd fairlens
python3 -m venv .venv && source .venv/bin/activate
pip install -e "sdk/[dev]" scikit-learn reportlab pypdf

# 2. Run the demo (no GCP needed)
python scripts/demo.py

# 3. Run all tests
make test-p0
```

---

## 📋 Feature Matrix

| # | Deliverable | Phase | Component | Status |
|---|-------------|-------|-----------|--------|
| D1 | Core SDK — 8 Fairness Metrics | P0 | `sdk/` | ✅ |
| D2 | Data Profiler & Bias Scanner | P0 | `scanner/` | ✅ |
| D3 | CI/CD Fairness Gate | P0 | `gate/` | ✅ |
| D4 | Real-Time Inference Monitor | P1 | `monitor/` | ✅ |
| D5 | Enterprise Console (BE + FE) | P1 | `console/` | ✅ |
| D6 | Gemini Remediation Engine | P1 | `remediation/` | ✅ |
| D7 | Compliance Report Generator | P2 | `compliance/` | ✅ |
| D8 | Synthetic Data Debiaser | P2 | `debiaser/` | ✅ |
| D9 | Explainability Overlay | P2 | `explainability/` | ✅ |
| D10 | Benchmark Suite | P3 | `benchmarks/` | ✅ |
| D11 | Education Hub | P3 | `education/` | ✅ |

---

## 📂 Repository Structure

```
fairlens/
├── sdk/                  # Python SDK — fairlens.audit()
├── scanner/              # Apache Beam dataset profiler
├── gate/                 # CI/CD fairness gate + Docker + GitHub Actions
├── monitor/              # Real-time Pub/Sub + Dataflow monitor
├── console/              # Enterprise UI (FastAPI + React)
├── remediation/          # Gemini-powered playbook generator
├── compliance/           # Regulatory PDF reports (EU AI Act, EEOC)
├── infra/                # Terraform GCP infrastructure
├── scripts/              # Demo scripts and setup utilities
├── tests/                # Acceptance test suite
└── docs/                 # Problem statement, architecture, impact
```

---

## 🔗 Demo & Documentation

- **Local demo (no GCP):** `python scripts/demo.py`
- **GCP demo:** `bash scripts/demo_gcp.sh`
- [Problem Statement](docs/PROBLEM_STATEMENT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Impact Metrics](docs/IMPACT_METRICS.md)

---

## License

Apache 2.0
