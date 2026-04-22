# FairLens Documentation

Welcome to the FairLens documentation — the enterprise AI bias detection and governance platform built on Google Cloud.

## What is FairLens?

FairLens embeds fairness directly into the ML lifecycle. It provides automated bias detection, real-time monitoring, and regulatory compliance reporting for production AI systems.

## Quick Start

```python
import fairlens

report = fairlens.audit(
    model=your_model,
    X_test=X_test,
    y_test=y_test,
    sensitive_cols=["gender", "race"],
)

print(report.to_json())
```

That's it. Three lines to audit any sklearn-compatible model for 8 fairness metrics.

## Platform Components

| Component | What It Does | Where It Runs |
|-----------|-------------|---------------|
| **SDK** | Computes 8 fairness metrics | `pip install fairlens` |
| **Scanner** | Profiles training data for bias | Cloud Dataflow |
| **Gate** | Blocks biased deployments | CI/CD (Docker) |
| **Monitor** | Detects live fairness drift | Cloud Dataflow Streaming |
| **Console** | Enterprise dashboard | Cloud Run |
| **Remediation** | AI-powered mitigation playbooks | Cloud Functions + Gemini |
| **Compliance** | Regulatory PDF reports | KMS-signed PDFs |
| **Debiaser** | Synthetic data augmentation | Vertex AI Training |
| **Explainability** | SHAP per-group attribution | SHAP + BigQuery |
| **Benchmarks** | Industry fairness baselines | REST API |

## SDG Alignment

FairLens addresses two UN Sustainable Development Goals:

- **SDG 10 — Reduced Inequalities**: Ensuring AI systems treat all demographic groups equitably
- **SDG 16 — Peace, Justice & Strong Institutions**: Automating compliance with EU AI Act and EEOC regulations
