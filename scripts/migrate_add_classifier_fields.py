#!/usr/bin/env python3
"""
Migration: Add classifier fields to procedures table.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool

def migrate():
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Add new classifier fields
            try:
                cur.execute("""
                    ALTER TABLE procedures
                    ADD COLUMN IF NOT EXISTS procedure_type VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS legal_basis VARCHAR(20),
                    ADD COLUMN IF NOT EXISTS project_components VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS ambiguity_flag BOOLEAN DEFAULT FALSE,
                    ADD COLUMN IF NOT EXISTS review_recommended BOOLEAN DEFAULT FALSE,
                    ADD COLUMN IF NOT EXISTS site_location_raw TEXT,
                    ADD COLUMN IF NOT EXISTS evidence_snippets JSONB;
                """)
                conn.commit()
                print("✅ Migration successful: Added classifier fields")
            except Exception as e:
                print(f"⚠️  Migration note: {e}")
                conn.rollback()

if __name__ == "__main__":
    migrate()






