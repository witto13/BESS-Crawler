"""
HTTP caching: store responses for HTML and PDF based on URL, ETag, Last-Modified.
Cache backend: local disk keyed by sha256(url).
"""
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime, timezone
import os

logger = logging.getLogger(__name__)


def _url_hash(url: str) -> str:
    """Compute SHA256 hash of URL for cache key."""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def _get_cache_path(base_path: Path, url: str, suffix: str = ".bin") -> Tuple[Path, Path]:
    """
    Get cache file path and metadata path.
    
    Returns:
        (content_path, metadata_path)
    """
    url_hash = _url_hash(url)
    # Use first 2 chars for directory structure
    cache_dir = base_path / url_hash[:2]
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    content_path = cache_dir / f"{url_hash}{suffix}"
    metadata_path = cache_dir / f"{url_hash}.meta.json"
    
    return content_path, metadata_path


def get_cached(
    url: str,
    base_path: Path,
    max_age_seconds: Optional[int] = None
) -> Optional[Tuple[bytes, Dict]]:
    """
    Get cached content and metadata if available and fresh.
    
    Args:
        url: URL to look up
        base_path: Base cache directory
        max_age_seconds: Maximum age in seconds (None = no expiry)
    
    Returns:
        (content_bytes, metadata_dict) or None if not cached/fresh
    """
    content_path, metadata_path = _get_cache_path(base_path, url)
    
    if not content_path.exists() or not metadata_path.exists():
        return None
    
    try:
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Check age if specified
        if max_age_seconds:
            cached_time = datetime.fromisoformat(metadata.get('cached_at', ''))
            age = (datetime.now(timezone.utc) - cached_time.replace(tzinfo=timezone.utc)).total_seconds()
            if age > max_age_seconds:
                return None
        
        # Load content
        with open(content_path, 'rb') as f:
            content = f.read()
        
        return content, metadata
    except Exception as e:
        logger.debug("Error reading cache for %s: %s", url, e)
        return None


def set_cached(
    url: str,
    content: bytes,
    headers: Dict,
    base_path: Path
) -> None:
    """
    Store content and metadata in cache.
    
    Args:
        url: URL
        content: Response content
        headers: Response headers
        base_path: Base cache directory
    """
    content_path, metadata_path = _get_cache_path(base_path, url)
    
    try:
        # Store content
        with open(content_path, 'wb') as f:
            f.write(content)
        
        # Store metadata
        metadata = {
            'url': url,
            'cached_at': datetime.now(timezone.utc).isoformat(),
            'content_length': len(content),
            'etag': headers.get('ETag'),
            'last_modified': headers.get('Last-Modified'),
            'content_type': headers.get('Content-Type'),
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.warning("Error writing cache for %s: %s", url, e)


def get_cache_headers(url: str, base_path: Path) -> Dict[str, str]:
    """
    Get conditional request headers (If-None-Match, If-Modified-Since) from cache.
    
    Args:
        url: URL
        base_path: Base cache directory
    
    Returns:
        Dict with conditional headers
    """
    cached = get_cached(url, base_path)
    if not cached:
        return {}
    
    _, metadata = cached
    headers = {}
    
    if metadata.get('etag'):
        headers['If-None-Match'] = metadata['etag']
    
    if metadata.get('last_modified'):
        headers['If-Modified-Since'] = metadata['last_modified']
    
    return headers






