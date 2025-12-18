#!/usr/bin/env python3
"""
Migration: Add project_entities and project_procedures tables.
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
                # Create project_entities table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS project_entities (
                        project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        state VARCHAR(2) NOT NULL,
                        municipality_key TEXT,
                        municipality_name TEXT,
                        county TEXT,
                        canonical_project_name TEXT,
                        project_components VARCHAR(50),
                        legal_basis_best VARCHAR(20),
                        site_location_best TEXT,
                        developer_company_best TEXT,
                        capacity_mw_best NUMERIC,
                        capacity_mwh_best NUMERIC,
                        area_hectares_best NUMERIC,
                        maturity_stage VARCHAR(50),
                        first_seen_date DATE,
                        last_seen_date DATE,
                        max_confidence NUMERIC,
                        needs_review BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    );
                """)
                
                # Create project_procedures link table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS project_procedures (
                        project_id UUID NOT NULL REFERENCES project_entities(project_id) ON DELETE CASCADE,
                        procedure_id TEXT NOT NULL REFERENCES procedures(procedure_id) ON DELETE CASCADE,
                        link_confidence NUMERIC,
                        link_reason TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        PRIMARY KEY (project_id, procedure_id)
                    );
                """)
                
                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_project_entities_municipality_name 
                    ON project_entities(municipality_key, canonical_project_name);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_project_entities_developer 
                    ON project_entities(developer_company_best);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_project_entities_location 
                    ON project_entities(site_location_best);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_project_entities_maturity 
                    ON project_entities(maturity_stage);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_project_entities_first_seen 
                    ON project_entities(first_seen_date);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_project_procedures_procedure 
                    ON project_procedures(procedure_id);
                """)
                
                conn.commit()
                print("✅ Migration successful: Created project_entities and project_procedures tables")
    except Exception as e:
        print(f"⚠️  Migration error: {e}")
        raise

if __name__ == "__main__":
    migrate()

