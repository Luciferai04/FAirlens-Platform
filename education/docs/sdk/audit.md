# `fairlens.audit()`

The core function that runs a complete fairness audit on any sklearn-compatible model.

## Signature

```python
def audit(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    sensitive_cols: list[str],
    threshold_config: dict | str | None = None,
    model_id: str | None = None,
) -> AuditReport
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | Any | sklearn-compatible model with `.predict()` method |
| `X_test` | DataFrame | Test features (must include sensitive_col columns) |
| `y_test` | Series | True labels |
| `sensitive_cols` | list[str] | Protected attribute column names to audit |
| `threshold_config` | dict/str/None | Threshold policy — dict, YAML path, or None for defaults |
| `model_id` | str/None | Optional model identifier for report tracking |

## Returns

An `AuditReport` object containing all computed metrics, pass/fail status, and violations.

## Default Thresholds

```yaml
demographic_parity_difference: 0.10
equalized_odds_difference: 0.10
disparate_impact_ratio: 0.80
calibration_error: 0.05
theil_index: 0.10
statistical_parity_difference: 0.10
average_odds_difference: 0.10
equal_opportunity_difference: 0.10
```

## Example

```python
import fairlens
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier()
model.fit(X_train, y_train)

report = fairlens.audit(model, X_test, y_test, ["gender", "race"])
print(report.passed)         # True/False
print(report.violations)     # List of threshold violations
print(report.to_json())      # Full JSON report
```
