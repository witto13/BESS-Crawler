"""
DAO for crawl_candidates table.
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid

from .client import get_pool


def insert_candidate(cur, row: Dict) -> str:
    """
    Insert a crawl candidate.
    
    Returns:
        candidate_id
    """
    query = """
    INSERT INTO crawl_candidates (
        candidate_id, run_id, municipality_key, discovery_source, discovery_path,
        title, date_hint, url, doc_urls, prefilter_score, status, reason
    )
    VALUES (
        COALESCE(%(candidate_id)s, gen_random_uuid()),
        %(run_id)s, %(municipality_key)s, %(discovery_source)s, %(discovery_path)s,
        %(title)s, %(date_hint)s, %(url)s, %(doc_urls)s, %(prefilter_score)s,
        %(status)s, %(reason)s
    )
    RETURNING candidate_id;
    """
    
    row.setdefault("candidate_id", None)
    row.setdefault("run_id", str(uuid.uuid4()))
    row.setdefault("municipality_key", None)
    row.setdefault("discovery_source", None)
    row.setdefault("discovery_path", None)
    row.setdefault("title", None)
    row.setdefault("date_hint", None)
    row.setdefault("url", "")
    row.setdefault("doc_urls", None)
    row.setdefault("prefilter_score", 0.0)
    row.setdefault("status", "NEW")
    row.setdefault("reason", None)
    
    cur.execute(query, row)
    result = cur.fetchone()
    return str(result[0])


def update_candidate_status(cur, candidate_id: str, status: str, reason: Optional[str] = None) -> None:
    """Update candidate status."""
    query = """
    UPDATE crawl_candidates
    SET status = %(status)s,
        reason = COALESCE(%(reason)s, reason),
        updated_at = now()
    WHERE candidate_id = %(candidate_id)s;
    """
    cur.execute(query, {
        "candidate_id": candidate_id,
        "status": status,
        "reason": reason,
    })


def get_candidates_for_extraction(cur, run_id: str, mode: str = "fast", limit: int = 100) -> List[Dict]:
    """
    Get candidates ready for extraction.
    
    Args:
        cur: Database cursor
        run_id: Run ID
        mode: "fast" (threshold 0.6) or "deep" (threshold 0.3)
        limit: Maximum candidates to return
    
    Returns:
        List of candidate dicts
    """
    threshold = 0.6 if mode == "fast" else 0.3
    
    query = """
    SELECT candidate_id, run_id, municipality_key, discovery_source, discovery_path,
           title, date_hint, url, doc_urls, prefilter_score
    FROM crawl_candidates
    WHERE run_id = %(run_id)s
    AND status = 'NEW'
    AND prefilter_score >= %(threshold)s
    ORDER BY prefilter_score DESC
    LIMIT %(limit)s;
    """
    
    cur.execute(query, {
        "run_id": run_id,
        "threshold": threshold,
        "limit": limit,
    })
    
    rows = cur.fetchall()
    return [
        {
            "candidate_id": row[0],
            "run_id": row[1],
            "municipality_key": row[2],
            "discovery_source": row[3],
            "discovery_path": row[4],
            "title": row[5],
            "date_hint": row[6],
            "url": row[7],
            "doc_urls": row[8],
            "prefilter_score": float(row[9]) if row[9] else 0.0,
        }
        for row in rows
    ]






