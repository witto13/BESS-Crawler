#!/usr/bin/env python3
"""
Re-score procedures using document text from already downloaded documents.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool
from apps.extract import rules_bess, rules_grid

def rescore_with_documents():
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Get procedures with their documents
            cur.execute("""
                SELECT DISTINCT
                    p.procedure_id,
                    p.title_raw,
                    p.title_norm,
                    STRING_AGG(DISTINCT COALESCE(d.text_extracted, ''), ' ') as doc_texts
                FROM procedures p
                LEFT JOIN sources s ON p.procedure_id = s.procedure_id
                LEFT JOIN documents d ON s.source_id = d.source_id
                WHERE p.procedure_id != 'test-proc-999'
                GROUP BY p.procedure_id, p.title_raw, p.title_norm
            """)
            
            procedures = cur.fetchall()
            print(f"Re-scoring {len(procedures)} procedures with document text...")
            
            updated = 0
            for proc_id, title_raw, title_norm, doc_texts in procedures:
                # Combine title and document text
                all_text = (title_raw or "") + " " + (title_norm or "") + " " + (doc_texts or "")
                all_text = all_text.strip()
                
                if not all_text:
                    continue
                
                # Score on combined text
                bess_score = rules_bess.score(all_text)
                grid_score = rules_grid.score(all_text)
                
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
            print(f"Done! Updated {updated} procedures with document text analysis.")

if __name__ == "__main__":
    rescore_with_documents()







