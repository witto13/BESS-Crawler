#!/usr/bin/env python3
"""
Orchestrator main: continuously schedules discovery jobs for municipalities.
Checks municipality_seed table and enqueues discovery jobs for municipalities
that haven't been crawled recently or at all.
"""
import logging
import signal
import sys
import time
from datetime import datetime, timedelta

from apps.db.client import get_pool
from apps.orchestrator.config import settings
from apps.orchestrator.queues import enqueue_job

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CHECK_INTERVAL_SECONDS = 60  # How often to check for new municipalities to crawl
BATCH_SIZE = 10  # How many municipalities to enqueue per cycle
RESCAN_INTERVAL_DAYS = 7  # Re-crawl municipalities after this many days

# Global flag for graceful shutdown
_shutdown = False


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown
    logger.info("Received shutdown signal, exiting...")
    _shutdown = True


def get_due_municipalities(pool, limit: int = BATCH_SIZE):
    """
    Select municipalities that have never been crawled or haven't been crawled recently.
    
    Returns municipalities from municipality_seed that either:
    - Have no recent crawl_stats entries, OR
    - Have crawl_stats entries older than RESCAN_INTERVAL_DAYS
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Find municipalities that need crawling
            # This query finds municipalities that either:
            # 1. Have no crawl_stats entries, OR
            # 2. Have their most recent crawl_stats entry older than RESCAN_INTERVAL_DAYS
            query = """
                SELECT DISTINCT ms.municipality_key, ms.name, ms.county, ms.state
                FROM municipality_seed ms
                LEFT JOIN LATERAL (
                    SELECT MAX(created_at) as last_crawled
                    FROM crawl_stats
                    WHERE municipality_key = ms.municipality_key
                ) cs ON true
                WHERE ms.state = 'BB'
                  AND (cs.last_crawled IS NULL 
                       OR cs.last_crawled < NOW() - INTERVAL '%s days')
                ORDER BY cs.last_crawled NULLS FIRST, ms.municipality_key
                LIMIT %s;
            """
            cur.execute(query, (RESCAN_INTERVAL_DAYS, limit))
            return cur.fetchall()


def sanitize_municipality_name_for_url(name: str) -> str:
    """
    Sanitize municipality name for URL generation.
    Handles special characters, spaces, parentheses, and other problematic characters.
    """
    import re
    
    if not name:
        return ""
    
    # Convert to lowercase
    sanitized = name.lower()
    
    # Remove parentheses and their contents (e.g., "Frankfurt (Oder)" -> "Frankfurt")
    sanitized = re.sub(r'\([^)]*\)', '', sanitized)
    
    # Replace common special characters
    sanitized = sanitized.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    sanitized = sanitized.replace('/', '-').replace('\\', '-')
    
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


def enqueue_municipality_discovery_jobs(municipality_key: str, name: str, county: str, state: str):
    """
    Enqueue discovery jobs for a municipality (RIS, Amtsblatt, Municipal Website).
    """
    sanitized_name = sanitize_municipality_name_for_url(name)
    jobs_enqueued = 0
    
    # Job 1: RIS Discovery
    try:
        enqueue_job(
            queue=settings.queue_name,
            payload={
                "region": state,
                "source": "ris",
                "entrypoint": None,  # Discovery will use municipality_name to generate URLs
                "municipality_key": municipality_key,
                "municipality_name": name,
                "county": county,
                "storage_base_path": settings.storage_base_path,
            },
        )
        jobs_enqueued += 1
    except Exception as e:
        logger.warning(f"Failed to enqueue RIS job for {name}: {e}")
    
    # Job 2: Amtsblatt Discovery
    try:
        enqueue_job(
            queue=settings.queue_name,
            payload={
                "region": state,
                "source": "gazette",
                "entrypoint": None,  # Discovery will use municipality_name to generate URLs
                "municipality_key": municipality_key,
                "municipality_name": name,
                "county": county,
                "storage_base_path": settings.storage_base_path,
            },
        )
        jobs_enqueued += 1
    except Exception as e:
        logger.warning(f"Failed to enqueue Amtsblatt job for {name}: {e}")
    
    # Job 3: Municipal Website Discovery
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
                        "municipality_key": municipality_key,
                        "municipality_name": name,
                        "county": county,
                        "storage_base_path": settings.storage_base_path,
                    },
                )
                jobs_enqueued += 1
            except Exception as e:
                logger.warning(f"Failed to enqueue Municipal Website job for {name} ({website_url}): {e}")
    
    return jobs_enqueued


def main():
    """
    Main orchestrator loop.
    Continuously checks for municipalities that need crawling and enqueues discovery jobs.
    """
    logger.info("=" * 60)
    logger.info("BESS Crawler Orchestrator starting...")
    logger.info("=" * 60)
    logger.info("Redis URL: %s", settings.redis_url)
    logger.info("Queue name: %s", settings.queue_name)
    logger.info("Check interval: %s seconds", CHECK_INTERVAL_SECONDS)
    logger.info("Batch size: %s municipalities per cycle", BATCH_SIZE)
    logger.info("Rescan interval: %s days", RESCAN_INTERVAL_DAYS)
    logger.info("=" * 60)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    pool = get_pool()
    total_jobs_enqueued = 0
    cycle_count = 0
    
    try:
        while not _shutdown:
            cycle_count += 1
            logger.info("--- Orchestrator cycle #%d ---", cycle_count)
            
            try:
                # Get municipalities that need crawling
                candidates = get_due_municipalities(pool, limit=BATCH_SIZE)
                
                if not candidates:
                    logger.info("No municipalities need crawling at this time. Sleeping for %ds...", CHECK_INTERVAL_SECONDS)
                    time.sleep(CHECK_INTERVAL_SECONDS)
                    continue
                
                logger.info("Found %d municipalities to crawl", len(candidates))
                
                # Enqueue discovery jobs for each municipality
                cycle_jobs = 0
                for muni_key, name, county, state in candidates:
                    jobs = enqueue_municipality_discovery_jobs(muni_key, name, county, state)
                    cycle_jobs += jobs
                    total_jobs_enqueued += jobs
                    logger.info("Queued %d discovery job(s) for: %s (key: %s)", jobs, name, muni_key)
                
                logger.info("Cycle complete: enqueued %d total jobs (%d municipalities)", cycle_jobs, len(candidates))
                logger.info("Total jobs enqueued since start: %d", total_jobs_enqueued)
                
                # Sleep before next cycle
                time.sleep(CHECK_INTERVAL_SECONDS)
                
            except Exception as e:
                logger.error("Error in orchestrator cycle: %s", e, exc_info=True)
                # Sleep on error to prevent tight loop
                time.sleep(10)
                
    except KeyboardInterrupt:
        logger.info("Orchestrator interrupted by user")
    except Exception as e:
        logger.error("Fatal orchestrator error: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        logger.info("=" * 60)
        logger.info("Orchestrator shutting down...")
        logger.info("Total jobs enqueued: %d", total_jobs_enqueued)
        logger.info("Total cycles: %d", cycle_count)
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
