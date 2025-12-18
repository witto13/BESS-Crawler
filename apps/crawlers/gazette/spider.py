"""
Amtsblatt crawler with explicit discovery paths.
Focuses on B-Plan announcements and permit notices.
"""
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import time

from ..discovery.amtsblatt_discovery import (
    discover_amtsblatt,
    list_amtsblatt_issues,
    extract_amtsblatt_procedures,
)

logger = logging.getLogger(__name__)

USER_AGENT = "BESS-Forensic-Crawler/1.0 (Research/Transparency; +https://github.com/bess-crawler)"
MIN_REQUEST_DELAY = 1.0
_last_request_time = {}


def _rate_limit(domain: str, min_delay: float = MIN_REQUEST_DELAY):
    """Rate-Limiting: Wartet zwischen Requests."""
    global _last_request_time
    if domain in _last_request_time:
        elapsed = time.time() - _last_request_time[domain]
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
    _last_request_time[domain] = time.time()


def list_issues(feed_url: str, municipality_name: str = "", session: Optional[requests.Session] = None) -> tuple[List[Dict], Dict]:
    """
    List available Amtsblatt issues using explicit discovery.
    
    Returns:
        (issues_list, diagnostics_dict)
    """
    issues = []
    diagnostics = {
        "method": "unknown",
        "attempted_urls": [],
        "failed_urls": {},
        "reason_code": None,
    }
    
    # Step 1: Discover Amtsblatt URL
    # Use feed_url only if it's a valid URL, otherwise discovery will use municipality_name
    valid_feed_url = feed_url if feed_url and (feed_url.startswith("http://") or feed_url.startswith("https://")) else None
    
    # Get official_website_url from session if provided
    official_website_url = None
    if session and hasattr(session, 'official_website_url'):
        official_website_url = session.official_website_url
    
    amtsblatt_url, discovery_diagnostics = discover_amtsblatt(municipality_name, valid_feed_url, official_website_url)
    diagnostics.update(discovery_diagnostics)
    
    # Log diagnostics
    logger.info(
        "Amtsblatt discovery for %s: method=%s, reason=%s, attempted=%d URLs",
        municipality_name or "unknown",
        diagnostics.get("method", "unknown"),
        diagnostics.get("reason_code", "unknown"),
        len(diagnostics.get("attempted_urls", []))
    )
    
    if not amtsblatt_url:
        logger.debug("No Amtsblatt found for %s (feed_url=%s, reason=%s)", 
                    municipality_name or "unknown", feed_url or "empty", diagnostics.get("reason_code"))
        # Only use feed_url if it's valid
        if valid_feed_url:
            amtsblatt_url = feed_url
        else:
            # No valid feed_url and discovery failed - return empty list
            logger.debug("Skipping: no valid feed_url and discovery failed")
            return [], diagnostics
    
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    
    # Step 2: List issues
    issues = list_amtsblatt_issues(amtsblatt_url, sess)
    
    # Fallback to old method if no issues found
    if not issues and valid_feed_url:
        fallback_issues = _list_issues_fallback(feed_url, sess)
        issues = fallback_issues
    
    diagnostics["reason_code"] = "FOUND" if issues else "FOUND_BUT_EMPTY"
    return issues, diagnostics


def _list_issues_fallback(feed_url: str, session: requests.Session) -> List[Dict]:
    """
    Fallback method: List issues from Amtsblatt feed or listing page (old implementation).
    Only works if feed_url is a valid URL.
    """
    if not feed_url or not (feed_url.startswith("http://") or feed_url.startswith("https://")):
        logger.debug("Fallback skipped: invalid feed_url '%s'", feed_url)
        return []
    
    issues = []
    
    try:
        resp = session.get(feed_url, timeout=20)
        if resp.status_code != 200:
            return issues
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for issue links (common patterns: dates, numbers, "Amtsblatt")
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            
            # Heuristics for issue links
            if any(keyword in text.lower() for keyword in ["amtsblatt", "bekanntmachung", "ausgabe", "nummer"]):
                url = urljoin(feed_url, href)
                issues.append({
                    "url": url,
                    "title": text,
                    "date": None,  # Could parse from text
                    "discovery_source": "AMTSBLATT",
                    "discovery_path": feed_url,
                })
    except Exception as e:
        logger.warning("Failed to list issues from %s: %s", feed_url, e)
    
    return issues


def fetch_issue(issue: Dict, session: Optional[requests.Session] = None) -> List[Dict]:
    """
    Fetch procedures from an Amtsblatt issue.
    Only extracts B-Plan and permit announcements.
    """
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    
    issue_url = issue.get("url")
    if not issue_url:
        return []
    
    # Use new discovery method
    procedures = extract_amtsblatt_procedures(issue_url, sess)
    
    # Fallback to old method if no procedures found
    if not procedures:
        return _fetch_issue_fallback(issue, sess)
    
    return procedures


def _fetch_issue_fallback(issue: Dict, session: requests.Session) -> List[Dict]:
    """
    Fallback method: Fetch documents from an Amtsblatt issue (old implementation).
    """
    documents = []
    
    try:
        url = issue.get("url")
        if not url:
            return documents
        
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            return documents
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find PDF/document links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            
            if href.lower().endswith((".pdf", ".doc", ".docx")):
                doc_url = urljoin(url, href)
                documents.append({
                    "doc_url": doc_url,
                    "label": text,
                    "issue_url": url,
                    "discovery_source": "AMTSBLATT",
                    "discovery_path": url,
                })
        
        # Also look for embedded PDFs or iframes
        for iframe in soup.find_all("iframe", src=True):
            src = iframe.get("src", "")
            if ".pdf" in src.lower():
                doc_url = urljoin(url, src)
                documents.append({
                    "doc_url": doc_url,
                    "label": "Embedded PDF",
                    "issue_url": url,
                    "discovery_source": "AMTSBLATT",
                    "discovery_path": url,
                })
    except Exception as e:
        logger.warning("Failed to fetch issue %s: %s", issue.get("url", "unknown"), e)
    
    return documents
