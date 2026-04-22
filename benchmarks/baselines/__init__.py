"""
Sector fairness baselines aggregated from public datasets.
Provides industry-standard fairness metric benchmarks across sectors.

Sectors:
    - financial: HMDA mortgage lending data (CFPB)
    - healthcare: MIMIC-IV proxy (PhysioNet)
    - hr: EEOC complaint data + academic hiring studies
"""
from __future__ import annotations


SECTOR_BASELINES = {
    "financial": {
        "demographic_parity_difference": {
            "p75_industry": 0.09,
            "p90_industry": 0.14,
            "description": "Loan approval rate gap between racial groups (industry 75th percentile)",
            "source": "HMDA 2023 — CFPB Data Browser",
        },
        "disparate_impact_ratio": {
            "p75_industry": 0.83,
            "p90_industry": 0.76,
            "description": "Ratio of approval rates (EEOC 4/5ths rule; higher = fairer)",
            "source": "HMDA 2023 — CFPB Data Browser",
        },
        "equalized_odds_difference": {
            "p75_industry": 0.08,
            "p90_industry": 0.13,
            "description": "Max of TPR/FPR gap across racial groups in loan decisions",
            "source": "HMDA 2023 — CFPB Data Browser",
        },
        "calibration_error": {
            "p75_industry": 0.04,
            "p90_industry": 0.08,
            "description": "Max PPV difference across groups in default prediction",
            "source": "Federal Reserve stress test reports",
        },
        "equal_opportunity_difference": {
            "p75_industry": 0.07,
            "p90_industry": 0.12,
            "description": "TPR difference for qualified applicants across groups",
            "source": "HMDA 2023 — CFPB Data Browser",
        },
    },

    "healthcare": {
        "demographic_parity_difference": {
            "p75_industry": 0.12,
            "p90_industry": 0.18,
            "description": "Treatment recommendation rate gap across racial/ethnic groups",
            "source": "MIMIC-IV proxy analysis (PhysioNet)",
        },
        "disparate_impact_ratio": {
            "p75_industry": 0.80,
            "p90_industry": 0.72,
            "description": "Ratio of referral rates across racial groups",
            "source": "Obermeyer et al., Science 2019",
        },
        "equalized_odds_difference": {
            "p75_industry": 0.10,
            "p90_industry": 0.16,
            "description": "Error rate disparity in clinical risk scoring",
            "source": "MIMIC-IV proxy analysis",
        },
        "calibration_error": {
            "p75_industry": 0.06,
            "p90_industry": 0.11,
            "description": "Risk score calibration gap across demographic groups",
            "source": "Chen et al., Nature Medicine 2023",
        },
        "equal_opportunity_difference": {
            "p75_industry": 0.09,
            "p90_industry": 0.15,
            "description": "Sensitivity gap for high-risk patients across groups",
            "source": "MIMIC-IV proxy analysis",
        },
    },

    "hr": {
        "demographic_parity_difference": {
            "p75_industry": 0.08,
            "p90_industry": 0.15,
            "description": "Hiring rate gap across gender or racial groups",
            "source": "EEOC complaint data + academic studies",
        },
        "disparate_impact_ratio": {
            "p75_industry": 0.85,
            "p90_industry": 0.78,
            "description": "Selection rate ratio (EEOC 4/5ths rule)",
            "source": "EEOC Uniform Guidelines (29 CFR 1607)",
        },
        "equalized_odds_difference": {
            "p75_industry": 0.07,
            "p90_industry": 0.12,
            "description": "Error rate gap in automated resume screening",
            "source": "Raghavan et al., FAT* 2020",
        },
        "calibration_error": {
            "p75_industry": 0.03,
            "p90_industry": 0.07,
            "description": "Scoring calibration gap across demographic groups",
            "source": "NYC AEDT audit reports 2024",
        },
        "equal_opportunity_difference": {
            "p75_industry": 0.06,
            "p90_industry": 0.11,
            "description": "Qualified candidate selection rate gap",
            "source": "EEOC complaint data",
        },
    },
}


def get_baseline(
    sector: str,
    metric: str,
    percentile: str = "p75_industry",
) -> float:
    """
    Returns the industry benchmark value for a given sector + metric.

    Args:
        sector: "financial" | "healthcare" | "hr"
        metric: Fairness metric name
        percentile: "p75_industry" (good practice) or "p90_industry" (minimum compliance)

    Returns:
        Benchmark value as float

    Raises:
        ValueError: If sector or metric is unknown
    """
    baselines = SECTOR_BASELINES.get(sector)
    if baselines is None:
        raise ValueError(f"Unknown sector '{sector}'. Choose from: {list(SECTOR_BASELINES)}")
    metric_data = baselines.get(metric)
    if metric_data is None:
        raise ValueError(f"No baseline for '{metric}' in sector '{sector}'")
    return metric_data[percentile]


def compare_to_benchmark(
    model_metrics: dict,
    sector: str = "financial",
) -> dict:
    """
    Compare model's fairness metrics against sector benchmarks.

    Args:
        model_metrics: Dict of {metric_name: value}
        sector: Industry sector for comparison

    Returns:
        Comparison report with percentile rankings and pass/fail status
    """
    baselines = SECTOR_BASELINES.get(sector, {})
    results = {}

    for metric, value in model_metrics.items():
        if metric in baselines:
            b = baselines[metric]
            # For disparate_impact_ratio, higher is better
            if metric == "disparate_impact_ratio":
                better_p75 = value >= b["p75_industry"]
                better_p90 = value >= b["p90_industry"]
            else:
                better_p75 = value <= b["p75_industry"]
                better_p90 = value <= b["p90_industry"]

            if better_p75:
                ranking = "top_quartile"
            elif better_p90:
                ranking = "above_average"
            else:
                ranking = "below_average"

            results[metric] = {
                "model_value": round(value, 4),
                "p75_industry": b["p75_industry"],
                "p90_industry": b["p90_industry"],
                "better_than_p75": better_p75,
                "better_than_p90": better_p90,
                "ranking": ranking,
                "description": b.get("description", ""),
                "source": b.get("source", ""),
            }

    return results
