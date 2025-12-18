"""
Municipality aggregator: logs per-municipality summaries after all sources are processed.
"""
import logging
from typing import Dict, Optional

from apps.db.client import get_pool

logger = logging.getLogger(__name__)


def log_municipality_summary(municipality_key: str, municipality_name: str, run_id: str):
    """
    Log a one-line summary per municipality after all sources are processed.
    Format: municipality_key | ris_status | amtsblatt_status | municipal_status | procedures_saved
    
    This is called after each discovery job completes, and will show the current state
    of all sources for that municipality.
    """
    try:
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Get status for all sources for this municipality
                cur.execute("""
                    SELECT 
                        source_type,
                        counts_json->>'source_status' as status,
                        (counts_json->>'procedures_saved')::int as procedures_saved
                    FROM crawl_stats
                    WHERE municipality_key = %s
                    AND run_id = %s
                    AND source_type IN ('RIS', 'GAZETTE', 'MUNICIPAL_WEBSITE')
                    ORDER BY source_type
                """, (municipality_key, run_id))
                
                results = cur.fetchall()
                
                # Build status dict
                statuses = {}
                total_procedures = 0
                for source_type, status, procedures in results:
                    statuses[source_type] = status or "NOT_RUN"
                    total_procedures += (procedures or 0)
                
                ris_status = statuses.get("RIS", "NOT_RUN")
                amtsblatt_status = statuses.get("GAZETTE", "NOT_RUN")
                municipal_status = statuses.get("MUNICIPAL_WEBSITE", "NOT_RUN")
                
                # Log one-line summary
                logger.info(
                    "MUNICIPALITY_SUMMARY: %s (%s) | RIS=%s | Amtsblatt=%s | Municipal=%s | Procedures=%d",
                    municipality_name or municipality_key,
                    municipality_key,
                    ris_status,
                    amtsblatt_status,
                    municipal_status,
                    total_procedures
                )
    except Exception as e:
        logger.debug("Failed to log municipality summary for %s: %s", municipality_key, e)

