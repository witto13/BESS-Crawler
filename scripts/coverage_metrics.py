#!/usr/bin/env python3
"""
Coverage metrics for Brandenburg municipalities.
Tracks which municipalities have been crawled and how many procedures found.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool
import pandas as pd

def generate_coverage_report():
    """
    Generate coverage report showing:
    - Total municipalities
    - Municipalities with procedures found
    - Procedures per municipality
    - Procedures per county
    - Coverage percentage
    """
    pool = get_pool()
    
    with pool.connection() as conn:
        # Overall statistics
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT ms.municipality_key) as total_municipalities,
                    COUNT(DISTINCT CASE WHEN p.procedure_id IS NOT NULL THEN ms.municipality_key END) as municipalities_with_procedures,
                    COUNT(DISTINCT p.procedure_id) as total_procedures,
                    COUNT(DISTINCT CASE WHEN p.bess_score >= 3 AND p.grid_score >= 3 THEN p.procedure_id END) as high_confidence_procedures
                FROM municipality_seed ms
                LEFT JOIN procedures p ON p.municipality_key = ms.municipality_key AND p.procedure_id != 'test-proc-999'
                WHERE ms.state = 'BB'
            """)
            overall = cur.fetchone()
        
        # Per county statistics
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    ms.county,
                    COUNT(DISTINCT ms.municipality_key) as total_municipalities,
                    COUNT(DISTINCT CASE WHEN p.procedure_id IS NOT NULL THEN ms.municipality_key END) as municipalities_with_procedures,
                    COUNT(DISTINCT p.procedure_id) as total_procedures,
                    COUNT(DISTINCT CASE WHEN p.bess_score >= 3 AND p.grid_score >= 3 THEN p.procedure_id END) as high_confidence_procedures
                FROM municipality_seed ms
                LEFT JOIN procedures p ON p.municipality_key = ms.municipality_key AND p.procedure_id != 'test-proc-999'
                WHERE ms.state = 'BB'
                GROUP BY ms.county
                ORDER BY total_procedures DESC, ms.county
            """)
            county_stats = cur.fetchall()
        
        # Per municipality statistics (top 50)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    ms.name,
                    ms.county,
                    COUNT(DISTINCT p.procedure_id) as total_procedures,
                    COUNT(DISTINCT CASE WHEN p.bess_score >= 3 AND p.grid_score >= 3 THEN p.procedure_id END) as high_confidence_procedures,
                    COUNT(DISTINCT s.source_id) as source_count,
                    COUNT(DISTINCT d.document_id) as document_count
                FROM municipality_seed ms
                LEFT JOIN procedures p ON p.municipality_key = ms.municipality_key AND p.procedure_id != 'test-proc-999'
                LEFT JOIN sources s ON s.procedure_id = p.procedure_id
                LEFT JOIN documents d ON d.source_id = s.source_id
                WHERE ms.state = 'BB'
                GROUP BY ms.municipality_key, ms.name, ms.county
                HAVING COUNT(DISTINCT p.procedure_id) > 0
                ORDER BY total_procedures DESC
                LIMIT 50
            """)
            municipality_stats = cur.fetchall()
        
        # Discovery source breakdown
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COALESCE(s.discovery_source, 'UNKNOWN') as discovery_source,
                    COUNT(DISTINCT p.procedure_id) as procedure_count
                FROM procedures p
                LEFT JOIN sources s ON s.procedure_id = p.procedure_id
                WHERE p.procedure_id != 'test-proc-999' AND p.state = 'BB'
                GROUP BY s.discovery_source
                ORDER BY procedure_count DESC
            """)
            source_breakdown = cur.fetchall()
    
    # Print report
    print("=" * 80)
    print("📊 BRANDENBURG COVERAGE REPORT")
    print("=" * 80)
    print()
    
    print("📈 OVERALL STATISTICS")
    print("-" * 80)
    total_munis, munis_with_procs, total_procs, high_conf_procs = overall
    coverage_pct = (munis_with_procs / total_munis * 100) if total_munis > 0 else 0
    print(f"Total Municipalities:        {total_munis}")
    print(f"Municipalities with Procedures: {munis_with_procs} ({coverage_pct:.1f}%)")
    print(f"Total Procedures Found:      {total_procs}")
    print(f"High Confidence Procedures:  {high_conf_procs}")
    print()
    
    print("🏛️  PER COUNTY STATISTICS")
    print("-" * 80)
    print(f"{'County':<30} {'Munis':<8} {'With Procs':<12} {'Procedures':<12} {'High Conf':<12}")
    print("-" * 80)
    for county, total_m, m_with_p, total_p, high_p in county_stats:
        print(f"{county:<30} {total_m:<8} {m_with_p:<12} {total_p:<12} {high_p:<12}")
    print()
    
    print("🏘️  TOP 50 MUNICIPALITIES BY PROCEDURES")
    print("-" * 80)
    print(f"{'Municipality':<30} {'County':<25} {'Procedures':<12} {'High Conf':<12} {'Sources':<10} {'Docs':<10}")
    print("-" * 80)
    for name, county, total_p, high_p, sources, docs in municipality_stats:
        print(f"{name:<30} {county:<25} {total_p:<12} {high_p:<12} {sources:<10} {docs:<10}")
    print()
    
    print("🔍 DISCOVERY SOURCE BREAKDOWN")
    print("-" * 80)
    print(f"{'Source':<30} {'Procedures':<12}")
    print("-" * 80)
    for source, count in source_breakdown:
        print(f"{source:<30} {count:<12}")
    print()
    
    print("=" * 80)
    
    # Export to CSV
    try:
        # County stats CSV
        df_county = pd.DataFrame(county_stats, columns=['County', 'Total_Municipalities', 'Municipalities_With_Procedures', 'Total_Procedures', 'High_Confidence_Procedures'])
        df_county.to_csv('exports/coverage_by_county.csv', index=False)
        print("✅ Exported: exports/coverage_by_county.csv")
        
        # Municipality stats CSV
        df_muni = pd.DataFrame(municipality_stats, columns=['Municipality', 'County', 'Total_Procedures', 'High_Confidence_Procedures', 'Source_Count', 'Document_Count'])
        df_muni.to_csv('exports/coverage_by_municipality.csv', index=False)
        print("✅ Exported: exports/coverage_by_municipality.csv")
        
        # Source breakdown CSV
        df_source = pd.DataFrame(source_breakdown, columns=['Discovery_Source', 'Procedure_Count'])
        df_source.to_csv('exports/coverage_by_source.csv', index=False)
        print("✅ Exported: exports/coverage_by_source.csv")
    except Exception as e:
        print(f"⚠️  Could not export CSVs: {e}")


if __name__ == "__main__":
    generate_coverage_report()






