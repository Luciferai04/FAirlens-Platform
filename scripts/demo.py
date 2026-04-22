#!/usr/bin/env python3
"""
FairLens P0 End-to-End Demo
============================
Demonstrates the full bias detection pipeline without requiring GCP credentials.

Usage:
    python scripts/demo.py
"""
from __future__ import annotations
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

start_time = time.time()

# ────────────────────────────────────────────────────────────────
# Step 1: Generate Synthetic Biased Hiring Dataset
# ────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  FairLens P0 Demo — Enterprise AI Bias Detection")
print("=" * 70)
print("\n[Step 1] Generating synthetic biased hiring dataset (1000 rows)...\n")

rng = np.random.RandomState(42)
n = 1000

gender = rng.choice(["male", "female"], n, p=[0.55, 0.45])
race = rng.choice(["White", "Black", "Asian", "Hispanic"], n, p=[0.45, 0.25, 0.15, 0.15])

years_experience = rng.poisson(5, n).clip(0, 30)
education_level = rng.choice([1, 2, 3, 4], n, p=[0.1, 0.3, 0.4, 0.2])
skill_score = rng.normal(70, 15, n).clip(0, 100).round(1)
interview_score = rng.normal(65, 12, n).clip(0, 100).round(1)

# Inject bias: P(hired=1 | female) = 0.35, P(hired=1 | male) = 0.62
hired = np.zeros(n, dtype=int)
for i in range(n):
    base_prob = 0.3 + 0.01 * years_experience[i] + 0.02 * education_level[i]
    if gender[i] == "male":
        base_prob += 0.20
    if race[i] == "White":
        base_prob += 0.05
    hired[i] = rng.binomial(1, min(max(base_prob, 0.05), 0.95))

df = pd.DataFrame({
    "years_experience": years_experience,
    "education_level": education_level,
    "skill_score": skill_score,
    "interview_score": interview_score,
    "gender": gender,
    "race": race,
    "hired": hired,
})

male_rate = df[df["gender"] == "male"]["hired"].mean()
female_rate = df[df["gender"] == "female"]["hired"].mean()
print(f"  Dataset: {len(df)} rows, {len(df.columns)} columns")
print(f"  P(hired=1 | male)   = {male_rate:.2f}")
print(f"  P(hired=1 | female) = {female_rate:.2f}")
print(f"  Actual DPD = {abs(male_rate - female_rate):.2f}")

# ────────────────────────────────────────────────────────────────
# Step 2: Train Random Forest Classifier
# ────────────────────────────────────────────────────────────────
print("\n[Step 2] Training RandomForestClassifier...\n")

