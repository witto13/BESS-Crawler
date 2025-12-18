"""
Cached downloader with conditional GETs and HEAD-before-GET for PDFs.
"""
from typing import Optional, Dict, Tuple
import requests
import logging
from pathlib import Path
from urllib.parse import urlparse

from apps.downloader.fetch import USER_AGENT, check_robots_txt, _rate_limit
from apps.net.cache import get_cached, set_cached, get_cache_headers
from apps.net.ratelimit import acquire, release
from apps.orchestrator.config import settings

logger = logging.getLogger(__name__)


def download_cached(
    url: str,
    timeout: int = None,
    max_retries: int = None,
    check_robots: bool = True,
    mode: str = "fast",
    use_cache: bool = True
) -> Optional[Tuple[bytes, Dict]]:
    """
    Download URL with caching and conditional GETs.
    
    Args:
        url: URL to download
        timeout: Request timeout (defaults to settings.crawl_timeout_s)
        max_retries: Maximum retries (defaults to settings.crawl_retries)
        check_robots: Whether to check robots.txt
        mode: "fast" or "deep"
        use_cache: Whether to use cache
    
    Returns:
        (content_bytes, headers_dict) or None
    """
    if timeout is None:
        timeout = settings.crawl_timeout_s
    if max_retries is None:
        max_retries = settings.crawl_retries
    
    # Check robots.txt
    if check_robots and not check_robots_txt(url):
        logger.warning("robots.txt disallows: %s", url)
        return None
    
    # Check cache
    cache_base = Path(settings.crawl_cache_base)
    if use_cache:
        cached = get_cached(url, cache_base)
        if cached:
            content, metadata = cached
            logger.debug("Cache hit: %s", url)
            return content, metadata
    
    # Acquire rate limit semaphores
    acquire(url, mode)
    
    try:
        # Rate limiting
        _rate_limit(url)
        
        headers = {
            'User-Agent': USER_AGENT
        }
        
        # Add conditional headers if cached
        if use_cache:
            cache_headers = get_cache_headers(url, cache_base)
            headers.update(cache_headers)
        
        # Retry loop
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers)
                
                # 304 Not Modified - use cached
                if resp.status_code == 304:
                    logger.debug("304 Not Modified: %s", url)
                    cached = get_cached(url, cache_base)
                    if cached:
                        return cached
                
                # 200 OK
                if resp.status_code == 200:
                    content = resp.content
                    resp_headers = dict(resp.headers)
                    
                    # Store in cache
                    if use_cache:
                        set_cached(url, content, resp_headers, cache_base)
                    
                    return content, resp_headers
                
                # 404
                elif resp.status_code == 404:
                    logger.debug("URL not found (404): %s", url)
                    return None
                
                # Other status
                else:
                    logger.warning("HTTP %d for %s", resp.status_code, url)
                    
            except requests.exceptions.Timeout:
                logger.warning("Timeout downloading %s (attempt %d/%d)", url, attempt + 1, max_retries)
            except requests.exceptions.RequestException as e:
                logger.warning("Error downloading %s: %s (attempt %d/%d)", url, e, attempt + 1, max_retries)
            
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
        
    finally:
        release(url)


def head_cached(
    url: str,
    timeout: int = None,
    mode: str = "fast"
) -> Optional[Dict]:
    """
    Send HEAD request to get headers (for size check before PDF download).
    
    Returns:
        headers_dict or None
    """
    if timeout is None:
        timeout = settings.crawl_timeout_s
    
    # Check robots.txt
    if not check_robots_txt(url):
        return None
    
    # Acquire rate limit
    acquire(url, mode)
    
    try:
        _rate_limit(url)
        
        headers = {
            'User-Agent': USER_AGENT
        }
        
        # Add conditional headers from cache
        cache_base = Path(settings.crawl_cache_base)
        cache_headers = get_cache_headers(url, cache_base)
        headers.update(cache_headers)
        
        resp = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
        
        if resp.status_code == 200:
            return dict(resp.headers)
        elif resp.status_code == 304:
            # Not modified - get from cache
            cached = get_cached(url, cache_base)
            if cached:
                _, metadata = cached
                return metadata
        
        return None
        
    except Exception as e:
        logger.warning("Error HEAD %s: %s", url, e)
        return None
    finally:
        release(url)






