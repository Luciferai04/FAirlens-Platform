# Quick Audit Tutorial

This tutorial walks you through auditing a machine learning model for bias in under 5 minutes.

## Step 1: Prepare Your Data

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Load your dataset (must include protected attribute columns)
df = pd.read_csv("your_dataset.csv")
X = df.drop(columns=["label"])
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

# Train your model
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train.drop(columns=["gender", "race"]), y_train)
```

## Step 2: Run the Audit

```python
import fairlens

report = fairlens.audit(
    model=model,
    X_test=X_test,
    y_test=y_test,
    sensitive_cols=["gender", "race"],  # Protected attributes to check
    model_id="my-model-v1",            # Optional identifier
)
```

## Step 3: Interpret Results

```python
# Check if the model passed all thresholds
print(f"Passed: {report.passed}")
print(f"Violations: {len(report.violations)}")

# View all metrics
for col, metrics in report.metrics.items():
    print(f"\n--- {col} ---")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")

# Export reports
report.to_html()   # → HTML string with styled table
report.to_json()   # → JSON string
```

## Step 4: Generate Compliance Report

```python
from compliance import generate_from_audit

generate_from_audit(report, "eu_ai_act", "compliance_report.pdf")
```

## What the Metrics Mean

| Metric | What It Measures | Threshold | Rule |
|--------|-----------------|-----------|------|
| Demographic Parity Difference | Gap in positive prediction rates | ≤ 0.10 | Lower = fairer |
| Disparate Impact Ratio | Ratio of lowest to highest group rate | ≥ 0.80 | EEOC 4/5ths rule |
| Equalized Odds Difference | Max TPR/FPR gap across groups | ≤ 0.10 | Lower = fairer |
| Equal Opportunity Difference | TPR gap for qualified candidates | ≤ 0.10 | Lower = fairer |
| Calibration Error | PPV gap across groups | ≤ 0.05 | Lower = fairer |
| Theil Index | Information-theoretic inequality | ≤ 0.10 | Lower = fairer |
| Statistical Parity Difference | Same as DPD (alias) | ≤ 0.10 | Lower = fairer |
| Average Odds Difference | Average of TPR and FPR gaps | ≤ 0.10 | Lower = fairer |
