#!/usr/bin/env python3
"""
Script to migrate existing database schema to add new fields.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool

def migrate_schema():
    """
    Add new columns to procedures table if they don't exist.
    """
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Add new columns if they don't exist
            migrations = [
                "ALTER TABLE procedures ADD COLUMN IF NOT EXISTS capacity_mw NUMERIC",
                "ALTER TABLE procedures ADD COLUMN IF NOT EXISTS capacity_mwh NUMERIC",
                "ALTER TABLE procedures ADD COLUMN IF NOT EXISTS area_hectares NUMERIC",
                "ALTER TABLE procedures ADD COLUMN IF NOT EXISTS decision_date DATE",
            ]
            
            for migration in migrations:
                try:
                    cur.execute(migration)
                    print(f"✓ {migration}")
                except Exception as e:
                    print(f"✗ {migration}: {e}")
            
            conn.commit()
            print("Schema migration completed!")

if __name__ == "__main__":
    migrate_schema()







