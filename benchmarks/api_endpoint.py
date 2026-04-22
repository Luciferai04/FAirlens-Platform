"""
REST API endpoints for the sector benchmark library.
Mounted at /v1/benchmarks/ in the console backend.

Usage:
    GET  /v1/benchmarks/financial/demographic_parity_difference
    POST /v1/benchmarks/financial/compare  (body: {metric: value, ...})
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from .baselines import SECTOR_BASELINES, compare_to_benchmark, get_baseline

router = APIRouter(prefix="/v1/benchmarks", tags=["benchmarks"])

SECTORS = list(SECTOR_BASELINES.keys())


@router.get("/{sector}/{metric}")
async def get_benchmark_endpoint(
    sector: str,
    metric: str,
    percentile: str = "p75",
):
    """
    GET /v1/benchmarks/financial/demographic_parity_difference
    Returns industry benchmark value for a sector + metric combination.
    """
    if sector not in SECTORS:
        raise HTTPException(400, f"Unknown sector '{sector}'. Choose from: {SECTORS}")

    baselines = SECTOR_BASELINES.get(sector, {})
    metric_data = baselines.get(metric)
    if metric_data is None:
        raise HTTPException(404, f"No baseline for '{metric}' in sector '{sector}'")

    return {
        "sector": sector,
        "metric": metric,
        "p75_industry": metric_data.get("p75_industry"),
        "p90_industry": metric_data.get("p90_industry"),
        "description": metric_data.get("description", ""),
        "source": metric_data.get("source", ""),
    }


@router.get("/{sector}")
async def list_sector_metrics(sector: str):
    """
    GET /v1/benchmarks/financial
    Lists all available metrics for a sector.
    """
    if sector not in SECTORS:
        raise HTTPException(400, f"Unknown sector '{sector}'. Choose from: {SECTORS}")

    baselines = SECTOR_BASELINES.get(sector, {})
    return {
        "sector": sector,
        "metrics": list(baselines.keys()),
        "count": len(baselines),
    }


@router.get("/")
async def list_sectors():
    """
    GET /v1/benchmarks/
    Lists all available sectors.
    """
    return {
        "sectors": SECTORS,
        "count": len(SECTORS),
    }


@router.post("/{sector}/compare")
async def compare_model_endpoint(sector: str, model_metrics: dict):
    """
    POST /v1/benchmarks/financial/compare
    Body: {"demographic_parity_difference": 0.07, "disparate_impact_ratio": 0.85}
    Returns comparison report with percentile rankings.
    """
    if sector not in SECTORS:
        raise HTTPException(400, f"Unknown sector '{sector}'. Choose from: {SECTORS}")
    return compare_to_benchmark(model_metrics, sector=sector)
