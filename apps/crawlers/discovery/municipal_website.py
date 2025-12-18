"""
Municipal website crawler - discovers B-Plan and permit signals from official municipal websites.
Only crawls specific sections defined in discovery paths.
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
    Returns list of accessible URLs.
    """
    accessible_urls = []
    base_url = base_url.rstrip("/")
    
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    
    for path in MUNICIPAL_DISCOVERY_PATHS:
        url = f"{base_url}{path}"
        try:
            resp = session.get(url, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                accessible_urls.append(url)
                logger.debug("Found accessible section: %s", url)
        except Exception as e:
            logger.debug("Section not accessible %s: %s", url, e)
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






