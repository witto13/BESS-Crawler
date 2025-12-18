#!/usr/bin/env python3
"""
Clear old data from database to see fresh progress with new recall improvements.
Deletes all procedures, sources, documents, projects, candidates, and stats.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool

def clear_old_data():
    """
    Clear all old data from the database.
    Order matters due to foreign key constraints.
    """
    pool = get_pool()
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            print("🗑️  Clearing old data from database...")
            
            # Get counts before deletion
            cur.execute("SELECT COUNT(*) FROM procedures WHERE procedure_id != 'test-proc-999'")
            proc_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM crawl_candidates")
            candidate_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM project_entities")
            project_count = cur.fetchone()[0]
            
            print(f"  Found {proc_count} procedures, {candidate_count} candidates, {project_count} projects")
            
            # Delete in order (respecting foreign keys)
            # 1. Delete extractions (references documents)
            cur.execute("DELETE FROM extractions")
            print(f"  ✅ Deleted extractions")
            
            # 2. Delete documents (references sources)
            cur.execute("DELETE FROM documents")
            print(f"  ✅ Deleted documents")
            
            # 3. Delete sources (references procedures)
            cur.execute("DELETE FROM sources")
            print(f"  ✅ Deleted sources")
            
            # 4. Delete project_procedures (references both projects and procedures)
            cur.execute("DELETE FROM project_procedures")
            print(f"  ✅ Deleted project_procedures links")
            
            # 5. Delete procedures
            cur.execute("DELETE FROM procedures WHERE procedure_id != 'test-proc-999'")
            print(f"  ✅ Deleted {proc_count} procedures")
            
            # 6. Delete project_entities
            cur.execute("DELETE FROM project_entities")
            print(f"  ✅ Deleted {project_count} projects")
            
            # 7. Delete candidates
            cur.execute("DELETE FROM crawl_candidates")
            print(f"  ✅ Deleted {candidate_count} candidates")
            
            # 8. Delete stats
            cur.execute("DELETE FROM crawl_stats")
            print(f"  ✅ Deleted crawl stats")
            
            conn.commit()
            
            print("\n✅ Database cleared! Ready for fresh crawl with new recall improvements.")
            print("   All old procedures, projects, candidates, and stats have been removed.")


if __name__ == "__main__":
    confirm = input("⚠️  This will DELETE ALL data from the database. Continue? (yes/no): ")
    if confirm.lower() == "yes":
        clear_old_data()
    else:
        print("❌ Cancelled. Database unchanged.")



