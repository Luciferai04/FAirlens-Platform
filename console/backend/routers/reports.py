"""Compliance reporting endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
import os

from auth import require_role
from db import db

router = APIRouter()

@router.get("/compliance")
async def list_compliance_reports(
    limit: int = Query(50, le=200),
    _=Depends(require_role(["viewer", "auditor", "admin", "owner"])),
):
    """List all generated compliance reports."""
    reports = db.get_compliance_reports()
    return reports[:limit]

@router.get("/benchmarks")
async def get_industry_benchmarks(
    _=Depends(require_role(["viewer", "auditor", "admin", "owner"])),
):
    """Retrieve sector baselines for comparison."""
    return db.get_benchmarks()
