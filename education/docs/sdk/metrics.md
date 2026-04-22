# Fairness Metrics Reference

FairLens computes 8 fairness metrics. Each metric measures a different aspect of algorithmic fairness.

## Metrics Summary

| Metric | Range | Fair Value | Threshold | Direction |
|--------|-------|------------|-----------|-----------|
| Demographic Parity Difference | [0, 1] | 0.0 | ≤ 0.10 | Lower = fairer |
| Equalized Odds Difference | [0, 1] | 0.0 | ≤ 0.10 | Lower = fairer |
| Disparate Impact Ratio | [0, 1] | 1.0 | ≥ 0.80 | Higher = fairer |
| Calibration Error | [0, 1] | 0.0 | ≤ 0.05 | Lower = fairer |
| Theil Index | [0, ∞) | 0.0 | ≤ 0.10 | Lower = fairer |
| Statistical Parity Difference | [0, 1] | 0.0 | ≤ 0.10 | Lower = fairer |
| Average Odds Difference | [0, 1] | 0.0 | ≤ 0.10 | Lower = fairer |
| Equal Opportunity Difference | [0, 1] | 0.0 | ≤ 0.10 | Lower = fairer |

## Detailed Descriptions

### Demographic Parity Difference (DPD)

**Formula:** `max(P(ŷ=1|A=g)) - min(P(ŷ=1|A=g))` across all groups g

**What it measures:** The gap in positive prediction rates across demographic groups. A DPD of 0.15 means the most-favored group is 15 percentage points more likely to receive a positive prediction than the least-favored group.

**When to use:** When equal selection rates across groups are legally or ethically required (e.g., hiring, lending).

### Disparate Impact Ratio (DIR)

**Formula:** `min(P(ŷ=1|A=g)) / max(P(ŷ=1|A=g))` across all groups g

**What it measures:** The ratio of the lowest to highest group selection rate. Based on the EEOC 4/5ths rule — a ratio below 0.80 is prima facie evidence of adverse impact.

**When to use:** Employment decisions, lending decisions, any context subject to EEOC or fair lending regulations.

### Equalized Odds Difference (EOD)

**Formula:** `max(|TPR_g1 - TPR_g2|, |FPR_g1 - FPR_g2|)` across all group pairs

**What it measures:** Whether the model's error rates (both false positives and true positives) are equal across groups. A model satisfies equalized odds when both TPR and FPR are equal across groups.

**When to use:** When both types of errors have significant consequences (e.g., criminal justice, healthcare triage).

### Equal Opportunity Difference

**Formula:** `max(TPR_g) - min(TPR_g)` across all groups g

**What it measures:** The gap in true positive rates across groups. Focuses only on whether qualified individuals are treated equally, regardless of how unqualified individuals are treated.

**When to use:** When the primary concern is that qualified candidates from all groups have equal chances of being selected.

### Calibration Error

**Formula:** `max(PPV_g) - min(PPV_g)` across all groups g  
Where PPV = Positive Predictive Value = P(y=1|ŷ=1)

**What it measures:** Whether a positive prediction means the same thing across groups. Perfect calibration means P(qualified | predicted qualified) is the same for all groups.

**When to use:** Risk scoring, credit scoring, and any context where the meaning of a score should be consistent across groups.

### Theil Index

**Formula:** Generalized Entropy Index with α=1

**What it measures:** An information-theoretic measure of inequality in prediction outcomes. Unlike pairwise metrics, the Theil Index captures multi-group inequality simultaneously.

**When to use:** When you have many groups and want a single summary statistic of overall inequality.

### Average Odds Difference

**Formula:** `0.5 * (|TPR_g1 - TPR_g2| + |FPR_g1 - FPR_g2|)` averaged across groups

**What it measures:** The average of the true positive rate and false positive rate differences. A smoother version of equalized odds that averages both error types.

### Statistical Parity Difference

**Formula:** Identical to Demographic Parity Difference

**What it measures:** Same as DPD — included as an alias for compatibility with different fairness frameworks.
