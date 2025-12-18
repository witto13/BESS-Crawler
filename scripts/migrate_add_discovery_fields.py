#!/usr/bin/env python3
"""
Migration: Add discovery fields to sources table.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool

def migrate():
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Add discovery fields to sources table
            try:
                cur.execute("""
                    ALTER TABLE sources
                    ADD COLUMN IF NOT EXISTS discovery_source VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS discovery_path TEXT;
                """)
                conn.commit()
                print("✅ Migration successful: Added discovery fields to sources table")
            except Exception as e:
                print(f"⚠️  Migration note: {e}")
                conn.rollback()

if __name__ == "__main__":
    migrate()






