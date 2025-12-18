"""
HTTP fallback for RIS URLs when HTTPS fails.
Only used for RIS extraction and only if explicitly enabled.
"""
import logging
from typing import Optional
from urllib.parse import urlparse, urlunparse

import requests
from requests.exceptions import SSLError, RequestException

from apps.net.ssl_policy import is_http_fallback_allowed, record_http_fallback
from apps.net.http_client import safe_get

logger = logging.getLogger(__name__)


def is_ris_page(content: str) -> bool:
    """
    Check if content looks like a RIS page.
    
    Args:
        content: HTML content to check
        
    Returns:
        True if content contains RIS markers
    """
    content_lower = content.lower()
    ris_markers = [
        "sitzung",
        "gremium",
        "tagesordnung",
        "beschluss",
        "sessionnet",
        "ratsinformationssystem",
        "ris",
        "vorlage",
        "antrag",
    ]
    return any(marker in content_lower for marker in ris_markers)


def ris_safe_get(
    url: str,
    session: Optional[requests.Session] = None,
    timeout: int = 30,
    allow_redirects: bool = True,
    headers: Optional[dict] = None,
    **kwargs
) -> Optional[requests.Response]:
    """
    Safe HTTP GET for RIS URLs with HTTP fallback when HTTPS fails due to SSL errors.
    
    Behavior:
    1. Try HTTPS with normal SSL verification
    2. If SSL error occurs AND HTTP fallback is allowed:
       - Try HTTP:// version of the URL
       - Only accept if response is 200 AND looks like a RIS page
       - Log RIS_HTTP_FALLBACK_USED
    3. Otherwise: return None or raise error
    
    Args:
        url: URL to fetch (should be HTTPS)
        session: Optional requests.Session
        timeout: Request timeout
        allow_redirects: Whether to follow redirects
        headers: Optional headers dict
        **kwargs: Additional arguments to pass to requests
        
    Returns:
        Response object if successful, None if failed
    """
    # Check if original URL was HTTPS
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        # Not HTTPS, just use safe_get normally
        return safe_get(
            url,
            session=session,
            timeout=timeout,
            allow_redirects=allow_redirects,
            headers=headers,
            verify=True,
            **kwargs
        )
    
    # First attempt: HTTPS with normal SSL handling
    sess = session if session is not None else requests.Session()
    if headers:
        sess.headers.update(headers)
    
    ssl_error_occurred = False
    
    try:
        resp = sess.get(
            url,
            timeout=timeout,
            allow_redirects=allow_redirects,
            verify=True,  # Normal SSL verification
            **kwargs
        )
        if resp.status_code == 200:
            return resp
        else:
            # Non-200 status, not an SSL error
            return None
    except SSLError as ssl_err:
        # SSL error occurred - check if we should try HTTP fallback
        ssl_error_occurred = True
        logger.debug("SSL error for RIS URL %s: %s", url, ssl_err)
    except RequestException as req_err:
        # Other request errors - not SSL related, don't try HTTP fallback
        logger.debug("Request error (non-SSL) for RIS URL %s: %s", url, req_err)
        return None
    except Exception as e:
        logger.error("Unexpected error fetching RIS URL %s: %s", url, e)
        return None
    
    # If we get here, HTTPS failed with SSL error
    # Check if HTTP fallback is allowed
    if not is_http_fallback_allowed():
        logger.debug("HTTP fallback not allowed for %s", url)
        return None
    
    if not ssl_error_occurred:
        # No SSL error, don't try HTTP fallback
        return None
    
    # Try HTTP fallback
    http_url = urlunparse((
        "http",  # scheme
        parsed.netloc,  # netloc
        parsed.path,  # path
        parsed.params,  # params
        parsed.query,  # query
        parsed.fragment  # fragment
    ))
    
    logger.info("Attempting HTTP fallback for RIS URL: %s -> %s", url, http_url)
    
    try:
        # Try HTTP (no SSL verification needed)
        http_resp = sess.get(
            http_url,
            timeout=timeout,
            allow_redirects=allow_redirects,
            verify=False,  # HTTP doesn't need SSL verification
            **kwargs
        )
        
        # Only accept if:
        # 1. Status is 200
        # 2. Content looks like a RIS page
        if http_resp.status_code == 200:
            if is_ris_page(http_resp.text):
                record_http_fallback(url, http_url)
                return http_resp
            else:
                logger.warning(
                    "HTTP fallback returned 200 but doesn't look like RIS page: %s",
                    http_url
                )
                return None
        else:
            logger.debug(
                "HTTP fallback returned non-200 status %d: %s",
                http_resp.status_code,
                http_url
            )
            return None
            
    except RequestException as e:
        logger.debug("HTTP fallback also failed for %s: %s", http_url, e)
        return None
    except Exception as e:
        logger.error("Unexpected error in HTTP fallback for %s: %s", http_url, e)
        return None

