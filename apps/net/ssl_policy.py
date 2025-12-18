"""
SSL/TLS policy and fallback mechanism for known-bad domains.
Provides controlled SSL verification bypass ONLY for allowlisted domains after SSL failures.
Also provides HTTP fallback for RIS URLs when HTTPS fails.
"""
import logging
import os
from typing import Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Metrics counters
ssl_errors_total = 0
ssl_fallback_used_total = 0
http_fallback_used_total = 0


def get_insecure_ssl_allowlist() -> Set[str]:
    """
    Get the list of domains allowed to bypass SSL verification.
    Configured via CRAWL_SSL_INSECURE_ALLOWLIST environment variable (comma-separated).
    """
    allowlist_str = os.environ.get("CRAWL_SSL_INSECURE_ALLOWLIST", "")
    
    if not allowlist_str:
        return set()
    
    # Parse comma-separated list and normalize (lowercase, strip whitespace)
    domains = {domain.strip().lower() for domain in allowlist_str.split(",") if domain.strip()}
    
    return domains


# Default allowlist for known-bad RIS domains
DEFAULT_INSECURE_SSL_ALLOWLIST = {
    "ssl.ratsinfo-online.net",
}

# Combined allowlist (default + env)
_INSECURE_SSL_ALLOWLIST = None


def _get_allowlist() -> Set[str]:
    """Get the combined allowlist (cached)."""
    global _INSECURE_SSL_ALLOWLIST
    if _INSECURE_SSL_ALLOWLIST is None:
        env_allowlist = get_insecure_ssl_allowlist()
        _INSECURE_SSL_ALLOWLIST = DEFAULT_INSECURE_SSL_ALLOWLIST | env_allowlist
        if _INSECURE_SSL_ALLOWLIST:
            logger.info("SSL insecure allowlist: %s", sorted(_INSECURE_SSL_ALLOWLIST))
    return _INSECURE_SSL_ALLOWLIST


def should_disable_ssl_verify(url: str) -> bool:
    """
    Check if SSL verification should be disabled for a given URL.
    
    This should ONLY be called after an SSL error has occurred.
    Returns True ONLY if the host is in the allowlist.
    
    Args:
        url: The URL to check
        
    Returns:
        True if SSL verification should be disabled (host is allowlisted)
        False otherwise (normal SSL verification should be used)
    """
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in host:
            host = host.split(':')[0]
        
        allowlist = _get_allowlist()
        is_allowlisted = host in allowlist
        
        if is_allowlisted:
            logger.debug("Host %s is in SSL insecure allowlist", host)
        
        return is_allowlisted
    except Exception as e:
        logger.warning("Failed to parse URL for SSL policy check: %s - %s", url, e)
        return False


def record_ssl_error():
    """Record an SSL error occurrence."""
    global ssl_errors_total
    ssl_errors_total += 1


def record_ssl_fallback(host: str, url: str):
    """
    Record that SSL fallback was used for a request.
    
    Args:
        host: The hostname where fallback was used
        url: The full URL where fallback was used
    """
    global ssl_fallback_used_total
    ssl_fallback_used_total += 1
    logger.warning(
        "SSL_FALLBACK_VERIFY_FALSE: host=%s url=%s (SSL verification disabled for allowlisted domain)",
        host,
        url
    )


def get_ssl_metrics() -> dict:
    """
    Get SSL metrics.
    
    Returns:
        Dictionary with ssl_errors_total, ssl_fallback_used_total, and http_fallback_used_total
    """
    return {
        "ssl_errors_total": ssl_errors_total,
        "ssl_fallback_used_total": ssl_fallback_used_total,
        "http_fallback_used_total": http_fallback_used_total,
    }


def is_http_fallback_allowed() -> bool:
    """
    Check if HTTP fallback is allowed.
    Configured via CRAWL_ALLOW_HTTP_FALLBACK environment variable.
    Default: False (HTTP fallback disabled)
    """
    allow_http = os.environ.get("CRAWL_ALLOW_HTTP_FALLBACK", "false").lower()
    return allow_http in ("true", "1", "yes", "on")


def record_http_fallback(original_url: str, http_url: str):
    """
    Record that HTTP fallback was used for a request.
    
    Args:
        original_url: The original HTTPS URL that failed
        http_url: The HTTP URL that was used as fallback
    """
    global http_fallback_used_total
    http_fallback_used_total += 1
    logger.warning(
        "RIS_HTTP_FALLBACK_USED: original=%s http_fallback=%s (HTTPS failed, using HTTP)",
        original_url,
        http_url
    )


def reset_ssl_metrics():
    """Reset SSL metrics (for testing)."""
    global ssl_errors_total, ssl_fallback_used_total, http_fallback_used_total
    ssl_errors_total = 0
    ssl_fallback_used_total = 0
    http_fallback_used_total = 0

