#!/usr/bin/env python3
"""
Migration: Add crawl_stats table for performance profiling.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool

def migrate():
    pool = get_pool()
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS crawl_stats (
                        run_id UUID NOT NULL,
                        job_id UUID NOT NULL,
                        municipality_key TEXT,
                        source_type VARCHAR(50),
                        domain TEXT,
                        counts_json JSONB,
                        timings_json JSONB,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        PRIMARY KEY (run_id, job_id)
                    );
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_crawl_stats_run_id 
                    ON crawl_stats(run_id);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_crawl_stats_domain 
                    ON crawl_stats(domain);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_crawl_stats_source_type 
                    ON crawl_stats(source_type);
                """)
                
                conn.commit()
                print("✅ Migration successful: Created crawl_stats table")
    except Exception as e:
        print(f"⚠️  Migration error: {e}")
        raise

if __name__ == "__main__":
    migrate()






