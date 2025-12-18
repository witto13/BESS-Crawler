#!/usr/bin/env python3
"""
Project-based coverage metrics (replaces procedure-based metrics).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool
import pandas as pd

def generate_project_coverage_report():
    """
    Generate coverage report focused on projects, not procedures.
    """
    pool = get_pool()
    
    with pool.connection() as conn:
        # Overall statistics
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT ms.municipality_key) as total_municipalities,
                    COUNT(DISTINCT CASE WHEN pe.project_id IS NOT NULL THEN ms.municipality_key END) as municipalities_with_projects,
                    COUNT(DISTINCT pe.project_id) as total_projects,
                    COUNT(DISTINCT CASE WHEN pe.legal_basis_best IN ('§35', '§36') OR pe.maturity_stage IN ('PERMIT_36', 'BAUVORBESCHEID', 'BAUGENEHMIGUNG') THEN pe.project_id END) as privileged_projects,
                    COUNT(DISTINCT CASE WHEN pe.maturity_stage LIKE 'BPLAN%' THEN pe.project_id END) as bplan_projects
                FROM municipality_seed ms
                LEFT JOIN project_entities pe ON pe.municipality_key = ms.municipality_key
                WHERE ms.state = 'BB'
            """)
            overall = cur.fetchone()
        
        # Per county statistics
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    ms.county,
                    COUNT(DISTINCT ms.municipality_key) as total_municipalities,
                    COUNT(DISTINCT CASE WHEN pe.project_id IS NOT NULL THEN ms.municipality_key END) as municipalities_with_projects,
                    COUNT(DISTINCT pe.project_id) as total_projects,
                    COUNT(DISTINCT CASE WHEN pe.legal_basis_best IN ('§35', '§36') OR pe.maturity_stage IN ('PERMIT_36', 'BAUVORBESCHEID', 'BAUGENEHMIGUNG') THEN pe.project_id END) as privileged_projects
                FROM municipality_seed ms
                LEFT JOIN project_entities pe ON pe.municipality_key = ms.municipality_key
                WHERE ms.state = 'BB'
                GROUP BY ms.county
                ORDER BY total_projects DESC, ms.county
            """)
            county_stats = cur.fetchall()
        
        # Top municipalities by project count
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    pe.municipality_name,
                    pe.county,
                    COUNT(DISTINCT pe.project_id) as project_count,
                    COUNT(DISTINCT CASE WHEN pe.legal_basis_best IN ('§35', '§36') OR pe.maturity_stage IN ('PERMIT_36', 'BAUVORBESCHEID', 'BAUGENEHMIGUNG') THEN pe.project_id END) as privileged_count
                FROM project_entities pe
                WHERE pe.state = 'BB'
                GROUP BY pe.municipality_name, pe.county
                ORDER BY project_count DESC
                LIMIT 50
            """)
            municipality_stats = cur.fetchall()
        
        # Projects by maturity stage
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    maturity_stage,
                    COUNT(*) as project_count
                FROM project_entities
                WHERE state = 'BB'
                GROUP BY maturity_stage
                ORDER BY project_count DESC
            """)
            maturity_stats = cur.fetchall()
    
    # Print report
    print("=" * 80)
    print("📊 BRANDENBURG PROJECT COVERAGE REPORT")
    print("=" * 80)
    print()
    
    print("📈 OVERALL STATISTICS")
    print("-" * 80)
    total_munis, munis_with_projects, total_projects, privileged_projects, bplan_projects = overall
    coverage_pct = (munis_with_projects / total_munis * 100) if total_munis > 0 else 0
    print(f"Total Municipalities:              {total_munis}")
    print(f"Municipalities with Projects:      {munis_with_projects} ({coverage_pct:.1f}%)")
    print(f"Total Projects Found:              {total_projects}")
    print(f"Privileged Projects (§35/§36):    {privileged_projects}")
    print(f"B-Plan Projects:                  {bplan_projects}")
    print()
    
    print("🏛️  PER COUNTY STATISTICS")
    print("-" * 80)
    print(f"{'County':<30} {'Munis':<8} {'With Proj':<12} {'Projects':<12} {'Privileged':<12}")
    print("-" * 80)
    for county, total_m, m_with_p, total_p, priv_p in county_stats:
        print(f"{county:<30} {total_m:<8} {m_with_p:<12} {total_p:<12} {priv_p:<12}")
    print()
    
    print("🏘️  TOP 50 MUNICIPALITIES BY PROJECT COUNT")
    print("-" * 80)
    print(f"{'Municipality':<30} {'County':<25} {'Projects':<12} {'Privileged':<12}")
    print("-" * 80)
    for name, county, proj_count, priv_count in municipality_stats:
        print(f"{name:<30} {county:<25} {proj_count:<12} {priv_count:<12}")
    print()
    
    print("📊 PROJECTS BY MATURITY STAGE")
    print("-" * 80)
    print(f"{'Maturity Stage':<30} {'Projects':<12}")
    print("-" * 80)
    for stage, count in maturity_stats:
        print(f"{stage:<30} {count:<12}")
    print()
    
    print("=" * 80)
    
    # Export to CSV
    try:
        df_county = pd.DataFrame(county_stats, columns=['County', 'Total_Municipalities', 'Municipalities_With_Projects', 'Total_Projects', 'Privileged_Projects'])
        df_county.to_csv('exports/project_coverage_by_county.csv', index=False)
        print("✅ Exported: exports/project_coverage_by_county.csv")
        
        df_muni = pd.DataFrame(municipality_stats, columns=['Municipality', 'County', 'Project_Count', 'Privileged_Count'])
        df_muni.to_csv('exports/project_coverage_by_municipality.csv', index=False)
        print("✅ Exported: exports/project_coverage_by_municipality.csv")
        
        df_maturity = pd.DataFrame(maturity_stats, columns=['Maturity_Stage', 'Project_Count'])
        df_maturity.to_csv('exports/project_coverage_by_maturity.csv', index=False)
        print("✅ Exported: exports/project_coverage_by_maturity.csv")
    except Exception as e:
        print(f"⚠️  Could not export CSVs: {e}")


if __name__ == "__main__":
    generate_project_coverage_report()






