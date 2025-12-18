#!/usr/bin/env python3
"""
Migration: Add crawl_candidates table for 2-stage pipeline.
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
                # Create enum type for status
                cur.execute("""
                    DO $$ BEGIN
                        CREATE TYPE candidate_status AS ENUM ('NEW', 'SKIPPED', 'ENQUEUED', 'DONE', 'ERROR');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """)
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS crawl_candidates (
                        candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        run_id UUID NOT NULL,
                        municipality_key TEXT,
                        discovery_source VARCHAR(50),
                        discovery_path TEXT,
                        title TEXT,
                        date_hint DATE,
                        url TEXT NOT NULL,
                        doc_urls JSONB,
                        prefilter_score NUMERIC,
                        status candidate_status DEFAULT 'NEW',
                        reason TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    );
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_candidates_run_id 
                    ON crawl_candidates(run_id);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_candidates_status 
                    ON crawl_candidates(status);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_candidates_prefilter_score 
                    ON crawl_candidates(prefilter_score);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_candidates_municipality 
                    ON crawl_candidates(municipality_key, discovery_source);
                """)
                
                conn.commit()
                print("✅ Migration successful: Created crawl_candidates table")
    except Exception as e:
        print(f"⚠️  Migration error: {e}")
        raise

if __name__ == "__main__":
    migrate()






