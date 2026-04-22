# Loan Approval Bias Audit Tutorial

This tutorial demonstrates auditing a mortgage lending model using real HMDA benchmark data.

## Scenario

A bank deploys an ML model to pre-screen mortgage applications. Federal regulators require the bank to demonstrate compliance with the Equal Credit Opportunity Act (ECOA) and the EEOC 4/5ths rule for adverse impact analysis.

## Step 1: Load HMDA Benchmark Data

```python
from benchmarks.loaders.hmda import load_hmda_sample

# Load synthetic HMDA-like data (5000 applications)
df = load_hmda_sample(n_rows=5000)
print(f"Dataset: {len(df)} rows")
print(f"Approval rate: {df['approved'].mean():.2%}")
print(f"Approval by race:\n{df.groupby('race')['approved'].mean()}")
```

## Step 2: Train a Lending Model

```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split

features = ["loan_amount", "income", "debt_to_income", "property_value", "credit_score"]
X = df[features + ["race", "sex"]]
y = df["approved"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

model = GradientBoostingClassifier(n_estimators=200, random_state=42)
model.fit(X_train[features], y_train)
```

## Step 3: Audit for Racial Bias

```python
import fairlens

class LendingWrapper:
    def __init__(self, m, cols):
        self.m = m; self.cols = cols
    def predict(self, X):
        return self.m.predict(X[self.cols])

report = fairlens.audit(
    LendingWrapper(model, features),
    X_test, y_test,
    sensitive_cols=["race", "sex"],
    model_id="mortgage-model-v2",
)

print(f"Overall: {'PASS' if report.passed else 'FAIL'}")
for v in report.violations:
    print(f"  ⚠️  {v['col']}.{v['metric']}: {v['value']:.4f}")
```

## Step 4: Compare Against Industry Benchmarks

```python
from benchmarks import compare_to_benchmark

race_metrics = report.metrics.get("race", {})
comparison = compare_to_benchmark(race_metrics, sector="financial")

for metric, result in comparison.items():
    status = "✅" if result["better_than_p75"] else "⚠️"
    print(f"{status} {metric}: {result['model_value']:.4f} "
          f"(industry p75: {result['p75_industry']})")
```

## Step 5: Generate EEOC Compliance Report

```python
from compliance import generate_from_audit

generate_from_audit(report, "eeoc", "mortgage_eeoc_report.pdf", sign=False)
print("EEOC Adverse Impact Analysis saved!")
```
