"""
HMDA (Home Mortgage Disclosure Act) dataset loader.
Source: https://ffiec.cfpb.gov/data-browser/
This is public US government data — no license restrictions.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from ..baselines import SECTOR_BASELINES, compare_to_benchmark


HMDA_BQ_TABLE = "fairlens-benchmarks.financial.hmda_2023"


def get_baseline(metric: str, percentile: str = "p75_industry") -> float:
    """
    Returns the financial industry benchmark value for a given metric.
    Use p75_industry for good practice, p90_industry for minimum compliance.
    """
    baselines = SECTOR_BASELINES.get("financial", {})
    metric_data = baselines.get(metric)
    if metric_data is None:
        raise ValueError(f"No financial baseline for metric '{metric}'")
    return metric_data[percentile]


def load_hmda_sample(n_rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic HMDA-like dataset for local development.
    In production, use load_hmda_from_bq() to query real HMDA data.

    Returns:
        DataFrame with columns: loan_amount, income, debt_to_income,
        property_value, race, sex, approved
    """
    rng = np.random.RandomState(seed)

    race = rng.choice(
        ["White", "Black", "Asian", "Hispanic", "Other"],
        n_rows, p=[0.55, 0.15, 0.12, 0.13, 0.05],
    )
    sex = rng.choice(["Male", "Female"], n_rows, p=[0.58, 0.42])

    income = rng.lognormal(mean=11.0, sigma=0.7, size=n_rows).round(0)
    loan_amount = (income * rng.uniform(2.0, 5.0, n_rows)).round(0)
    debt_to_income = rng.uniform(0.1, 0.6, n_rows).round(2)
    property_value = (loan_amount * rng.uniform(1.0, 1.5, n_rows)).round(0)
    credit_score = rng.normal(700, 60, n_rows).clip(300, 850).round(0)

    # Inject realistic bias patterns
    approved = np.zeros(n_rows, dtype=int)
    for i in range(n_rows):
        base = 0.5 + 0.0001 * (credit_score[i] - 600) - 0.5 * debt_to_income[i]
        if race[i] == "White":
            base += 0.08
        elif race[i] == "Black":
            base -= 0.05
        if sex[i] == "Male":
            base += 0.03
        approved[i] = rng.binomial(1, min(max(base, 0.05), 0.95))

    return pd.DataFrame({
        "loan_amount": loan_amount,
        "income": income,
        "debt_to_income": debt_to_income,
        "property_value": property_value,
        "credit_score": credit_score,
        "race": race,
        "sex": sex,
        "approved": approved,
    })


def load_hmda_from_bq(project: str, limit: int = 100000) -> pd.DataFrame:
    """
    Load real HMDA data from BigQuery Analytics Hub listing.
    Requires GCP credentials and BigQuery access.
    """
    from google.cloud import bigquery
    client = bigquery.Client(project=project)
    query = f"""
        SELECT
            loan_amount, income, debt_to_income_ratio as debt_to_income,
            property_value, derived_race as race, derived_sex as sex,
            CASE WHEN action_taken = 1 THEN 1 ELSE 0 END as approved
        FROM `{HMDA_BQ_TABLE}`
        LIMIT {limit}
    """
    return client.query(query).to_dataframe()
