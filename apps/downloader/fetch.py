"""
Robust downloader with retries and error handling.
Compliance: User-Agent, Rate-Limiting, robots.txt respect.
"""
from typing import Optional, Dict
import hashlib
import requests
import logging
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from apps.net.http_client import safe_get

logger = logging.getLogger(__name__)

# User-Agent für Compliance
USER_AGENT = "BESS-Forensic-Crawler/1.0 (Research/Transparency; +https://github.com/bess-crawler)"

# Rate-Limiting: Mindest-Delay zwischen Requests (in Sekunden)
# Domain-spezifische Delays (basierend auf robots.txt)
DOMAIN_DELAYS = {
    'geobasis-bb.de': 10.0,  # robots.txt erfordert crawl-delay: 10
    'www.geobasis-bb.de': 10.0,
}
MIN_REQUEST_DELAY = 1.0  # Default für andere Domains
_last_request_time = {}

# Robots.txt Cache
_robots_cache = {}


def check_robots_txt(url: str) -> bool:
    """
    Prüft robots.txt und gibt True zurück, wenn URL gecrawlt werden darf.
    """
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Cache prüfen
        if base_url in _robots_cache:
            rp = _robots_cache[base_url]
        else:
            rp = RobotFileParser()
            rp.set_url(f"{base_url}/robots.txt")
            try:
                rp.read()
                _robots_cache[base_url] = rp
            except Exception as e:
                logger.debug("Could not read robots.txt for %s: %s", base_url, e)
                # Wenn robots.txt nicht erreichbar, erlauben (konservativ)
                return True
        
        return rp.can_fetch(USER_AGENT, url)
    except Exception as e:
        logger.debug("Error checking robots.txt for %s: %s", url, e)
        # Bei Fehler erlauben (konservativ)
        return True


def _rate_limit(url: str, min_delay: Optional[float] = None):
    """
    Rate-Limiting: Wartet zwischen Requests.
    Domain-spezifische Delays werden respektiert (z.B. geobasis-bb.de: 10s).
    """
    global _last_request_time
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Domain-spezifisches Delay oder Default
    if min_delay is None:
        min_delay = DOMAIN_DELAYS.get(domain, MIN_REQUEST_DELAY)
    
    if domain in _last_request_time:
        elapsed = time.time() - _last_request_time[domain]
        if elapsed < min_delay:
            sleep_time = min_delay - elapsed
            logger.debug("Rate-limiting: waiting %.1fs for %s", sleep_time, domain)
            time.sleep(sleep_time)
    
    _last_request_time[domain] = time.time()


def download(url: str, timeout: int = 30, max_retries: int = 3, check_robots: bool = True) -> Optional[bytes]:
    """
    Download URL with retries and error handling.
    
    Args:
        url: URL to download
        timeout: Request timeout
        max_retries: Maximum retry attempts
        check_robots: Whether to check robots.txt (default: True)
    """
    # Prüfe robots.txt
    if check_robots and not check_robots_txt(url):
        logger.warning("robots.txt disallows: %s", url)
        return None
    
    # Rate-Limiting
    _rate_limit(url)
    
    headers = {
        'User-Agent': USER_AGENT
    }
    
    for attempt in range(max_retries):
        try:
            # Use safe_get for SSL fallback support
            resp = safe_get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers=headers,
                verify=True  # Default: verify SSL, fallback only for allowlisted domains
            )
            
            if resp is None:
                # Request failed (handled by safe_get)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
            
            if resp.status_code == 200:
                return resp.content
            elif resp.status_code == 404:
                logger.debug("URL not found (404): %s", url)
                return None
            else:
                logger.warning("HTTP %d for %s", resp.status_code, url)
        except requests.exceptions.Timeout:
            logger.warning("Timeout downloading %s (attempt %d/%d)", url, attempt + 1, max_retries)
        except requests.exceptions.RequestException as e:
            logger.warning("Error downloading %s: %s (attempt %d/%d)", url, e, attempt + 1, max_retries)
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

