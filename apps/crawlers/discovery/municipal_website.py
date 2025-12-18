"""
Municipal website crawler - discovers B-Plan and permit signals from official municipal websites.

Uses SPIDER approach:
1. Loads the homepage
2. Dynamically finds links containing keywords: "Bauen", "Planung", "Satzungen", "Bekanntmachung", etc.
3. Follows those links specifically

Falls back to predefined paths if spider approach finds nothing.
"""
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

from .municipality_index import MUNICIPAL_DISCOVERY_PATHS

logger = logging.getLogger(__name__)

# User-Agent for compliance
USER_AGENT = "BESS-Forensic-Crawler/1.0 (Research/Transparency; +https://github.com/bess-crawler)"


def discover_municipal_sections(base_url: str) -> List[str]:
    """
    Discover which municipal sections exist and are accessible.
    Uses SPIDER approach: loads homepage and follows relevant links dynamically.
    Falls back to predefined paths if spider approach finds nothing.
    
    Returns list of accessible URLs.
    """
    base_url = base_url.rstrip("/")
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    
    # SPIDER APPROACH: Load homepage and find relevant links
    accessible_urls = _spider_discover_sections(base_url, session)
    
    # FALLBACK: If spider found nothing, try predefined paths
    if not accessible_urls:
        logger.debug("Spider approach found no sections, falling back to predefined paths")
        accessible_urls = _path_based_discover_sections(base_url, session)
    
    return accessible_urls


