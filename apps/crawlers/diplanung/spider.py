"""
Minimal DiPlanung spider.

This is intentionally conservative: it fetches the entrypoint, extracts likely
procedure links, and returns metadata records. Refine selectors per portal if
needed.

Compliance: User-Agent, Rate-Limiting.
"""

from typing import List, Dict, Optional
from urllib.parse import urljoin
import time

import requests
from bs4 import BeautifulSoup

# User-Agent für Compliance
USER_AGENT = "BESS-Forensic-Crawler/1.0 (Research/Transparency; +https://github.com/bess-crawler)"
MIN_REQUEST_DELAY = 1.0  # Mindest-Delay zwischen Requests
_last_request_time = {}


def _rate_limit(domain: str, min_delay: float = MIN_REQUEST_DELAY):
    """Rate-Limiting: Wartet zwischen Requests."""
    global _last_request_time
    if domain in _last_request_time:
        elapsed = time.time() - _last_request_time[domain]
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
    _last_request_time[domain] = time.time()


def list_procedures(entrypoint: str, session: Optional[requests.Session] = None) -> List[Dict]:
    from urllib.parse import urlparse
    parsed = urlparse(entrypoint)
    domain = parsed.netloc
    
    # Rate-Limiting
    _rate_limit(domain)
    
    sess = session or requests.Session()
    headers = {'User-Agent': USER_AGENT}
    resp = sess.get(entrypoint, timeout=20, headers=headers)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    records: List[Dict] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        # Heuristic: DiPlanung procedure detail pages often contain "verfahren"
        if "verfahren" in href or "participation" in href:
            url = urljoin(entrypoint, href)
            title = anchor.get_text(strip=True)
            records.append({"url": url, "title": title})
    return records


def fetch_documents(detail_url: str, session: Optional[requests.Session] = None) -> List[Dict]:
    """
    Scrape a detail page for document links.
    """
    from urllib.parse import urlparse
    parsed = urlparse(detail_url)
    domain = parsed.netloc
    
    # Rate-Limiting
    _rate_limit(domain)
    
    sess = session or requests.Session()
    headers = {'User-Agent': USER_AGENT}
    resp = sess.get(detail_url, timeout=20, headers=headers)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    docs: List[Dict] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.lower().endswith((".pdf", ".doc", ".docx")):
            docs.append(
                {
                    "doc_url": urljoin(detail_url, href),
                    "label": anchor.get_text(strip=True),
                }
            )
    return docs

