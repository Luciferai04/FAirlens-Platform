ill attach their # FairLens — Demo Script (3-Minute Video)

> **Target:** Google Solutions Challenge 2026  
> **SDG Alignment:** SDG 10 (Reduced Inequalities), SDG 16 (Peace, Justice & Strong Institutions)

---

## Opening (0:00 – 0:20) — The Problem

**Narration:** *"AI systems deployed in banking, healthcare, and HR are making decisions that affect millions of lives. But these models often encode historical biases — denying loans, filtering resumes, and triaging patients unfairly across racial, gender, and age groups."*

**Visual:** Show a brief montage of headlines about AI bias in lending and hiring.

---

## Demo Step 1 (0:20 – 0:40) — The SDK

**Narration:** *"FairLens is an end-to-end AI governance platform. It starts with a Python SDK that computes 8 fairness metrics in a single call."*

**Visual:** Terminal showing:
```python
import fairlens
report = fairlens.audit(df, label_col="approved", protected_cols=["race", "gender"])
print(report)  # → AuditReport: 2/8 metrics FAILING
```

---

## Demo Step 2 (0:40 – 1:10) — The Console

**Narration:** *"The Governance Console gives risk teams real-time visibility across all deployed models."*

**Visual:** Walk through these screens:
1. **Dashboard** — Show 5 models monitored, 4 active incidents, 0.78 avg equity score
2. **Model Registry** — Click on "Loan Approval Engine" → show failing status, equity bars
3. **Model Detail** — Radar chart showing 8 metrics, 30-day trend line, SHAP heatmap

---

## Demo Step 3 (1:10 – 1:40) — Incident Response

**Narration:** *"When a fairness threshold is breached, FairLens automatically generates remediation playbooks powered by Gemini."*

**Visual:**
1. **Incident Log** — Show INC-8921 (Loan Origination, Critical severity)
2. Click **"Playbook"** button → slide panel opens
3. Show 3 strategies: Threshold Adjustment (Low effort), Reweighting (Medium), Feature Excision (High)
4. Click **"Approve & Execute"** → toast notification confirms

---

## Demo Step 4 (1:40 – 2:10) — Compliance

**Narration:** *"Every audit is cryptographically signed with Cloud KMS and stored as an immutable compliance artifact."*

**Visual:**
1. **Compliance Ledger** — Show 4 reports with KMS signatures and SHA-256 hashes
2. Click **"Generate Report"** → select EU AI Act framework
3. Show generated PDF with compliance sections

---

## Demo Step 5 (2:10 – 2:40) — The Pipeline

**Narration:** *"FairLens integrates directly into CI/CD pipelines as a fairness gate. If a model fails the 4/5ths rule, the deployment is automatically blocked."*

**Visual:** Show GitHub Actions workflow with:
- ✅ `fair-model` → gate passes, deploy succeeds
- ❌ `biased-model` → gate fails, PR is blocked with violation details

---

## Closing (2:40 – 3:00) — Impact & Architecture

**Narration:** *"FairLens is built entirely on Google Cloud — BigQuery for analytics, Vertex AI for serving, Gemini for explainability, and Cloud Run for scalable deployment. Together, these tools make AI governance accessible to every organization."*

**Visual:** Architecture diagram showing:
- SDK → Scanner (Dataflow) → Gate (CI/CD) → Console (Cloud Run)
- BigQuery ↔ Gemini → Compliance Reports
- Cloud KMS → Spanner (audit trail)

---

## GCP Services Used

| Service | Purpose |
|---------|---------|
| BigQuery | Audit report storage, metric analytics |
| Cloud Run | Console frontend + API backend |
| Vertex AI | Model endpoint monitoring |
| Gemini | Playbook generation, SHAP explanations |
| Cloud KMS | Compliance report signing |
| Pub/Sub | Event-driven scan triggers |
| Cloud Build | CI/CD fairness gate |
| Spanner | Immutable compliance ledger |
| Dataflow | Bias scanner pipeline |
