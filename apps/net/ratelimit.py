"""
Per-domain rate limiting and global concurrency control.
"""
import asyncio
import time
import logging
from typing import Dict, Optional
from urllib.parse import urlparse
from threading import Semaphore, Lock
import random

logger = logging.getLogger(__name__)

# Global semaphores
_global_semaphore: Optional[Semaphore] = None
_domain_semaphores: Dict[str, Semaphore] = {}
_domain_locks: Dict[str, Lock] = {}
_config_lock = Lock()

# Configuration
_global_concurrency = 100
_per_domain_concurrency = 2
_jitter_ms = (50, 250)


def configure(
    global_concurrency: int = 100,
    per_domain_concurrency: int = 2,
    jitter_ms: tuple = (50, 250)
):
    """
    Configure rate limiting.
    
    Args:
        global_concurrency: Global semaphore limit
        per_domain_concurrency: Per-domain semaphore limit
        jitter_ms: (min, max) jitter in milliseconds
    """
    global _global_semaphore, _global_concurrency, _per_domain_concurrency, _jitter_ms
    
    with _config_lock:
        _global_concurrency = global_concurrency
        _per_domain_concurrency = per_domain_concurrency
        _jitter_ms = jitter_ms
        _global_semaphore = Semaphore(global_concurrency)


def _get_domain_semaphore(domain: str) -> Semaphore:
    """Get or create semaphore for domain."""
    if domain not in _domain_semaphores:
        with _config_lock:
            if domain not in _domain_semaphores:
                _domain_semaphores[domain] = Semaphore(_per_domain_concurrency)
                _domain_locks[domain] = Lock()
    return _domain_semaphores[domain]


def acquire(url: str, mode: str = "fast") -> None:
    """
    Acquire semaphores for URL (blocking).
    
    Args:
        url: URL to fetch
        mode: "fast" (with jitter) or "deep" (no jitter)
    """
    global _global_semaphore
    
    if _global_semaphore is None:
        configure()
    
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Acquire global semaphore
    _global_semaphore.acquire()
    
    # Acquire domain semaphore
    domain_sem = _get_domain_semaphore(domain)
    domain_sem.acquire()
    
    # Add jitter in fast mode
    if mode == "fast" and _jitter_ms:
        jitter = random.uniform(_jitter_ms[0], _jitter_ms[1]) / 1000.0
        time.sleep(jitter)


def release(url: str) -> None:
    """
    Release semaphores for URL.
    
    Args:
        url: URL that was fetched
    """
    global _global_semaphore
    
    if _global_semaphore is None:
        return
    
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Release domain semaphore
    if domain in _domain_semaphores:
        _domain_semaphores[domain].release()
    
    # Release global semaphore
    _global_semaphore.release()






