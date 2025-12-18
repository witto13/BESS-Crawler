"""
RIS/SessionNet connector with explicit discovery paths.
Focuses on committees and sessions that handle B-Plan and permit procedures.
"""
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import time

from apps.net.http_client import safe_get
from apps.net.ris_http_fallback import ris_safe_get
from ..discovery.ris_discovery import (
    discover_ris,
    discover_committees,
    crawl_committee_sessions,
    extract_session_items,
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


def discover(base_url: str) -> List[str]:
    """
    Discover SessionNet installations by checking common paths.
    """
    common_paths = [
        "/si0100.asp",
        "/si0100.php",
        "/index.php",
        "/",
    ]
    found = []
    for path in common_paths:
        try:
            url = urljoin(base_url, path)
            resp = ris_safe_get(url, timeout=10, headers={"User-Agent": USER_AGENT})
            if resp and resp.status_code == 200 and "sessionnet" in resp.text.lower():
                found.append(url)
                break
        except:
            continue
    return found


def list_procedures(base_url: str, municipality_name: str = "", session: Optional[requests.Session] = None) -> tuple[List[Dict], Dict]:
    """
    List procedures from RIS/SessionNet using explicit discovery paths.
    Discovery order: RIS -> Committees -> Sessions -> Items
    
    Returns:
        (procedures_list, diagnostics_dict)
    """
    procedures = []
    diagnostics = {
        "method": "unknown",
        "attempted_urls": [],
        "failed_urls": {},
        "reason_code": None,
    }
    
    # Step 1: Discover RIS URL
    # Use base_url only if it's a valid URL, otherwise discovery will use municipality_name
    valid_base_url = base_url if base_url and (base_url.startswith("http://") or base_url.startswith("https://")) else None
    
    # Get official_website_url from session if provided
    official_website_url = None
    if session and hasattr(session, 'official_website_url'):
        official_website_url = session.official_website_url
    
    ris_url, discovery_diagnostics = discover_ris(municipality_name, valid_base_url, official_website_url)
    diagnostics.update(discovery_diagnostics)
    
    # Log diagnostics
    logger.info(
        "RIS discovery for %s: method=%s, reason=%s, attempted=%d URLs",
        municipality_name or "unknown",
        diagnostics.get("method", "unknown"),
        diagnostics.get("reason_code", "unknown"),
        len(diagnostics.get("attempted_urls", []))
    )
    
    if not ris_url:
        logger.debug("No RIS found for %s (base_url=%s, reason=%s)", 
                    municipality_name or "unknown", base_url or "empty", diagnostics.get("reason_code"))
        # Only try fallback if we have a valid base_url
        if valid_base_url:
            fallback_procs, fallback_diagnostics = _list_procedures_fallback(base_url, session)
            diagnostics.update(fallback_diagnostics)
            return fallback_procs, diagnostics
        else:
            # No valid base_url and discovery failed - return empty list with diagnostics
            logger.debug("Skipping fallback: no valid base_url provided")
            return [], diagnostics
    
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    
    # Step 2: Discover committees
    committees = discover_committees(ris_url, sess)
    if not committees:
        logger.debug("No committees found in RIS %s", ris_url)
        # Try direct session listing
        direct_procs, direct_diagnostics = _list_sessions_direct(ris_url, sess)
        diagnostics.update(direct_diagnostics)
        return direct_procs, diagnostics
    
    # Step 3: Crawl sessions from each committee (with smart pagination)
    from datetime import datetime
    cutoff_date = datetime(2023, 1, 1)
    consecutive_old_count = 0
    max_consecutive_old = 3  # Stop after N=3 consecutive old sessions
    
    for committee in committees:
        sessions = crawl_committee_sessions(committee["url"], sess)
        
        # Step 4: Extract items from each session (smart pagination: stop after N=3 consecutive old sessions)
        for session_info in sessions:
            # Check session date
            session_date = session_info.get("date")
            if session_date and isinstance(session_date, datetime):
                if session_date < cutoff_date:
                    consecutive_old_count += 1
                    if consecutive_old_count >= max_consecutive_old:
                        logger.debug("Stopping pagination: %d consecutive old sessions (last: %s < 2023-01-01)", 
                                    consecutive_old_count, session_date)
                        break
                else:
                    # Reset counter if we hit a recent session
                    consecutive_old_count = 0
            else:
                # If no date, assume it might be recent and reset counter
                consecutive_old_count = 0
            
            items = extract_session_items(session_info["url"], sess)
            
            for item in items:
                procedures.append({
                    "url": item["url"],
                    "title": item["title"],
                    "date": session_date,
                    "discovery_source": "RIS",
                    "discovery_path": session_info["discovery_path"],
                })
        
        # Reset counter for next committee
        consecutive_old_count = 0
    
    diagnostics["reason_code"] = "FOUND" if procedures else "FOUND_BUT_EMPTY"
    return procedures, diagnostics


def _list_sessions_direct(ris_url: str, session: requests.Session) -> tuple[List[Dict], Dict]:
    """Fallback: Try to list sessions directly from RIS."""
    procedures = []
    diagnostics = {"method": "direct_fallback", "reason_code": "FOUND_BUT_EMPTY"}
    
    try:
        resp = ris_safe_get(ris_url, session=session, timeout=20)
        if not resp or resp.status_code != 200:
            return procedures, diagnostics
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for session links
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            text = anchor.get_text(strip=True)
            
            if any(term in text.lower() for term in ["sitzung", "tagesordnung", "beschluss"]):
                session_url = urljoin(ris_url, href)
                items = extract_session_items(session_url, session)
                
                for item in items:
                    procedures.append({
                        "url": item["url"],
                        "title": item["title"],
                        "discovery_source": "RIS",
                        "discovery_path": ris_url,
                    })
    except Exception as e:
        logger.warning("Failed to list sessions directly from RIS %s: %s", ris_url, e)
    
    diagnostics["reason_code"] = "FOUND" if procedures else "FOUND_BUT_EMPTY"
    return procedures, diagnostics


def _list_procedures_fallback(base_url: str, session: Optional[requests.Session] = None) -> tuple[List[Dict], Dict]:
    """
    Fallback method: List procedures from SessionNet system (old implementation).
    Only works if base_url is a valid URL.
    """
    diagnostics = {"method": "pattern_fallback", "reason_code": "FOUND_BUT_EMPTY"}
    if not base_url or not (base_url.startswith("http://") or base_url.startswith("https://")):
        logger.debug("Fallback skipped: invalid base_url '%s'", base_url)
        return [], diagnostics
    
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    procedures = []
    
    # Common SessionNet search/list endpoints
    search_urls = [
        urljoin(base_url, "si0100.asp"),
        urljoin(base_url, "si0100.php"),
        urljoin(base_url, "index.php"),
    ]
    
    for search_url in search_urls:
        try:
            resp = sess.get(search_url, timeout=20)
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Look for links to agenda items (common patterns)
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                
                # Heuristics for procedure links
                if any(keyword in href.lower() for keyword in ["si0200", "si0300", "dokument", "vorlage", "antrag"]):
                    url = urljoin(base_url, href)
                    procedures.append({
                        "url": url,
                        "title": text,
                        "source": "sessionnet",
                        "discovery_source": "RIS",
                        "discovery_path": base_url,
                    })
        except Exception as e:
            logger.warning("Failed to fetch from %s: %s", search_url, e)
            continue
    
    diagnostics["reason_code"] = "FOUND" if procedures else "FOUND_BUT_EMPTY"
    return procedures, diagnostics


def fetch_agenda_item(url: str, session: Optional[requests.Session] = None) -> Dict:
    """
    Fetch agenda item details and attachments.
    """
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    try:
        resp = ris_safe_get(url, session=sess, timeout=20)
        if not resp or resp.status_code != 200:
            return {}
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Extract title
        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else ""
        
        # Find document attachments
        documents = []
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if href.lower().endswith((".pdf", ".doc", ".docx")):
                doc_url = urljoin(url, href)
                documents.append({
                    "doc_url": doc_url,
                    "label": link.get_text(strip=True),
                })
        
        return {
            "url": url,
            "title": title_text,
            "documents": documents,
        }
    except Exception as e:
        logger.warning("Failed to fetch agenda item %s: %s", url, e)
        return {}
