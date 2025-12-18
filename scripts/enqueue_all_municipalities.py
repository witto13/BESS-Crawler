#!/usr/bin/env python3
"""
Enqueue jobs for ALL Brandenburg municipalities (408 Gemeinden).
Creates jobs for RIS, Amtsblatt, and Municipal Website discovery for each municipality.
"""
import sys
import os
import logging
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool
from apps.orchestrator.queues import enqueue_job
from apps.orchestrator.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sanitize_municipality_name_for_url(name: str) -> str:
    """
    Sanitize municipality name for URL generation.
    Handles special characters, spaces, parentheses, and other problematic characters.
    """
    if not name:
        return ""
    
    # Convert to lowercase
    sanitized = name.lower()
    
    # Remove parentheses and their contents (e.g., "Frankfurt (Oder)" -> "Frankfurt")
    sanitized = re.sub(r'\([^)]*\)', '', sanitized)
    
    # Replace common special characters
    sanitized = sanitized.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    sanitized = sanitized.replace('/', '-').replace('\\', '-')
    sanitized = sanitized.replace('.', '').replace(',', '')
    
    # Replace spaces and multiple dashes with single dash
    sanitized = re.sub(r'[\s_]+', '-', sanitized)
    sanitized = re.sub(r'-+', '-', sanitized)
    
    # Remove leading/trailing dashes and dots
    sanitized = sanitized.strip('-.').strip()
    
    # Remove any remaining invalid characters (keep only alphanumeric, dash, dot)
    sanitized = re.sub(r'[^a-z0-9\-.]', '', sanitized)
    
    # Ensure it's not empty after sanitization
    if not sanitized or sanitized == '-':
        # Fallback: use first word or generate safe name
        words = name.lower().split()
        if words:
            sanitized = re.sub(r'[^a-z0-9]', '', words[0])
        else:
            sanitized = "unknown"
    
    return sanitized


def enqueue_municipality_jobs():
    """
    Enqueue discovery jobs for all Brandenburg municipalities.
    """
    pool = get_pool()
    jobs_enqueued = 0
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Get all Brandenburg municipalities
            cur.execute("""
                SELECT municipality_key, name, county, state
                FROM municipality_seed
                WHERE state = 'BB'
                ORDER BY county, name
            """)
            
            municipalities = cur.fetchall()
            total = len(municipalities)
            logger.info(f"Found {total} Brandenburg municipalities")
            
            for muni_key, name, county, state in municipalities:
                # Sanitize municipality name for URL generation
                sanitized_name = sanitize_municipality_name_for_url(name)
                
                # Job 1: RIS Discovery
                # Use municipality name for discovery (discovery code will generate URLs from name)
                try:
                    enqueue_job(
                        queue=settings.queue_name,
                        payload={
                            "region": state,
                            "source": "ris",
                            "entrypoint": None,  # Discovery will use municipality_name to generate URLs
                            "municipality_key": muni_key,
                            "municipality_name": name,
                            "county": county,
                            "storage_base_path": settings.storage_base_path,
                        },
                    )
                    jobs_enqueued += 1
                except Exception as e:
                    logger.warning(f"Failed to enqueue RIS job for {name}: {e}")
                
                # Job 2: Amtsblatt Discovery
                # Use municipality name for discovery (discovery code will generate URLs from name)
                try:
                    enqueue_job(
                        queue=settings.queue_name,
                        payload={
                            "region": state,
                            "source": "gazette",
                            "entrypoint": None,  # Discovery will use municipality_name to generate URLs
                            "municipality_key": muni_key,
                            "municipality_name": name,
                            "county": county,
                            "storage_base_path": settings.storage_base_path,
                        },
                    )
                    jobs_enqueued += 1
                except Exception as e:
                    logger.warning(f"Failed to enqueue Amtsblatt job for {name}: {e}")
                
                # Job 3: Municipal Website Discovery
                # Generate sanitized URLs using proper sanitization
                if sanitized_name:
                    website_patterns = [
                        f"https://www.{sanitized_name}.de",
                        f"https://{sanitized_name}.de",
                    ]
                    
                    for website_url in website_patterns[:1]:  # Try first pattern only
                        try:
                            enqueue_job(
                                queue=settings.queue_name,
                                payload={
                                    "region": state,
                                    "source": "municipal_website",
                                    "entrypoint": website_url,
                                    "municipality_key": muni_key,
                                    "municipality_name": name,
                                    "county": county,
                                    "storage_base_path": settings.storage_base_path,
                                },
                            )
                            jobs_enqueued += 1
                            break  # Only one website job per municipality
                        except Exception as e:
                            logger.debug(f"Failed to enqueue Municipal Website job for {name} ({website_url}): {e}")
                            continue
                else:
                    logger.debug(f"Skipping Municipal Website job for {name} (could not sanitize name)")
                
                # Progress logging
                if jobs_enqueued % 50 == 0:
                    logger.info(f"Progress: {jobs_enqueued} jobs enqueued...")
    
    logger.info(f"✅ Enqueued {jobs_enqueued} jobs for {total} municipalities")
    logger.info(f"   - ~{total} RIS jobs")
    logger.info(f"   - ~{total} Amtsblatt jobs")
    logger.info(f"   - ~{total} Municipal Website jobs")
    return jobs_enqueued


if __name__ == "__main__":
    jobs = enqueue_municipality_jobs()
    print(f"\n✅ Total: {jobs} jobs enqueued")
    print("🚀 Ready to start crawling!")





