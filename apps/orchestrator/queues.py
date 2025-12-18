import json
import logging
from typing import Any, Dict

import redis

from .config import settings

logger = logging.getLogger(__name__)
_redis = redis.from_url(settings.redis_url)


def enqueue_job(queue: str, payload: Dict[str, Any]) -> None:
    """
    Push payload to Redis list queue.
    """
    _redis.rpush(queue, json.dumps(payload))
    logger.info("Enqueued -> %s: %s", queue, payload)

