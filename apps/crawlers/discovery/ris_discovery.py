"""
RIS (Ratsinformationssystem) discovery with explicit paths.
Focuses on committees and sessions that handle B-Plan and permit procedures.
"""
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import time

from apps.net.ris_http_fallback import ris_safe_get

# Committee allowlist for RIS acceleration (widened slightly)
RIS_COMMITTEE_ALLOWLIST = [
    "bauausschuss",
    "hauptausschuss",
    "gemeindevertretung",
    "stadtverordnetenversammlung",
    "bau- und planungsausschuss",
    "planungsausschuss",
    # Optional: Wirtschaft/Umwelt if present
    "wirtschaftsausschuss",
    "umweltausschuss",
    "wirtschaft",
    "umwelt",
]

try:
    from .municipality_index import RIS_URL_PATTERNS, RIS_COMMITTEE_PATHS, RIS_COMMITTEE_NAMES
except ImportError:
    RIS_COMMITTEE_NAMES = RIS_COMMITTEE_ALLOWLIST
    RIS_COMMITTEE_PATHS = ["/gremien", "/ausschuesse", "/ausschüsse"]
    RIS_URL_PATTERNS = []

logger = logging.getLogger(__name__)

USER_AGENT = "BESS-Forensic-Crawler/1.0 (Research/Transparency; +https://github.com/bess-crawler)"


def discover_ris(
    municipality_name: str,
    base_url: Optional[str] = None,
    official_website_url: Optional[str] = None
) -> tuple[Optional[str], Dict]:
    """
    Discover RIS URL for a municipality.
    Uses site-driven discovery first, then falls back to URL guessing.
    
    Returns:
        (ris_url or None, diagnostics_dict)
    """
    from .municipality_index import discover_ris_urls
    from .site_link_discovery import discover_links_from_official_site
    
    diagnostics = {
        "method": "unknown",
        "attempted_urls": [],
        "failed_urls": {},
        "reason_code": None,
    }
    
    potential_urls = []
    
    # Step 1: Try site-driven discovery from official website
    if official_website_url:
        try:
            logger.info("Attempting site-driven RIS discovery for %s from %s", municipality_name, official_website_url)
            links = discover_links_from_official_site(official_website_url, max_pages=10, max_depth=1)
            ris_urls_from_site = links.get("ris_urls", [])
            
            if ris_urls_from_site:
                potential_urls.extend(ris_urls_from_site)
                diagnostics["method"] = "site_driven"
                diagnostics["attempted_urls"].extend(ris_urls_from_site[:10])
                logger.info("Site-driven discovery found %d RIS URLs for %s", len(ris_urls_from_site), municipality_name)
        except Exception as e:
            logger.warning("Site-driven discovery failed for %s: %s", official_website_url, e)
            diagnostics["failed_urls"]["site_driven"] = str(e)
    
    # Step 2: Fallback to URL guessing patterns
    if not potential_urls:
        logger.debug("No site-driven URLs found, falling back to pattern guessing for %s", municipality_name)
        guessed_urls = discover_ris_urls(municipality_name, base_url)
        potential_urls.extend(guessed_urls)
        diagnostics["method"] = "pattern_guessing"
        diagnostics["attempted_urls"].extend(guessed_urls[:10])
    
    # Step 3: Test each potential URL
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    
    for url in potential_urls:
        try:
            # Try common entry points
            for entry_point in ["", "/si0100.asp", "/si0100.php", "/index.php"]:
                test_url = url.rstrip("/") + entry_point
                # Use ris_safe_get for HTTP fallback support
                resp = ris_safe_get(test_url, session=session, timeout=10, allow_redirects=True)
                if resp and resp.status_code == 200:
                    # Check if it looks like a RIS page
                    if any(term in resp.text.lower() for term in ["sitzung", "gremium", "tagesordnung", "beschluss"]):
                        logger.info("Found RIS at %s (method: %s)", test_url, diagnostics["method"])
                        diagnostics["reason_code"] = "FOUND"
                        return test_url, diagnostics
        except Exception as e:
            error_key = f"{url}:{type(e).__name__}"
            diagnostics["failed_urls"][error_key] = str(e)[:200]
            logger.debug("RIS discovery failed for %s: %s", url, e)
            continue
    
    # No RIS found
    if not potential_urls:
        diagnostics["reason_code"] = "NO_SEED_URL"
    elif all("404" in str(v) or "Not Found" in str(v) for v in diagnostics["failed_urls"].values()):
        diagnostics["reason_code"] = "ALL_URLS_404"
    elif any("SSL" in str(v) or "certificate" in str(v) for v in diagnostics["failed_urls"].values()):
        diagnostics["reason_code"] = "SSL_BLOCKED"
    else:
        diagnostics["reason_code"] = "NO_MARKERS_FOUND"
    
    logger.debug("No RIS found for %s (reason: %s)", municipality_name, diagnostics["reason_code"])
    return None, diagnostics


