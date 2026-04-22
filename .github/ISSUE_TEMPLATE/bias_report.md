---
name: Bias Report
about: Report a bias incident discovered using FairLens
title: "[BIAS] "
labels: bias-incident, needs-triage
assignees: ''
---

## Bias Incident Report

### Model Information
- **Model Type:** <!-- e.g., Classification, Regression, Ranking -->
- **Model ID:** <!-- FairLens model identifier, if registered -->
- **Framework:** <!-- sklearn, TensorFlow, PyTorch, Vertex AI, etc. -->
- **Domain:** <!-- Hiring, Lending, Healthcare, Insurance, etc. -->

### Dataset Description
- **Dataset Name/Source:** <!-- e.g., "internal hiring data Q1 2024" -->
- **Dataset Size:** <!-- number of rows -->
- **Protected Attributes Analysed:** <!-- e.g., gender, race, age_group -->
- **Label Column:** <!-- e.g., hired, approved, diagnosed -->

### Metric Values

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Demographic Parity Difference | | 0.10 | |
| Equalized Odds Difference | | 0.10 | |
| Disparate Impact Ratio | | 0.80 | |
| Calibration Error | | 0.05 | |
| Equal Opportunity Difference | | 0.10 | |

### Affected Population
- **Most impacted group:** <!-- e.g., "Female applicants" -->
- **Estimated number of affected individuals:** <!-- if known -->
- **Nature of impact:** <!-- e.g., "Lower selection rate", "Higher false positive rate" -->

### Severity
<!-- Choose one -->
- [ ] **Critical** — Disparate impact ratio < 0.60 or DPD > 0.30
- [ ] **High** — Disparate impact ratio 0.60-0.75 or DPD 0.20-0.30
- [ ] **Medium** — Disparate impact ratio 0.75-0.80 or DPD 0.10-0.20
- [ ] **Low** — Marginal threshold violation

### Steps to Reproduce
1. <!-- How to reproduce the bias finding -->
2. <!-- e.g., "Run: fairlens.audit(model, X, y, ['gender'])" -->
3. <!-- Include code snippets if possible -->

### FairLens Audit Report
<!-- Paste the JSON output of report.to_json() or attach the HTML report -->
```json

```

### Additional Context
<!-- Any other context, screenshots, or related issues -->