def _spider_discover_sections(base_url: str, session: requests.Session) -> List[str]:
    """
    SPIDER APPROACH: Load homepage and dynamically discover relevant sections.
    
    Strategy:
    1. Load the homepage
    2. Look for links containing keywords: "Bauen", "Planung", "Satzungen", "Bekanntmachung", etc.
    3. Follow those links specifically
    4. Return list of discovered section URLs
    """
    accessible_urls = []
    visited_urls = set()
    
    # Keywords to look for in links (German planning/announcement terms)
    relevant_keywords = [
        # Planning terms
        "bauen", "planung", "bebauungsplan", "bauleitplanung", "b-plan",
        "stadtplanung", "flaechennutzungsplan", "fnp",
        # Announcement terms
        "bekanntmachung", "bekanntmachungen", "amtliche", "öffentlich", "oeffentlich",
        "satzung", "satzungen", "verordnung", "verordnungen",
        # Procedure terms
        "verfahren", "beteiligung", "auslegung", "aufstellung",
        # Building/construction terms
        "bauvorbescheid", "baugenehmigung", "bauantrag", "bauvorhaben",
        # Committee/meeting terms
        "bauausschuss", "planungsausschuss", "gemeindevertretung",
    ]
    
    try:
        # Step 1: Load homepage
        logger.debug("Spider: Loading homepage %s", base_url)
        resp = session.get(base_url, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            logger.debug("Spider: Homepage not accessible (status %d)", resp.status_code)
            return accessible_urls
        
        soup = BeautifulSoup(resp.text, "html.parser")
        visited_urls.add(base_url)
        
        # Step 2: Find all links on homepage
        candidate_urls = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            text = anchor.get_text(strip=True)
            
            # Build full URL
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            
            # Only follow links on same domain
            base_domain = urlparse(base_url).netloc
            if parsed.netloc and parsed.netloc != base_domain:
                continue  # External link, skip
            
            # Normalize URL (remove fragments, query params for comparison)
            normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            
            # Check if link text or URL contains relevant keywords
            combined = (text + " " + href + " " + normalized_url).lower()
            if any(keyword in combined for keyword in relevant_keywords):
                if normalized_url not in visited_urls:
                    candidate_urls.append((normalized_url, text))
                    visited_urls.add(normalized_url)
        
        logger.debug("Spider: Found %d candidate links on homepage", len(candidate_urls))
        
        # Step 3: Verify candidate URLs are accessible
        for url, link_text in candidate_urls:
            try:
                resp = session.get(url, timeout=10, allow_redirects=True)
                if resp.status_code == 200:
                    accessible_urls.append(url)
                    logger.debug("Spider: Found accessible section: %s (from link: %s)", url, link_text[:50])
            except Exception as e:
                logger.debug("Spider: Section not accessible %s: %s", url, e)
                continue
        
        logger.info("Spider: Discovered %d accessible sections from homepage", len(accessible_urls))
        
    except Exception as e:
        logger.warning("Spider discovery failed for %s: %s", base_url, e)
    
    return accessible_urls


def _path_based_discover_sections(base_url: str, session: requests.Session) -> List[str]:
    """
    FALLBACK: Path-based discovery using predefined paths.
    Used when spider approach finds nothing.
    """
    accessible_urls = []
    
    for path in MUNICIPAL_DISCOVERY_PATHS:
        url = f"{base_url}{path}"
        try:
            resp = session.get(url, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                accessible_urls.append(url)
                logger.debug("Path-based: Found accessible section: %s", url)
        except Exception as e:
            logger.debug("Path-based: Section not accessible %s: %s", url, e)
            continue
    
    return accessible_urls


def crawl_municipal_section(section_url: str, session: Optional[requests.Session] = None) -> List[Dict]:
    """
    Crawl a specific municipal section for procedures.
    Only looks for B-Plan announcements, public displays, Satzungsbeschlüsse.
    Stops at PDF links or RIS/Amtsblatt links.
    """
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    
    procedures = []
    
    try:
        resp = sess.get(section_url, timeout=20)
        if resp.status_code != 200:
            return procedures
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for procedure links
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            text = anchor.get_text(strip=True)
            
            # Check if it's a procedure-related link
            href_lower = href.lower()
            text_lower = text.lower()
            
            is_procedure = any(
                term in href_lower or term in text_lower
                for term in [
                    "bebauungsplan", "b-plan", "bauleitplanung",
                    "aufstellungsbeschluss", "auslegung", "satzung",
                    "bauvorbescheid", "baugenehmigung", "einvernehmen",
                    "verfahren", "beteiligung"
                ]
            )
            
            if is_procedure:
                full_url = urljoin(section_url, href)
                
                # Stop if it's a PDF or external link (RIS/Amtsblatt)
                if href_lower.endswith((".pdf", ".doc", ".docx")):
                    procedures.append({
                        "url": full_url,
                        "title": text,
                        "type": "document",
                        "discovery_source": "MUNICIPAL_WEBSITE",
                        "discovery_path": section_url,
                    })
                elif any(term in href_lower for term in ["ris", "allris", "sessionnet", "amtsblatt"]):
                    # External link - don't crawl, but note it
                    logger.debug("Found external link to %s: %s", full_url, text)
                else:
                    # Internal procedure page
                    procedures.append({
                        "url": full_url,
                        "title": text,
                        "type": "procedure",
                        "discovery_source": "MUNICIPAL_WEBSITE",
                        "discovery_path": section_url,
                    })
        
    except Exception as e:
        logger.warning("Failed to crawl municipal section %s: %s", section_url, e)
    
    return procedures


def extract_procedure_details(procedure_url: str, session: Optional[requests.Session] = None) -> Dict:
    """
    Extract details from a procedure detail page.
    Looks for documents, dates, and procedure information.
    """
    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    
    details = {
        "url": procedure_url,
        "title": "",
        "documents": [],
        "discovery_source": "MUNICIPAL_WEBSITE",
        "discovery_path": procedure_url,
    }
    
    try:
        resp = sess.get(procedure_url, timeout=20)
        if resp.status_code != 200:
            return details
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Extract title
        title_elem = soup.find("h1") or soup.find("title")
        if title_elem:
            details["title"] = title_elem.get_text(strip=True)
        
        # Extract documents
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if href.lower().endswith((".pdf", ".doc", ".docx")):
                doc_url = urljoin(procedure_url, href)
                details["documents"].append({
                    "url": doc_url,
                    "label": anchor.get_text(strip=True),
                })
        
    except Exception as e:
        logger.warning("Failed to extract details from %s: %s", procedure_url, e)
    
    return details






