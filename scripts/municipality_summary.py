#!/usr/bin/env python3
"""
Per-municipality summary: aggregates discovery results across RIS, Amtsblatt, and Municipal Website.
Shows one-line summary per municipality with status for each source and procedures saved.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool
import json

def municipality_summary():
    """
    Generate per-municipality summary showing:
    - Municipality name
    - RIS status (SUCCESS, ERROR_SSL, ERROR_OTHER, etc.)
    - Amtsblatt status
    - Municipal Website status
    - Total procedures saved across all sources
    """
    pool = get_pool()
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Get per-municipality stats aggregated across all sources
            cur.execute("""
                SELECT 
                    cs.municipality_key,
                    m.name as municipality_name,
                    m.county,
                    COUNT(DISTINCT cs.job_id) as jobs_processed,
                    SUM((cs.counts_json->>'candidates_found')::int) as total_candidates,
                    SUM((cs.counts_json->>'procedures_saved')::int) as total_procedures_saved,
                    -- RIS status
                    MAX(CASE WHEN cs.source_type = 'RIS' THEN cs.counts_json->>'source_status' END) as ris_status,
                    MAX(CASE WHEN cs.source_type = 'RIS' THEN cs.counts_json->>'error_message' END) as ris_error,
                    -- Amtsblatt status
                    MAX(CASE WHEN cs.source_type = 'GAZETTE' THEN cs.counts_json->>'source_status' END) as amtsblatt_status,
                    MAX(CASE WHEN cs.source_type = 'GAZETTE' THEN cs.counts_json->>'error_message' END) as amtsblatt_error,
                    -- Municipal Website status
                    MAX(CASE WHEN cs.source_type = 'MUNICIPAL_WEBSITE' THEN cs.counts_json->>'source_status' END) as municipal_status,
                    MAX(CASE WHEN cs.source_type = 'MUNICIPAL_WEBSITE' THEN cs.counts_json->>'error_message' END) as municipal_error
                FROM crawl_stats cs
                LEFT JOIN municipality_seed m ON m.municipality_key = cs.municipality_key
                WHERE cs.created_at > NOW() - INTERVAL '24 hours'
                GROUP BY cs.municipality_key, m.name, m.county
                ORDER BY total_procedures_saved DESC, cs.municipality_key
            """)
            
            results = cur.fetchall()
    
    # Print summary
    print("=" * 120)
    print("📊 PER-MUNICIPALITY SUMMARY")
    print("=" * 120)
    print()
    print(f"{'Municipality':<30} {'County':<25} {'RIS':<12} {'Amtsblatt':<12} {'Municipal':<12} {'Procedures':<10}")
    print("-" * 120)
    
    for row in results:
        muni_key, muni_name, county, jobs, candidates, procedures, ris_status, ris_error, amts_status, amts_error, mun_status, mun_error = row
        
        # Format status (truncate if too long)
        ris_status_str = (ris_status or "NOT_RUN")[:11]
        amts_status_str = (amts_status or "NOT_RUN")[:11]
        mun_status_str = (mun_status or "NOT_RUN")[:11]
        
        muni_display = (muni_name or muni_key)[:29]
        county_display = (county or "")[:24]
        
        print(f"{muni_display:<30} {county_display:<25} {ris_status_str:<12} {amts_status_str:<12} {mun_status_str:<12} {procedures or 0:<10}")
    
    print()
    print("=" * 120)
    print()
    
    # Summary statistics
    total_municipalities = len(results)
    municipalities_with_procedures = sum(1 for r in results if (r[5] or 0) > 0)
    municipalities_with_errors = sum(1 for r in results if any(s in ["ERROR_SSL", "ERROR_OTHER", "ERROR_NETWORK"] for s in [r[6], r[8], r[10]] if s))
    
    ris_errors = sum(1 for r in results if r[6] and "ERROR" in r[6])
    amts_errors = sum(1 for r in results if r[8] and "ERROR" in r[8])
    mun_errors = sum(1 for r in results if r[10] and "ERROR" in r[10])
    
    print("📈 Summary Statistics:")
    print(f"  Total Municipalities Processed:  {total_municipalities}")
    print(f"  Municipalities with Procedures:   {municipalities_with_procedures} ({municipalities_with_procedures/total_municipalities*100:.1f}%)")
    print(f"  Municipalities with Errors:       {municipalities_with_errors}")
    print()
    print("  Errors by Source:")
    print(f"    RIS Errors:                    {ris_errors}")
    print(f"    Amtsblatt Errors:              {amts_errors}")
    print(f"    Municipal Website Errors:      {mun_errors}")
    print()
    print("=" * 120)


if __name__ == "__main__":
    municipality_summary()

