# Hiring Model Bias Audit — Full Tutorial

This tutorial demonstrates a complete bias audit of a hiring model, including synthetic data generation, bias detection, remediation playbook, and compliance reporting.

## Scenario

A company uses a RandomForest classifier to screen job applications. The model was trained on 3 years of historical hiring data. HR has concerns that the model may be unfairly disadvantaging female candidates.

## Step 1: Generate the Dataset

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

rng = np.random.RandomState(42)
n = 1000

# Features
years_experience = rng.poisson(5, n).clip(0, 30)
education_level = rng.choice([1, 2, 3, 4], n, p=[0.1, 0.3, 0.4, 0.2])
skill_score = rng.normal(70, 15, n).clip(0, 100).round(1)
interview_score = rng.normal(65, 12, n).clip(0, 100).round(1)
gender = rng.choice(["male", "female"], n, p=[0.55, 0.45])

# Inject bias: males hired at ~62%, females at ~35%
hired = np.zeros(n, dtype=int)
for i in range(n):
    p = 0.3 + 0.01 * years_experience[i] + 0.02 * education_level[i]
    if gender[i] == "male": p += 0.20
    hired[i] = rng.binomial(1, min(max(p, 0.05), 0.95))

df = pd.DataFrame({
    "years_experience": years_experience,
    "education_level": education_level,
    "skill_score": skill_score,
    "interview_score": interview_score,
    "gender": gender,
    "hired": hired,
})
```

## Step 2: Train and Audit

```python
import fairlens

features = ["years_experience", "education_level", "skill_score", "interview_score"]
X = df[features + ["gender"]]
y = df["hired"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train[features], y_train)

class ModelWrapper:
    def __init__(self, m, cols):
        self.m = m; self.cols = cols
    def predict(self, X):
        return self.m.predict(X[self.cols])

report = fairlens.audit(
    ModelWrapper(model, features), X_test, y_test,
    sensitive_cols=["gender"], model_id="hiring-model-v1"
)

print(f"Passed: {report.passed}")
print(f"Violations: {len(report.violations)}")
for v in report.violations:
    print(f"  ⚠️  {v['metric']}: {v['value']:.4f} (threshold: {v['threshold']:.4f})")
```

## Step 3: Benchmark Against Industry

```python
from benchmarks import compare_to_benchmark

model_metrics = report.metrics.get("gender", {})
comparison = compare_to_benchmark(model_metrics, sector="hr")

for metric, result in comparison.items():
    print(f"{metric}: {result['ranking']} "
          f"(model={result['model_value']:.4f}, "
          f"p75={result['p75_industry']})")
```

## Step 4: Explain the Bias

```python
from explainability import compute_disparity_drivers

drivers = compute_disparity_drivers(ModelWrapper(model, features), X_test, "gender")
print("\nBias Disparity Drivers:")
for feature, info in drivers.items():
    flag = "⚠️ PROXY RISK" if info["is_proxy_risk"] else "✓"
    print(f"  {feature}: disparity={info['disparity']:.4f} {flag}")
```

## Step 5: Debias the Dataset

```python
from debiaser import augment_underrepresented

augmented_df, report = augment_underrepresented(df, "gender", strategy="equalize", epochs=1)
print(f"\nOriginal: {df['gender'].value_counts().to_dict()}")
print(f"Augmented: {augmented_df['gender'].value_counts().to_dict()}")
```

## Step 6: Generate Compliance Report

```python
from compliance import generate_from_audit

generate_from_audit(report, "eeoc", "hiring_eeoc_report.pdf", sign=False)
print("EEOC compliance report generated!")
```
