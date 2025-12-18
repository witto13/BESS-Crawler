#!/usr/bin/env python3
"""
Recall debug report: identify which gates are killing recall.
Shows skipped items, false negatives, and breakdown by discovery source.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool
import json

def recall_debug_report():
    """
    Generate recall debug report showing:
    - How many items were skipped as containers
    - Top 50 skipped titles with prefilter scores
    - How many skipped items had BESS terms (false negatives)
    - Breakdown by discovery_source
    """
    pool = get_pool()
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Count skipped candidates
            cur.execute("""
                SELECT 
                    discovery_source,
                    status,
                    COUNT(*) as count,
                    AVG(prefilter_score) as avg_score
                FROM crawl_candidates
                WHERE status IN ('SKIPPED', 'ERROR')
                GROUP BY discovery_source, status
                ORDER BY discovery_source, status;
            """)
            skipped_by_source = cur.fetchall()
            
            # Top 50 skipped titles with scores
            cur.execute("""
                SELECT 
                    title,
                    discovery_source,
                    prefilter_score,
                    status,
                    reason
                FROM crawl_candidates
                WHERE status = 'SKIPPED'
                ORDER BY prefilter_score DESC
                LIMIT 50;
            """)
            top_skipped = cur.fetchall()
            
            # Check procedures table for skipped items that might have BESS terms
            # (This would require checking sources table for procedure_id IS NULL)
            cur.execute("""
                SELECT 
                    COUNT(*) as skipped_sources,
                    COUNT(DISTINCT s.discovery_source) as sources_count
                FROM sources s
                WHERE s.procedure_id IS NULL
                AND s.discovery_source IS NOT NULL;
            """)
            skipped_sources = cur.fetchone()
            
            # Count procedures by discovery source
            cur.execute("""
                SELECT 
                    s.discovery_source,
                    COUNT(DISTINCT p.procedure_id) as procedure_count,
                    COUNT(DISTINCT CASE WHEN p.procedure_type = 'UNKNOWN' THEN p.procedure_id END) as unknown_count,
                    COUNT(DISTINCT CASE WHEN p.review_recommended = true THEN p.procedure_id END) as review_count
                FROM procedures p
                JOIN sources s ON s.procedure_id = p.procedure_id
                WHERE p.state = 'BB'
                AND p.procedure_id != 'test-proc-999'
                GROUP BY s.discovery_source
                ORDER BY procedure_count DESC;
            """)
            procedures_by_source = cur.fetchall()
            
            # Count projects with privileged legal basis
            cur.execute("""
                SELECT 
                    COUNT(*) as total_projects,
                    COUNT(CASE WHEN legal_basis_best IN ('§35', '§36') THEN 1 END) as privileged_projects,
                    COUNT(CASE WHEN maturity_stage IN ('PERMIT_36', 'BAUVORBESCHEID', 'BAUGENEHMIGUNG') THEN 1 END) as permit_projects,
                    COUNT(CASE WHEN needs_review = true THEN 1 END) as review_projects
                FROM project_entities
                WHERE state = 'BB';
            """)
            project_stats = cur.fetchone()
    
    # Print report
    print("=" * 100)
    print("🔍 RECALL DEBUG REPORT")
    print("=" * 100)
    print()
    
    print("📊 SKIPPED CANDIDATES BY SOURCE")
    print("-" * 100)
    print(f"{'Source':<20} {'Status':<15} {'Count':<10} {'Avg Score':<12}")
    print("-" * 100)
    for source, status, count, avg_score in skipped_by_source:
        print(f"{source or 'N/A':<20} {status:<15} {count:<10} {avg_score or 0:<12.2f}")
    print()
    
    print("📋 TOP 50 SKIPPED TITLES (by prefilter_score)")
    print("-" * 100)
    print(f"{'Title':<60} {'Source':<15} {'Score':<10} {'Reason':<20}")
    print("-" * 100)
    for title, source, score, status, reason in top_skipped:
        title_short = (title or "")[:58]
        print(f"{title_short:<60} {source or 'N/A':<15} {score or 0:<10.2f} {(reason or '')[:18]:<20}")
    print()
    
    print("📈 PROCEDURES BY SOURCE")
    print("-" * 100)
    print(f"{'Source':<20} {'Total':<10} {'UNKNOWN':<10} {'Review':<10}")
    print("-" * 100)
    for source, total, unknown, review in procedures_by_source:
        print(f"{source or 'N/A':<20} {total:<10} {unknown or 0:<10} {review or 0:<10}")
    print()
    
    print("🏗️  PROJECT STATISTICS")
    print("-" * 100)
    if project_stats:
        total, privileged, permit, review = project_stats
        privileged_pct = (privileged / total * 100) if total > 0 else 0
        permit_pct = (permit / total * 100) if total > 0 else 0
        print(f"Total Projects:              {total}")
        print(f"Privileged Projects (§35/§36): {privileged} ({privileged_pct:.1f}%)")
        print(f"Permit Projects:             {permit} ({permit_pct:.1f}%)")
        print(f"Projects Needing Review:     {review}")
    print()
    
    print("⚠️  SKIPPED SOURCES (procedure_id IS NULL)")
    print("-" * 100)
    if skipped_sources:
        skipped_count, sources_count = skipped_sources
        print(f"Total Skipped Sources:        {skipped_count}")
        print(f"Unique Discovery Sources:     {sources_count}")
    print()
    
    print("=" * 100)
    print()
    print("💡 RECOMMENDATIONS:")
    print("- Check top skipped titles for false negatives")
    print("- Review UNKNOWN procedure_type items (may be privileged projects)")
    print("- Consider lowering thresholds for sources with high skip rates")
    print("=" * 100)


if __name__ == "__main__":
    recall_debug_report()






