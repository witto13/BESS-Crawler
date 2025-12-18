#!/usr/bin/env python3
"""
Script to add RIS and Gazette jobs for each municipality in Brandenburg.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool
from apps.orchestrator.queues import enqueue_job
from apps.orchestrator.config import settings

def add_municipality_jobs():
    """
    Add RIS and Gazette jobs for each Brandenburg municipality.
    """
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Get all Brandenburg municipalities
            cur.execute("""
                SELECT municipality_key, name, county
                FROM municipality_seed
                WHERE state = 'BB'
            """)
            
            municipalities = cur.fetchall()
            print(f"Found {len(municipalities)} Brandenburg municipalities")
            
            job_count = 0
            for muni_key, name, county in municipalities:
                # Try common RIS patterns
                ris_patterns = [
                    f"https://{name.lower().replace(' ', '').replace('-', '')}.sessionnet.de",
                    f"https://ris.{name.lower().replace(' ', '').replace('-', '')}.de",
                    f"https://{name.lower().replace(' ', '-')}.sessionnet.de",
                ]
                
                for ris_url in ris_patterns:
                    enqueue_job(
                        queue=settings.queue_name,
                        payload={
                            "region": "BB",
                            "source": "ris",
                            "entrypoint": ris_url,
                            "municipality_key": muni_key,
                            "storage_base_path": settings.storage_base_path,
                        },
                    )
                    job_count += 1
                
                # Try common Gazette patterns
                gazette_patterns = [
                    f"https://{name.lower().replace(' ', '').replace('-', '')}.de/amtsblatt",
                    f"https://{name.lower().replace(' ', '-')}.de/bekanntmachungen",
                    f"https://www.{name.lower().replace(' ', '-')}.de/amtsblatt",
                ]
                
                for gazette_url in gazette_patterns:
                    enqueue_job(
                        queue=settings.queue_name,
                        payload={
                            "region": "BB",
                            "source": "gazette",
                            "entrypoint": gazette_url,
                            "municipality_key": muni_key,
                            "storage_base_path": settings.storage_base_path,
                        },
                    )
                    job_count += 1
            
            print(f"Enqueued {job_count} RIS/Gazette jobs")

if __name__ == "__main__":
    add_municipality_jobs()







