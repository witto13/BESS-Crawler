"""
HTTP client with SSL fallback for known-bad domains.
Provides safe_get() function that handles SSL errors with controlled fallback.
"""
import logging
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.exceptions import SSLError, RequestException

from apps.net.ssl_policy import (
    should_disable_ssl_verify,
    record_ssl_error,
    record_ssl_fallback,
)

logger = logging.getLogger(__name__)


def safe_get(
    url: str,
    session: Optional[requests.Session] = None,
    timeout: int = 30,
    allow_redirects: bool = True,
    headers: Optional[dict] = None,
    verify: bool = True,
    **kwargs
) -> Optional[requests.Response]:
    """
    Safe HTTP GET with SSL fallback for allowlisted domains.
    
    Default behavior: verify=True (normal SSL verification)
    If SSL error occurs AND host is allowlisted: retry once with verify=False
    Otherwise: raise the SSL error
    
    Args:
        url: URL to fetch
        session: Optional requests.Session to use
        timeout: Request timeout
        allow_redirects: Whether to follow redirects
        headers: Optional headers dict
        verify: Initial SSL verification setting (default: True)
        **kwargs: Additional arguments to pass to requests.get()
        
    Returns:
        Response object if successful, None if failed
    """
    sess = session if session is not None else requests.Session()
    
    # Set headers if provided
    if headers:
        sess.headers.update(headers)
    
    # First attempt: always with SSL verification (unless explicitly disabled)
    try:
        resp = sess.get(
            url,
            timeout=timeout,
            allow_redirects=allow_redirects,
            verify=verify,
            **kwargs
        )
        return resp
    except SSLError as ssl_err:
        # SSL error occurred - check if we should use fallback
        record_ssl_error()
        
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if ':' in host:
            host = host.split(':')[0]
        
        # Only use fallback if host is allowlisted
        if should_disable_ssl_verify(url):
            logger.warning(
                "SSL error for allowlisted domain %s: %s - attempting fallback with verify=False",
                host,
                ssl_err
            )
            
            # Retry once with verify=False
            try:
                resp = sess.get(
                    url,
                    timeout=timeout,
                    allow_redirects=allow_redirects,
                    verify=False,
                    **kwargs
                )
                record_ssl_fallback(host, url)
                return resp
            except Exception as fallback_err:
                logger.error(
                    "SSL fallback also failed for %s: %s",
                    url,
                    fallback_err
                )
                return None
        else:
            # SSL error but host is NOT allowlisted - raise the error
            logger.error(
                "SSL error for non-allowlisted domain %s: %s (not using fallback)",
                host,
                ssl_err
            )
            raise
    except RequestException as req_err:
        # Other request errors - just log and return None
        logger.debug("Request error for %s: %s", url, req_err)
        return None
    except Exception as e:
        logger.error("Unexpected error fetching %s: %s", url, e)
        return None