features = ["years_experience", "education_level", "skill_score", "interview_score"]
X = df[features + ["gender", "race"]].copy()
X["gender_enc"] = (X["gender"] == "male").astype(int)
X["race_enc"] = pd.Categorical(X["race"]).codes
y = df["hired"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
model.fit(X_train[features + ["gender_enc", "race_enc"]], y_train)

# Wrap model to work with full DataFrame
class ModelWrapper:
    def __init__(self, model, feature_cols):
        self.model = model
        self.feature_cols = feature_cols
    def predict(self, X_df):
        X_copy = X_df.copy()
        if "gender_enc" not in X_copy.columns:
            X_copy["gender_enc"] = (X_copy["gender"] == "male").astype(int)
        if "race_enc" not in X_copy.columns:
            X_copy["race_enc"] = pd.Categorical(X_copy["race"]).codes
        return self.model.predict(X_copy[self.feature_cols])

wrapped = ModelWrapper(model, features + ["gender_enc", "race_enc"])
accuracy = (wrapped.predict(X_test) == y_test.values).mean()
print(f"  Model accuracy: {accuracy:.2%}")

# ────────────────────────────────────────────────────────────────
# Step 3: Run FairLens Audit
# ────────────────────────────────────────────────────────────────
print("\n[Step 3] Running fairlens.audit()...\n")

import fairlens

policy_path = os.path.join(os.path.dirname(__file__), "..", "gate", "policy", "default_policy.yaml")
if not os.path.exists(policy_path):
    policy_path = None

report = fairlens.audit(
    model=wrapped,
    X_test=X_test,
    y_test=y_test,
    sensitive_cols=["gender", "race"],
    threshold_config=policy_path,
    triggered_by="demo",
    model_id="hiring-model-v1",
)

# ────────────────────────────────────────────────────────────────
# Step 4: Display Results
# ────────────────────────────────────────────────────────────────
print("[Step 4] Audit Results:\n")

# Try rich/colorama for pretty output, fall back to plain
try:
    from rich.console import Console
    from rich.table import Table as RichTable
    console = Console()
    for col, col_metrics in report.metrics.items():
        table = RichTable(title=f"Metrics for '{col}'", show_lines=True)
        table.add_column("Metric", style="cyan", width=35)
        table.add_column("Value", justify="center", width=10)
        table.add_column("Threshold", justify="center", width=10)
        table.add_column("Status", justify="center", width=8)
        for metric_name, value in col_metrics.items():
            threshold = report.thresholds.get(metric_name, "—")
            if metric_name == "disparate_impact_ratio":
                is_pass = value >= threshold if isinstance(threshold, (int, float)) else True
            else:
                is_pass = abs(value) <= threshold if isinstance(threshold, (int, float)) else True
            status = "[green]PASS[/green]" if is_pass else "[red]FAIL[/red]"
            thr_str = f"{threshold:.4f}" if isinstance(threshold, float) else str(threshold)
            table.add_row(metric_name, f"{value:.4f}", thr_str, status)
        console.print(table)
        console.print()
except ImportError:
    for col, col_metrics in report.metrics.items():
        print(f"  --- Metrics for '{col}' ---")
        print(f"  {'Metric':<40} {'Value':>8} {'Threshold':>10} {'Status':>8}")
        print(f"  {'-'*40} {'-'*8} {'-'*10} {'-'*8}")
        for metric_name, value in col_metrics.items():
            threshold = report.thresholds.get(metric_name, "—")
            if metric_name == "disparate_impact_ratio":
                is_pass = value >= threshold if isinstance(threshold, (int, float)) else True
            else:
                is_pass = abs(value) <= threshold if isinstance(threshold, (int, float)) else True
            status = "PASS" if is_pass else "FAIL"
            thr_str = f"{threshold:.4f}" if isinstance(threshold, float) else str(threshold)
            print(f"  {metric_name:<40} {value:>8.4f} {thr_str:>10} {status:>8}")
        print()

overall = "PASSED" if report.passed else "FAILED"
print(f"  Overall: {overall}")
if report.violations:
    print(f"  Violations ({len(report.violations)}):")
    for v in report.violations:
        print(f"    - {v['col']}.{v['metric']}: {v['value']:.4f} ({v['direction']} threshold {v['threshold']:.4f})")

# ────────────────────────────────────────────────────────────────
# Step 5: Generate HTML Report
# ────────────────────────────────────────────────────────────────
print("\n[Step 5] Generating HTML report...\n")

output_dir = os.path.join(os.path.dirname(__file__), "..", "demo_output")
os.makedirs(output_dir, exist_ok=True)
html_path = os.path.join(output_dir, "audit_report.html")
with open(html_path, "w") as f:
    f.write(report.to_html())
print(f"  HTML report saved to: {html_path}")

# Also save JSON
json_path = os.path.join(output_dir, "audit_report.json")
with open(json_path, "w") as f:
    f.write(report.to_json())
print(f"  JSON report saved to: {json_path}")

# ────────────────────────────────────────────────────────────────
# Step 6: Generate Compliance PDF
# ────────────────────────────────────────────────────────────────
print("\n[Step 6] Generating EU AI Act compliance PDF...\n")
try:
    from compliance.generator import generate_from_audit
    pdf_path = os.path.join(output_dir, "compliance_eu_ai_act.pdf")
    sha = generate_from_audit(report, "eu_ai_act", pdf_path, sign=False)
    print(f"  PDF report saved to: {pdf_path}")
    print(f"  SHA-256: {sha}")
except ImportError as e:
    print(f"  Skipping PDF (missing dependency: {e})")
    print("  Install with: pip install reportlab")

# ────────────────────────────────────────────────────────────────
# Step 7: Simulated Remediation Playbook
# ────────────────────────────────────────────────────────────────
print("\n[Step 7] Simulated Gemini Remediation Playbook:\n")

playbook = {
    "playbook_id": "demo-playbook-001",
    "incident_id": "DPD-gender-violation",
    "root_cause_analysis": (
        "The hiring model exhibits significant gender-based bias, likely stemming from "
        "historical hiring data where male candidates were disproportionately selected. "
        "The model has learned to use gender-correlated features (e.g., years_experience) "
        "as proxies, amplifying existing societal biases."
    ),
    "strategies": [
        {
            "name": "Threshold Adjustment (Post-Processing)",
            "technique": "threshold_adjustment",
            "description": "Apply group-specific decision thresholds to equalize positive prediction rates.",
            "code_snippet": "from fairlearn.postprocessing import ThresholdOptimizer\nto = ThresholdOptimizer(estimator=model, constraints='demographic_parity')\nto.fit(X_train, y_train, sensitive_features=train_gender)",
            "estimated_effort": "low",
        },
        {
            "name": "Reweighting Training Data",
            "technique": "reweighting",
            "description": "Apply sample weights inversely proportional to group representation and label rate.",
            "code_snippet": "from fairlearn.reductions import ExponentiatedGradient, DemographicParity\nmitigator = ExponentiatedGradient(estimator, DemographicParity())\nmitigator.fit(X_train, y_train, sensitive_features=train_gender)",
            "estimated_effort": "medium",
        },
        {
            "name": "Feature Audit and Proxy Removal",
            "technique": "feature_removal",
            "description": "Use mutual information to identify and remove proxy features correlated with gender.",
            "code_snippet": "from sklearn.feature_selection import mutual_info_classif\nmi = mutual_info_classif(X_train, gender_encoded)\nproxy_features = [f for f, s in zip(X.columns, mi) if s > 0.1]",
            "estimated_effort": "low",
        },
    ],
    "priority_order": [
        "Threshold Adjustment (Post-Processing)",
        "Reweighting Training Data",
        "Feature Audit and Proxy Removal",
    ],
}
print(json.dumps(playbook, indent=2))

# ────────────────────────────────────────────────────────────────
# Summary
# ────────────────────────────────────────────────────────────────
elapsed = time.time() - start_time
print(f"\n{'=' * 70}")
print(f"  Demo complete in {elapsed:.1f}s")
print(f"  Outputs saved to: {os.path.abspath(output_dir)}/")
print(f"{'=' * 70}\n")
