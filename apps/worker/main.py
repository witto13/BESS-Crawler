#!/usr/bin/env python3
"""
Worker main: listens to Redis queue and routes jobs to discovery or extraction workers.
"""
import json
import logging
import sys
import time
import uuid
from typing import Dict, Any

import redis

from apps.orchestrator.config import settings
from apps.worker.discovery_worker import process_discovery_job
from apps.worker.extraction_worker import process_extraction_job
from apps.utils.ssl_config import log_ssl_info, configure_requests_ssl

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure SSL/TLS on startup
logger.info("Initializing SSL/TLS configuration...")
configure_requests_ssl()
log_ssl_info()

# Connect to Redis
_redis = redis.from_url(settings.redis_url)


def main():
    """
    Main worker loop: listen to Redis queue and process jobs.
    Routes jobs based on payload:
    - If payload has 'candidate_id': extraction job
    - Otherwise: discovery job
    """
    run_id = str(uuid.uuid4())
    logger.info("Worker started with run_id: %s", run_id)
    logger.info("Listening to queue: %s", settings.queue_name)
    
    while True:
        try:
            # Blocking pop from queue (BLPOP with 5 second timeout)
            result = _redis.blpop(settings.queue_name, timeout=5)
            
            if result is None:
                # Timeout - no jobs, continue loop
                continue
            
            queue_name, job_data = result
            payload = json.loads(job_data)
            
            logger.info("Processing job: %s", payload.get("source", "unknown"))
            
            # Route job based on payload structure
            if "candidate_id" in payload:
                # Extraction job
                try:
                    process_extraction_job(payload, run_id)
                    logger.info("Extraction job completed successfully")
                except Exception as e:
                    logger.error("Extraction job failed: %s", e, exc_info=True)
            else:
                # Discovery job
                try:
                    process_discovery_job(payload, run_id)
                    logger.info("Discovery job completed successfully")
                except Exception as e:
                    logger.error("Discovery job failed: %s", e, exc_info=True)
        
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error("Worker error: %s", e, exc_info=True)
            # Wait a bit before retrying
            time.sleep(1)


if __name__ == "__main__":
    main()
