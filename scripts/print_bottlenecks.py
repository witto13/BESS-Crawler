#!/usr/bin/env python3
"""
Print top slow domains and slow steps from crawl_stats.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool
import json

def print_bottlenecks(run_id: str = None):
    """
    Print bottleneck analysis from crawl_stats.
    """
    pool = get_pool()
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Build query
            if run_id:
                query = """
                    SELECT domain, source_type,
                           COUNT(*) as job_count,
                           AVG((timings_json->>'total_ms')::numeric) as avg_total_ms,
                           AVG((timings_json->>'fetch_pdf_ms')::numeric) as avg_pdf_ms,
                           AVG((timings_json->>'extract_pdf_ms')::numeric) as avg_extract_ms,
                           AVG((timings_json->>'classify_ms')::numeric) as avg_classify_ms,
                           AVG((timings_json->>'db_write_ms')::numeric) as avg_db_ms,
                           SUM((counts_json->>'pdfs_downloaded')::int) as total_pdfs
                    FROM crawl_stats
                    WHERE run_id = %s
                    GROUP BY domain, source_type
                    ORDER BY avg_total_ms DESC
                    LIMIT 20;
                """
                cur.execute(query, (run_id,))
            else:
                query = """
                    SELECT domain, source_type,
                           COUNT(*) as job_count,
                           AVG((timings_json->>'total_ms')::numeric) as avg_total_ms,
                           AVG((timings_json->>'fetch_pdf_ms')::numeric) as avg_pdf_ms,
                           AVG((timings_json->>'extract_pdf_ms')::numeric) as avg_extract_ms,
                           AVG((timings_json->>'classify_ms')::numeric) as avg_classify_ms,
                           AVG((timings_json->>'db_write_ms')::numeric) as avg_db_ms,
                           SUM((counts_json->>'pdfs_downloaded')::int) as total_pdfs
                    FROM crawl_stats
                    GROUP BY domain, source_type
                    ORDER BY avg_total_ms DESC
                    LIMIT 20;
                """
                cur.execute(query)
            
            rows = cur.fetchall()
    
    print("=" * 100)
    print("🔍 BOTTLENECK ANALYSIS")
    print("=" * 100)
    print()
    print(f"{'Domain':<30} {'Source':<20} {'Jobs':<8} {'Avg Total (ms)':<15} {'Avg PDF (ms)':<15} {'Avg Extract (ms)':<15} {'Avg Classify (ms)':<15} {'Avg DB (ms)':<15} {'Total PDFs':<12}")
    print("-" * 100)
    
    for row in rows:
        domain, source_type, job_count, avg_total, avg_pdf, avg_extract, avg_classify, avg_db, total_pdfs = row
        print(f"{domain or 'N/A':<30} {source_type or 'N/A':<20} {job_count:<8} {avg_total or 0:<15.1f} {avg_pdf or 0:<15.1f} {avg_extract or 0:<15.1f} {avg_classify or 0:<15.1f} {avg_db or 0:<15.1f} {total_pdfs or 0:<12}")
    
    print()
    print("=" * 100)


if __name__ == "__main__":
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    print_bottlenecks(run_id)