def discover_committees(ris_base_url: str, session: Optional[requests.Session] = None) -> List[Dict]:
    """
    Discover committees in RIS that handle B-Plan and permit procedures.
    Returns list of committee information.
    """
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    
    committees = []
    
    try:
        # Try to find committee list
        for path in RIS_COMMITTEE_PATHS:
            url = urljoin(ris_base_url, path)
            try:
                resp = ris_safe_get(url, session=sess, timeout=10)
                if resp and resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    
                    # Look for committee links
                    for anchor in soup.find_all("a", href=True):
                        text = anchor.get_text(strip=True).lower()
                        href = anchor["href"]
                        
                        # Check if it's a relevant committee (use allowlist)
                        committee_names = RIS_COMMITTEE_NAMES if RIS_COMMITTEE_NAMES else RIS_COMMITTEE_ALLOWLIST
                        if any(committee_name in text for committee_name in committee_names):
                            committees.append({
                                "name": anchor.get_text(strip=True),
                                "url": urljoin(ris_base_url, href),
                                "discovery_source": "RIS",
                                "discovery_path": url,
                            })
            except Exception as e:
                logger.debug("Failed to check RIS path %s: %s", url, e)
                continue
    except Exception as e:
        logger.warning("Failed to discover committees from RIS %s: %s", ris_base_url, e)
    
    return committees


def crawl_committee_sessions(committee_url: str, session: Optional[requests.Session] = None) -> List[Dict]:
    """
    Crawl sessions from a committee.
    Focuses on sessions with B-Plan or permit items.
    Extracts dates from session titles/text for smart pagination.
    """
    from datetime import datetime
    import re
    
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    
    sessions = []
    
    try:
        resp = ris_safe_get(committee_url, session=sess, timeout=20)
        if not resp or resp.status_code != 200:
            return sessions
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for session links
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            text = anchor.get_text(strip=True)
            
            # Check if it's a session (usually has date)
            if any(term in text.lower() for term in ["sitzung", "sitzungstag", "datum"]):
                session_url = urljoin(committee_url, href)
                
                # Try to extract date from text
                session_date = None
                # Common date patterns: DD.MM.YYYY, DD-MM-YYYY, YYYY-MM-DD
                date_patterns = [
                    r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
                    r'(\d{1,2})-(\d{1,2})-(\d{4})',    # DD-MM-YYYY
                    r'(\d{4})-(\d{1,2})-(\d{1,2})',     # YYYY-MM-DD
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, text)
                    if match:
                        try:
                            if len(match.groups()) == 3:
                                if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                                    year, month, day = match.groups()
                                else:  # DD.MM.YYYY or DD-MM-YYYY
                                    day, month, year = match.groups()
                                session_date = datetime(int(year), int(month), int(day))
                                break
                        except (ValueError, TypeError):
                            continue
                
                sessions.append({
                    "url": session_url,
                    "title": text,
                    "date": session_date,
                    "discovery_source": "RIS",
                    "discovery_path": committee_url,
                })
        
    except Exception as e:
        logger.warning("Failed to crawl committee sessions %s: %s", committee_url, e)
    
    return sessions


def extract_session_items(session_url: str, session: Optional[requests.Session] = None) -> List[Dict]:
    """
    Extract agenda items from a session.
    Widened: looks for privileged project language and energy/speicher terms.
    """
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    
    items = []
    
    try:
        resp = ris_safe_get(session_url, session=sess, timeout=20)
        if not resp or resp.status_code != 200:
            return items
        
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text().lower()
        
        # Expanded keywords for privileged projects
        privileged_terms = [
            "bebauungsplan", "b-plan", "bauleitplanung",
            "bauvorbescheid", "baugenehmigung",
            "einvernehmen", "§ 36", "§36",
            "§ 35", "§35", "§ 34", "§34",
            "bauantrag", "bauvoranfrage", "vorbescheid",
            "stellungnahme", "kenntnisnahme",
            "antrag auf errichtung",
        ]
        
        energy_speicher_terms = [
            "batteriespeicher", "energiespeicher", "speicheranlage",
            "speicher", "photovoltaik", "umspannwerk",
            "energie", "containeranlage",
        ]
        
        # Look for procedure-related items
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            item_text = anchor.get_text(strip=True)
            item_text_lower = item_text.lower()
            
            # Check if it's a B-Plan, permit, or energy-related item
            is_relevant = any(
                term in item_text_lower
                for term in privileged_terms + energy_speicher_terms
            )
            
            if is_relevant:
                item_url = urljoin(session_url, href)
                items.append({
                    "url": item_url,
                    "title": item_text,
                    "discovery_source": "RIS",
                    "discovery_path": session_url,
                })
        
    except Exception as e:
        logger.warning("Failed to extract session items from %s: %s", session_url, e)
    
    return items

