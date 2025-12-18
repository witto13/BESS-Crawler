#!/usr/bin/env python3
"""
Script to re-score existing procedures with updated rules.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool
from apps.extract import rules_bess, rules_grid

def rescore_all():
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Get all procedures
            cur.execute("""
                SELECT procedure_id, title_raw, title_norm 
                FROM procedures 
                WHERE procedure_id != 'test-proc-999'
            """)
            
            procedures = cur.fetchall()
            print(f"Re-scoring {len(procedures)} procedures...")
            
            updated = 0
            for proc_id, title_raw, title_norm in procedures:
                # Score on title
                bess_score = rules_bess.score(title_raw or "")
                grid_score = rules_grid.score(title_raw or "")
                
                # Also check normalized title
                if title_norm:
                    bess_score = max(bess_score, rules_bess.score(title_norm))
                    grid_score = max(grid_score, rules_grid.score(title_norm))
                
                # Set confidence
                if bess_score >= 3 and grid_score >= 3:
                    confidence = "high"
                elif bess_score >= 1 or grid_score >= 1:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                # Update
                cur.execute("""
                    UPDATE procedures 
                    SET bess_score = %s, grid_score = %s, confidence = %s
                    WHERE procedure_id = %s
                """, (bess_score, grid_score, confidence, proc_id))
                
                updated += 1
                if updated % 50 == 0:
                    print(f"  Updated {updated}/{len(procedures)}...")
            
            conn.commit()
            print(f"Done! Updated {updated} procedures.")

if __name__ == "__main__":
    rescore_all()







