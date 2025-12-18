"""
DAO for crawl_stats table.
"""
from typing import Dict
import uuid
import json

from .client import get_pool


def insert_crawl_stats(cur, row: Dict) -> None:
    """
    Insert crawl statistics.
    
    Args:
        cur: Database cursor
        row: Dict with run_id, job_id, municipality_key, source_type, domain,
             counts_json, timings_json
    """
    query = """
    INSERT INTO crawl_stats (
        run_id, job_id, municipality_key, source_type, domain,
        counts_json, timings_json
    )
    VALUES (
        %(run_id)s, %(job_id)s, %(municipality_key)s, %(source_type)s, %(domain)s,
        %(counts_json)s, %(timings_json)s
    )
    ON CONFLICT (run_id, job_id) DO UPDATE SET
        counts_json = EXCLUDED.counts_json,
        timings_json = EXCLUDED.timings_json;
    """
    
    # Ensure JSON fields are JSON strings
    if isinstance(row.get("counts_json"), dict):
        row["counts_json"] = json.dumps(row["counts_json"])
    if isinstance(row.get("timings_json"), dict):
        row["timings_json"] = json.dumps(row["timings_json"])
    
    cur.execute(query, row)






