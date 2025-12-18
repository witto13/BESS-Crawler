"""
Queue management for the BESS crawler.
Handles Redis queue operations for job distribution between orchestrator, discovery, and extraction workers.
"""
import json
import logging
from typing import Any, Dict

import redis

from .config import settings

logger = logging.getLogger(__name__)

# Initialize Redis connection
_redis = redis.from_url(settings.redis_url, decode_responses=False)


# Queue name constants
# Note: The system uses a single queue with payload-based routing
# Discovery jobs: payload without 'candidate_id'
# Extraction jobs: payload with 'candidate_id'
QUEUE_DISCOVERY = settings.queue_name  # Default: "crawl"
QUEUE_EXTRACTION = settings.queue_name  # Same queue, different payload structure


def get_queue_connection():
    """
    Returns a connection to the Redis queue.
    Can be used for direct queue operations if needed.
    """
    return redis.from_url(settings.redis_url, decode_responses=False)


def enqueue_job(queue: str, payload: Dict[str, Any]) -> None:
    """
    Push payload to Redis list queue.
    
    Args:
        queue: Queue name (typically settings.queue_name / "crawl")
        payload: Job payload dictionary
        
    Note: Both discovery and extraction jobs use the same queue.
    The worker routes jobs based on payload structure:
    - If payload has 'candidate_id': extraction job
    - Otherwise: discovery job
    """
    _redis.rpush(queue, json.dumps(payload))
    job_type = "extraction" if "candidate_id" in payload else "discovery"
    logger.info("Enqueued %s job -> %s: %s", job_type, queue, payload.get("source", "unknown"))


def enqueue_discovery_job(payload: Dict[str, Any]) -> None:
    """
    Convenience function to enqueue a discovery job.
    Discovery jobs are identified by NOT having a 'candidate_id' field.
    """
    enqueue_job(QUEUE_DISCOVERY, payload)


def enqueue_extraction_job(payload: Dict[str, Any]) -> None:
    """
    Convenience function to enqueue an extraction job.
    Extraction jobs must have a 'candidate_id' field.
    """
    if "candidate_id" not in payload:
        logger.warning("Extraction job missing 'candidate_id' field: %s", payload)
    enqueue_job(QUEUE_EXTRACTION, payload)
