# Impact Metrics

FairLens tracks 6 key performance indicators (KPIs) that map directly to real-world impact for affected communities and organizations.

## KPI Dashboard

| # | KPI | Baseline | Target | Measurement Method | What This Means in Human Terms |
|---|-----|----------|--------|--------------------|-------------------------------|
| 1 | **Fairness Coverage** | 0% of models audited | 100% of production models have automated fairness audits | Count of models with at least one `fairlens.audit()` run in the last 30 days ÷ total registered models | Every AI system making decisions about people's lives — hiring, lending, healthcare — is being checked for bias. No model ships without a fairness report. |
| 2 | **Detection Latency** | Days to weeks (manual review) | < 5 minutes from prediction to drift alert | Time between a biased prediction entering Pub/Sub and the Page-Hinkley detector firing a Cloud Monitoring alert | When an AI system starts treating a demographic group unfairly, the team knows within minutes — not after thousands of people have been harmed. |
| 3 | **Remediation Rate** | 0% (no automated playbooks) | 80% of incidents have an approved remediation playbook within 24 hours | Count of incidents with status="approved" within 24h ÷ total incidents | For every bias incident detected, there's a concrete action plan with code snippets ready for engineers to implement — no more "we'll look into it" delays. |
| 4 | **Developer Onboarding** | N/A (no unified tool exists) | < 10 minutes from `pip install fairlens` to first audit report | Measured by the demo script: time from import to `report.to_json()` output | Any ML engineer can add fairness checks to their model with 3 lines of code. Fairness becomes as easy as `model.fit()`. |
| 5 | **Compliance Cost Savings** | $50K–$200K per manual compliance report (consultant fees) | $0 marginal cost per report (automated generation) | Compare cost of `compliance.generate()` (compute only) vs. external audit firm quotes | Organizations can generate EU AI Act and EEOC compliance documentation instantly instead of hiring expensive consultants — making fairness affordable for startups, not just enterprises. |
| 6 | **Model Equity Score** | Unknown (no continuous measurement) | All production models maintain equity score ≥ 0.85 | Rolling 7-day average of `custom.googleapis.com/fairlens/equity_score` metric across all models | This is the north star: a single number that tells you whether your AI systems are treating people fairly. An equity score of 0.85+ means the model's predictions are within acceptable fairness bounds across all demographic groups. |

## How We Measure Impact

### For Affected Communities
- **Reduction in disparate impact:** Track the aggregate disparate impact ratio across all monitored models. Target: all models above the 0.80 EEOC threshold.
- **Faster incident resolution:** Measure mean time to remediation (MTTR) for bias incidents. Target: < 24 hours from detection to approved playbook.
- **Transparency:** Every audit report is available as HTML, JSON, and signed PDF — providing an auditable record that affected individuals and regulators can review.

### For Organizations
- **Regulatory readiness:** Number of models with current compliance documentation (EU AI Act Annex IV, EEOC analysis).
- **Pipeline integration:** Percentage of CI/CD pipelines with the fairness gate enabled.
- **Cost avoidance:** Estimated regulatory fine exposure avoided through proactive bias detection.

### Measurement Infrastructure
All metrics are computed automatically via:
- BigQuery audit trail (`fairlens.audit_reports`, `fairlens.bias_incidents`)
- Cloud Monitoring custom metrics (`fairlens/equity_score`)
- Firestore playbook documents (remediation tracking)
