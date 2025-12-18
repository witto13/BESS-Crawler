"""
Amtsblatt discovery with explicit paths.
Focuses on B-Plan announcements and permit notices.
"""
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import time

from apps.net.http_client import safe_get
from .municipality_index import AMTSBLATT_PATTERNS

logger = logging.getLogger(__name__)

USER_AGENT = "BESS-Forensic-Crawler/1.0 (Research/Transparency; +https://github.com/bess-crawler)"


def discover_amtsblatt(
    municipality_name: str,
    base_url: Optional[str] = None,
    official_website_url: Optional[str] = None
) -> tuple[Optional[str], Dict]:
    """
    Discover Amtsblatt URL for a municipality.
    Uses site-driven discovery first, then falls back to URL guessing.
    
    Returns:
        (amtsblatt_url or None, diagnostics_dict)
    """
    from .municipality_index import discover_amtsblatt_urls
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
            logger.info("Attempting site-driven Amtsblatt discovery for %s from %s", municipality_name, official_website_url)
            links = discover_links_from_official_site(official_website_url, max_pages=10, max_depth=1)
            amtsblatt_urls_from_site = links.get("amtsblatt_urls", []) + links.get("bekanntmachung_urls", [])
            
            if amtsblatt_urls_from_site:
                potential_urls.extend(amtsblatt_urls_from_site)
                diagnostics["method"] = "site_driven"
                diagnostics["attempted_urls"].extend(amtsblatt_urls_from_site[:10])
                logger.info("Site-driven discovery found %d Amtsblatt URLs for %s", len(amtsblatt_urls_from_site), municipality_name)
        except Exception as e:
            logger.warning("Site-driven discovery failed for %s: %s", official_website_url, e)
            diagnostics["failed_urls"]["site_driven"] = str(e)
    
    # Step 2: Fallback to URL guessing patterns
    if not potential_urls:
        logger.debug("No site-driven URLs found, falling back to pattern guessing for %s", municipality_name)
        guessed_urls = discover_amtsblatt_urls(municipality_name, base_url)
        potential_urls.extend(guessed_urls)
        diagnostics["method"] = "pattern_guessing"
        diagnostics["attempted_urls"].extend(guessed_urls[:10])
    
    # Step 3: Test each potential URL
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    
    for url in potential_urls:
        try:
            resp = safe_get(url, session=session, timeout=10, allow_redirects=True, verify=True)
            if resp and resp.status_code == 200:
                # Check if it looks like an Amtsblatt page
                text_lower = resp.text.lower()
                if any(term in text_lower for term in ["amtsblatt", "bekanntmachung", "veröffentlichung", "ausgabe"]):
                    logger.info("Found Amtsblatt at %s (method: %s)", url, diagnostics["method"])
                    diagnostics["reason_code"] = "FOUND"
                    return url, diagnostics
        except Exception as e:
            error_key = f"{url}:{type(e).__name__}"
            diagnostics["failed_urls"][error_key] = str(e)[:200]
            logger.debug("Amtsblatt discovery failed for %s: %s", url, e)
            continue
    
    # No Amtsblatt found
    if not potential_urls:
        diagnostics["reason_code"] = "NO_SEED_URL"
    elif all("404" in str(v) or "Not Found" in str(v) for v in diagnostics["failed_urls"].values()):
        diagnostics["reason_code"] = "ALL_URLS_404"
    elif any("SSL" in str(v) or "certificate" in str(v) for v in diagnostics["failed_urls"].values()):
        diagnostics["reason_code"] = "SSL_BLOCKED"
    else:
        diagnostics["reason_code"] = "NO_MARKERS_FOUND"
    
    logger.debug("No Amtsblatt found for %s (reason: %s)", municipality_name, diagnostics["reason_code"])
    return None, diagnostics


def list_amtsblatt_issues(amtsblatt_url: str, session: Optional[requests.Session] = None) -> List[Dict]:
    """
    List all available Amtsblatt issues.
    Returns list of issue metadata.
    """
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    
    issues = []
    
    try:
        resp = safe_get(amtsblatt_url, session=sess, timeout=20, verify=True)
        if not resp or resp.status_code != 200:
            return issues
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for issue links (usually contain dates or issue numbers)
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            text = anchor.get_text(strip=True)
            
            # Check if it looks like an issue link
            if any(term in text.lower() for term in ["ausgabe", "nummer", "jahr", "2023", "2024", "2025"]):
                issue_url = urljoin(amtsblatt_url, href)
                issues.append({
                    "url": issue_url,
                    "title": text,
                    "discovery_source": "AMTSBLATT",
                    "discovery_path": amtsblatt_url,
                })
        
    except Exception as e:
        logger.warning("Failed to list Amtsblatt issues from %s: %s", amtsblatt_url, e)
    
    return issues


def extract_amtsblatt_procedures(issue_url: str, session: Optional[requests.Session] = None) -> List[Dict]:
    """
    Extract procedures from an Amtsblatt issue.
    Only looks for B-Plan and permit announcements.
    """
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    
    procedures = []
    
    try:
        resp = safe_get(issue_url, session=sess, timeout=20, verify=True)
        if not resp or resp.status_code != 200:
            return procedures
        
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()
        text_lower = text.lower()
        
        # Look for procedure-related content
        procedure_keywords = [
            "bebauungsplan", "b-plan", "bauleitplanung",
            "aufstellungsbeschluss", "öffentliche auslegung", "satzungsbeschluss",
            "bauvorbescheid", "baugenehmigung",
            "§ 36", "§36", "gemeindliches einvernehmen",
            "batteriespeicher", "energiespeicher", "speicheranlage",
        ]
        
        # Check if issue contains relevant procedures
        has_relevant_content = any(keyword in text_lower for keyword in procedure_keywords)
        
        if has_relevant_content:
            # Look for PDF links
            for anchor in soup.find_all("a", href=True):
                href = anchor["href"]
                if href.lower().endswith(".pdf"):
                    doc_url = urljoin(issue_url, href)
                    procedures.append({
                        "url": doc_url,
                        "title": anchor.get_text(strip=True) or "Amtsblatt PDF",
                        "type": "document",
                        "discovery_source": "AMTSBLATT",
                        "discovery_path": issue_url,
                    })
            
            # If no PDFs found, treat the issue page itself as a procedure
            if not procedures:
                procedures.append({
                    "url": issue_url,
                    "title": soup.find("title").get_text(strip=True) if soup.find("title") else "Amtsblatt Issue",
                    "type": "issue",
                    "discovery_source": "AMTSBLATT",
                    "discovery_path": issue_url,
                })
        
    except Exception as e:
        logger.warning("Failed to extract procedures from Amtsblatt issue %s: %s", issue_url, e)
    
    return procedures





