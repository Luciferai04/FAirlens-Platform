import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path("local_data/fairlens.db")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Mirror exact BigQuery schemas
    c.executescript("""
    CREATE TABLE IF NOT EXISTS audit_reports (
        report_id TEXT PRIMARY KEY,
        model_id TEXT NOT NULL,
        name TEXT,
        version TEXT,
        created_at TEXT NOT NULL,
        protected_cols TEXT,      -- JSON array
        metrics TEXT,             -- JSON object
        threshold_policy TEXT,
        passed INTEGER,
        triggered_by TEXT,
        provider TEXT,
        intended_purpose TEXT,
        equity_score REAL,
        violations_count INTEGER,
        trend TEXT                -- JSON array of 30 floats
    );
    
    CREATE TABLE IF NOT EXISTS bias_incidents (
        incident_id TEXT PRIMARY KEY,
        model_id TEXT NOT NULL,
        model_name TEXT,
        model_category TEXT,
        detected_at TEXT NOT NULL,
        metric_name TEXT,
        sub_metric TEXT,
        current_value REAL,
        threshold REAL,
        severity TEXT,
        status TEXT,
        sensitive_col TEXT,
        playbook_id TEXT,
        resolved_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS shap_attributions (
        attribution_id TEXT PRIMARY KEY,
        model_id TEXT NOT NULL,
        sensitive_col TEXT,
        group_value TEXT,
        feature_name TEXT,
        mean_abs_shap REAL,
        disparity REAL,
        computed_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS compliance_reports (
        report_id TEXT PRIMARY KEY,
        model_id TEXT NOT NULL,
        model_name TEXT,
        framework TEXT,
        generated_at TEXT,
        kms_signed INTEGER DEFAULT 0,
        sha256_hash TEXT,
        pdf_path TEXT
    );
    
    CREATE TABLE IF NOT EXISTS playbooks (
        playbook_id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        strategies TEXT,          -- JSON array
        human_approved INTEGER DEFAULT 0,
        created_at TEXT,
        executed_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS bias_index_scores (
        score_id TEXT PRIMARY KEY,
        model_id TEXT NOT NULL,
        computed_at TEXT NOT NULL,
        -- Enterprise Bias Index components
        metric_coverage_score REAL,
        severity_weighted_score REAL,
        temporal_stability_score REAL,
        intersectional_score REAL,
        remediation_velocity_score REAL,
        regulatory_alignment_score REAL,
        -- Composite
        enterprise_bias_index REAL,
        risk_tier TEXT,           -- GREEN / AMBER / RED / CRITICAL
        percentile_rank REAL      -- vs industry benchmarks
    );
    """)
    conn.commit()
    print(f"Database initialized at {DB_PATH}")
    return conn

if __name__ == "__main__":
    init_db()
