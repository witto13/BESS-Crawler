"""
Batch operations for improved DB performance.
"""
from typing import List, Dict
from psycopg import sql

from .client import get_pool


def upsert_procedures_batch(cur, rows: List[Dict]) -> None:
    """
    Batch upsert procedures.
    
    Args:
        cur: Database cursor
        rows: List of procedure dicts
    """
    if not rows:
        return
    
    query = """
    INSERT INTO procedures (
        procedure_id, title_raw, title_norm, instrument, status, state, county, municipality, municipality_key,
        geometry, bbox, grid_score, bess_score, confidence, developer_company,
        capacity_mw, capacity_mwh, area_hectares, decision_date,
        procedure_type, legal_basis, project_components, ambiguity_flag, review_recommended, site_location_raw, evidence_snippets
    )
    VALUES %s
    ON CONFLICT (procedure_id) DO UPDATE SET
        title_raw=EXCLUDED.title_raw,
        title_norm=EXCLUDED.title_norm,
        status=EXCLUDED.status,
        grid_score=EXCLUDED.grid_score,
        bess_score=EXCLUDED.bess_score,
        confidence=EXCLUDED.confidence,
        developer_company=EXCLUDED.developer_company,
        capacity_mw=EXCLUDED.capacity_mw,
        capacity_mwh=EXCLUDED.capacity_mwh,
        area_hectares=EXCLUDED.area_hectares,
        decision_date=EXCLUDED.decision_date,
        procedure_type=EXCLUDED.procedure_type,
        legal_basis=EXCLUDED.legal_basis,
        project_components=EXCLUDED.project_components,
        ambiguity_flag=EXCLUDED.ambiguity_flag,
        review_recommended=EXCLUDED.review_recommended,
        site_location_raw=EXCLUDED.site_location_raw,
        evidence_snippets=EXCLUDED.evidence_snippets,
        updated_at=now();
    """
    
    # Prepare data tuples
    values = []
    for row in rows:
        # Ensure all fields exist
        row.setdefault("capacity_mw", None)
        row.setdefault("capacity_mwh", None)
        row.setdefault("area_hectares", None)
        row.setdefault("decision_date", None)
        row.setdefault("procedure_type", None)
        row.setdefault("legal_basis", None)
        row.setdefault("project_components", None)
        row.setdefault("ambiguity_flag", False)
        row.setdefault("review_recommended", False)
        row.setdefault("site_location_raw", None)
        row.setdefault("evidence_snippets", None)
        
        values.append((
            row["procedure_id"],
            row.get("title_raw"),
            row.get("title_norm"),
            row.get("instrument"),
            row.get("status"),
            row.get("state"),
            row.get("county"),
            row.get("municipality"),
            row.get("municipality_key"),
            row.get("geometry"),
            row.get("bbox"),
            row.get("grid_score"),
            row.get("bess_score"),
            row.get("confidence"),
            row.get("developer_company"),
            row.get("capacity_mw"),
            row.get("capacity_mwh"),
            row.get("area_hectares"),
            row.get("decision_date"),
            row.get("procedure_type"),
            row.get("legal_basis"),
            row.get("project_components"),
            row.get("ambiguity_flag"),
            row.get("review_recommended"),
            row.get("site_location_raw"),
            row.get("evidence_snippets"),
        ))
    
    # Use execute_values for batch insert
    from psycopg.extras import execute_values
    execute_values(cur, query, values)


def insert_sources_batch(cur, rows: List[Dict]) -> None:
    """Batch insert sources."""
    if not rows:
        return
    
    from datetime import datetime, timezone
    
    query = """
    INSERT INTO sources (source_id, procedure_id, source_system, source_url, source_date, retrieved_at, http_status, discovery_source, discovery_path)
    VALUES %s
    ON CONFLICT (source_id) DO NOTHING;
    """
    
    values = []
    for row in rows:
        if "retrieved_at" not in row or row.get("retrieved_at") is None:
            row["retrieved_at"] = datetime.now(timezone.utc)
        
        values.append((
            row["source_id"],
            row.get("procedure_id"),
            row.get("source_system"),
            row.get("source_url"),
            row.get("source_date"),
            row["retrieved_at"],
            row.get("http_status", 200),
            row.get("discovery_source"),
            row.get("discovery_path"),
        ))
    
    from psycopg.extras import execute_values
    execute_values(cur, query, values)






