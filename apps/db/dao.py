from typing import Dict, List

from psycopg import sql

from .client import get_pool


def upsert_procedure(conn, row: Dict) -> None:
    query = """
    INSERT INTO procedures (procedure_id, title_raw, title_norm, instrument, status, state, county, municipality, municipality_key,
                            geometry, bbox, grid_score, bess_score, confidence, developer_company,
                            capacity_mw, capacity_mwh, area_hectares, decision_date,
                            procedure_type, legal_basis, project_components, ambiguity_flag, review_recommended, site_location_raw, evidence_snippets)
    VALUES (%(procedure_id)s, %(title_raw)s, %(title_norm)s, %(instrument)s, %(status)s, %(state)s,
            %(county)s, %(municipality)s, %(municipality_key)s, %(geometry)s, %(bbox)s,
            %(grid_score)s, %(bess_score)s, %(confidence)s, %(developer_company)s,
            %(capacity_mw)s, %(capacity_mwh)s, %(area_hectares)s, %(decision_date)s,
            %(procedure_type)s, %(legal_basis)s, %(project_components)s, %(ambiguity_flag)s, %(review_recommended)s, %(site_location_raw)s, %(evidence_snippets)s)
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
    conn.execute(query, row)


def insert_source(conn, row: Dict) -> None:
    # retrieved_at: set explicitly with Python datetime
    from datetime import datetime, timezone
    if "retrieved_at" not in row or row.get("retrieved_at") is None:
        row["retrieved_at"] = datetime.now(timezone.utc)
    # Ensure discovery fields exist
    row.setdefault("discovery_source", None)
    row.setdefault("discovery_path", None)
    query = """
    INSERT INTO sources (source_id, procedure_id, source_system, source_url, source_date, retrieved_at, http_status, discovery_source, discovery_path)
    VALUES (%(source_id)s, %(procedure_id)s, %(source_system)s, %(source_url)s, %(source_date)s, %(retrieved_at)s, %(http_status)s, %(discovery_source)s, %(discovery_path)s)
    ON CONFLICT (source_id) DO NOTHING;
    """
    conn.execute(query, row)


def insert_document(conn, row: Dict) -> None:
    query = """
    INSERT INTO documents (document_id, source_id, doc_url, doc_type, sha256, file_path, text_extracted, ocr_used, page_map)
    VALUES (%(document_id)s, %(source_id)s, %(doc_url)s, %(doc_type)s, %(sha256)s, %(file_path)s, %(text_extracted)s, %(ocr_used)s, %(page_map)s)
    ON CONFLICT (document_id) DO NOTHING;
    """
    conn.execute(query, row)


def insert_extractions(conn, rows: List[Dict]) -> None:
    if not rows:
        return
    # Use executemany for batch insert
    query = """
    INSERT INTO extractions (extraction_id, document_id, field, value, method, evidence)
    VALUES (%(extraction_id)s, %(document_id)s, %(field)s, %(value)s, %(method)s, %(evidence)s)
    ON CONFLICT (extraction_id) DO NOTHING;
    """
    for row in rows:
        conn.execute(query, row)


def upsert_project_entity(cur, row: Dict) -> str:
    """
    Upsert a project entity. Returns project_id.
    Note: cur should be a cursor.
    """
    query = """
    INSERT INTO project_entities (
        project_id, state, municipality_key, municipality_name, county,
        canonical_project_name, project_components, legal_basis_best,
        site_location_best, developer_company_best,
        capacity_mw_best, capacity_mwh_best, area_hectares_best,
        maturity_stage, first_seen_date, last_seen_date,
        max_confidence, needs_review
    )
    VALUES (
        COALESCE(%(project_id)s, gen_random_uuid()),
        %(state)s, %(municipality_key)s, %(municipality_name)s, %(county)s,
        %(canonical_project_name)s, %(project_components)s, %(legal_basis_best)s,
        %(site_location_best)s, %(developer_company_best)s,
        %(capacity_mw_best)s, %(capacity_mwh_best)s, %(area_hectares_best)s,
        %(maturity_stage)s, %(first_seen_date)s, %(last_seen_date)s,
        %(max_confidence)s, %(needs_review)s
    )
    ON CONFLICT (project_id) DO UPDATE SET
        canonical_project_name = COALESCE(EXCLUDED.canonical_project_name, project_entities.canonical_project_name),
        project_components = COALESCE(EXCLUDED.project_components, project_entities.project_components),
        legal_basis_best = CASE 
            WHEN EXCLUDED.legal_basis_best IN ('§35', '§34') THEN EXCLUDED.legal_basis_best
            WHEN project_entities.legal_basis_best IN ('§35', '§34') THEN project_entities.legal_basis_best
            ELSE COALESCE(EXCLUDED.legal_basis_best, project_entities.legal_basis_best)
        END,
        site_location_best = COALESCE(EXCLUDED.site_location_best, project_entities.site_location_best),
        developer_company_best = COALESCE(EXCLUDED.developer_company_best, project_entities.developer_company_best),
        capacity_mw_best = GREATEST(COALESCE(EXCLUDED.capacity_mw_best, 0), COALESCE(project_entities.capacity_mw_best, 0)),
        capacity_mwh_best = GREATEST(COALESCE(EXCLUDED.capacity_mwh_best, 0), COALESCE(project_entities.capacity_mwh_best, 0)),
        area_hectares_best = GREATEST(COALESCE(EXCLUDED.area_hectares_best, 0), COALESCE(project_entities.area_hectares_best, 0)),
        maturity_stage = EXCLUDED.maturity_stage,
        first_seen_date = LEAST(COALESCE(EXCLUDED.first_seen_date, '9999-12-31'::date), COALESCE(project_entities.first_seen_date, '9999-12-31'::date)),
        last_seen_date = GREATEST(COALESCE(EXCLUDED.last_seen_date, '1900-01-01'::date), COALESCE(project_entities.last_seen_date, '1900-01-01'::date)),
        max_confidence = GREATEST(COALESCE(EXCLUDED.max_confidence, 0), COALESCE(project_entities.max_confidence, 0)),
        needs_review = EXCLUDED.needs_review OR project_entities.needs_review,
        updated_at = now()
    """
    # After upsert, update needs_review if any linked procedure has review_recommended
    update_review_query = """
    UPDATE project_entities pe
    SET needs_review = TRUE
    WHERE pe.project_id = %(project_id)s
    AND EXISTS (
        SELECT 1 FROM project_procedures pp
        JOIN procedures p ON p.procedure_id = pp.procedure_id
        WHERE pp.project_id = pe.project_id
        AND p.review_recommended = TRUE
    );
    RETURNING project_id;
    """
    # Ensure all fields exist
    row.setdefault("project_id", None)
    row.setdefault("state", None)
    row.setdefault("municipality_key", None)
    row.setdefault("municipality_name", None)
    row.setdefault("county", None)
    row.setdefault("canonical_project_name", None)
    row.setdefault("project_components", None)
    row.setdefault("legal_basis_best", None)
    row.setdefault("site_location_best", None)
    row.setdefault("developer_company_best", None)
    row.setdefault("capacity_mw_best", None)
    row.setdefault("capacity_mwh_best", None)
    row.setdefault("area_hectares_best", None)
    row.setdefault("maturity_stage", "DISCOVERED")
    row.setdefault("first_seen_date", None)
    row.setdefault("last_seen_date", None)
    row.setdefault("max_confidence", 0.0)
    row.setdefault("needs_review", False)
    
    # Execute and get project_id
    cur.execute(query, row)
    result = cur.fetchone()
    if result:
        return str(result[0])
    # Fallback if no RETURNING worked
    import uuid
    return str(uuid.uuid4())


def link_procedure_to_project(cur, project_id: str, procedure_id: str, link_confidence: float, link_reason: str) -> None:
    """
    Link a procedure to a project entity.
    Note: cur should be a cursor.
    """
    query = """
    INSERT INTO project_procedures (project_id, procedure_id, link_confidence, link_reason)
    VALUES (%(project_id)s, %(procedure_id)s, %(link_confidence)s, %(link_reason)s)
    ON CONFLICT (project_id, procedure_id) DO UPDATE SET
        link_confidence = EXCLUDED.link_confidence,
        link_reason = EXCLUDED.link_reason;
    """
    cur.execute(query, {
        "project_id": project_id,
        "procedure_id": procedure_id,
        "link_confidence": link_confidence,
        "link_reason": link_reason,
    })


def with_connection(func):
    def wrapper(*args, **kwargs):
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                return func(cur, *args, **kwargs)

    return wrapper

