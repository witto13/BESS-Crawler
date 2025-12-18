"""
Site-driven discovery: find RIS/Amtsblatt links from official municipal websites.
This replaces URL guessing with actual link discovery from real websites.
"""
from typing import List, Dict, Optional, Set
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import re

from apps.net.http_client import safe_get

logger = logging.getLogger(__name__)

USER_AGENT = "BESS-Forensic-Crawler/1.0 (Research/Transparency; +https://github.com/bess-crawler)"

# RIS link patterns (domains/paths that indicate RIS systems)
RIS_DOMAIN_PATTERNS = [
    r'allris',
    r'sessionnet',
    r'ratsinfo',
    r'ris\.',
    r'\.ris\.',
]

RIS_PATH_PATTERNS = [
    r'/ris',
    r'/ratsinfo',
    r'/sessionnet',
    r'/si0100',
    r'/to0100',
    r'/vo0200',
    r'/bi/',
    r'/gremien',
    r'/sitzung',
    r'/tagesordnung',
]

# Amtsblatt/Bekanntmachung link patterns
AMTSBLATT_PATH_PATTERNS = [
    r'/amtsblatt',
    r'/amtliche-bekanntmach',
    r'/bekanntmach',
    r'/veroeffentlich',
    r'/auslegung',
    r'/bauleitplanung',
    r'/beteiligung',
    r'/oeffentliche-auslegung',
    r'/öffentliche-auslegung',
]

# Pages to check (in order of priority)
DISCOVERY_PAGES = [
    "",  # Homepage
    "/sitemap.xml",
    "/impressum",
    "/kontakt",
    "/startseite",
    "/index",
]


def normalize_url(url: str, base_url: str) -> str:
    """Normalize a URL to absolute form."""
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    return urljoin(base_url, url)


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs are on the same domain."""
    try:
        domain1 = urlparse(url1).netloc.lower()
        domain2 = urlparse(url2).netloc.lower()
        # Remove port if present
        if ':' in domain1:
            domain1 = domain1.split(':')[0]
        if ':' in domain2:
            domain2 = domain2.split(':')[0]
        return domain1 == domain2
    except Exception:
        return False


def matches_pattern(text: str, patterns: List[str]) -> bool:
    """Check if text matches any of the regex patterns."""
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False


def discover_links_from_official_site(
    official_url: str,
    max_pages: int = 20,
    max_depth: int = 2
) -> Dict[str, List[str]]:
    """
    Discover RIS/Amtsblatt links from an official municipal website.
    
    Args:
        official_url: Base URL of the official municipal website
        max_pages: Maximum number of pages to fetch
        max_depth: Maximum depth to crawl (0 = homepage only, 1 = homepage + linked pages)
    
    Returns:
        Dict with keys: 'ris_urls', 'amtsblatt_urls', 'bekanntmachung_urls'
        Each contains a list of discovered URLs (ranked, best guess first)
    """
    if not official_url or not (official_url.startswith("http://") or official_url.startswith("https://")):
        logger.warning("Invalid official_url: %s", official_url)
        return {
            "ris_urls": [],
            "amtsblatt_urls": [],
            "bekanntmachung_urls": [],
        }
    
    base_url = official_url.rstrip("/")
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    
    ris_urls: Set[str] = set()
    amtsblatt_urls: Set[str] = set()
    bekanntmachung_urls: Set[str] = set()
    
    pages_fetched = 0
    pages_to_visit = []
    visited_urls: Set[str] = set()
    
    # Start with discovery pages
    for page_path in DISCOVERY_PAGES:
        if pages_fetched >= max_pages:
            break
        url = base_url + page_path if page_path else base_url
        if url not in visited_urls:
            pages_to_visit.append((url, 0))  # (url, depth)
    
    # Crawl pages
    while pages_to_visit and pages_fetched < max_pages:
        current_url, depth = pages_to_visit.pop(0)
        
        if current_url in visited_urls:
            continue
        
        if depth > max_depth:
            continue
        
        visited_urls.add(current_url)
        pages_fetched += 1
        
        try:
            resp = safe_get(current_url, session=session, timeout=10, allow_redirects=True)
            if not resp or resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Extract all links
            for anchor in soup.find_all("a", href=True):
                href = anchor.get("href", "")
                link_text = anchor.get_text(strip=True)
                
                # Normalize URL
                full_url = normalize_url(href, current_url)
                
                if not full_url or not full_url.startswith(("http://", "https://")):
                    continue
                
                # Check if it's a RIS link
                url_lower = full_url.lower()
                text_lower = link_text.lower()
                
                is_ris = (
                    matches_pattern(url_lower, RIS_DOMAIN_PATTERNS) or
                    matches_pattern(url_lower, RIS_PATH_PATTERNS) or
                    matches_pattern(text_lower, ["ris", "ratsinfo", "sessionnet", "allris", "sitzung", "gremium"])
                )
                
                if is_ris and is_same_domain(full_url, base_url) or not is_same_domain(full_url, base_url):
                    # RIS can be on different domain (common pattern)
                    ris_urls.add(full_url)
                    logger.debug("Found RIS link: %s (from %s)", full_url, current_url)
                
                # Check if it's an Amtsblatt link
                is_amtsblatt = (
                    matches_pattern(url_lower, AMTSBLATT_PATH_PATTERNS) or
                    matches_pattern(text_lower, ["amtsblatt", "bekanntmachung", "amtliche bekanntmachung"])
                )
                
                if is_amtsblatt:
                    amtsblatt_urls.add(full_url)
                    logger.debug("Found Amtsblatt link: %s (from %s)", full_url, current_url)
                
                # Check if it's a Bekanntmachung link (broader category)
                is_bekanntmachung = (
                    matches_pattern(url_lower, ["bekanntmach", "veroeffentlich", "auslegung"]) or
                    matches_pattern(text_lower, ["bekanntmachung", "veröffentlichung", "öffentliche auslegung"])
                )
                
                if is_bekanntmachung and full_url not in amtsblatt_urls:
                    bekanntmachung_urls.add(full_url)
                    logger.debug("Found Bekanntmachung link: %s (from %s)", full_url, current_url)
                
                # If depth allows, add internal links to visit queue
                if depth < max_depth and is_same_domain(full_url, base_url):
                    if full_url not in visited_urls:
                        # Only add if it looks like a discovery-relevant page
                        if any(term in url_lower for term in ["impressum", "kontakt", "sitemap", "index", "startseite"]):
                            pages_to_visit.append((full_url, depth + 1))
        
        except Exception as e:
            logger.debug("Failed to fetch %s: %s", current_url, e)
            continue
    
    # Rank URLs (best guess first)
    # Prioritize URLs with stronger signals
    def rank_ris_url(url: str) -> int:
        url_lower = url.lower()
        score = 0
        if "allris" in url_lower or "sessionnet" in url_lower:
            score += 10
        if "si0100" in url_lower or "ris" in url_lower:
            score += 5
        return score
    
    def rank_amtsblatt_url(url: str) -> int:
        url_lower = url.lower()
        score = 0
        if "amtsblatt" in url_lower:
            score += 10
        if "bekanntmachung" in url_lower:
            score += 5
        return score
    
    ranked_ris = sorted(list(ris_urls), key=rank_ris_url, reverse=True)
    ranked_amtsblatt = sorted(list(amtsblatt_urls), key=rank_amtsblatt_url, reverse=True)
    ranked_bekanntmachung = sorted(list(bekanntmachung_urls), key=rank_amtsblatt_url, reverse=True)
    
    logger.info(
        "Site discovery for %s: found %d RIS, %d Amtsblatt, %d Bekanntmachung URLs (fetched %d pages)",
        base_url, len(ranked_ris), len(ranked_amtsblatt), len(ranked_bekanntmachung), pages_fetched
    )
    
    return {
        "ris_urls": ranked_ris,
        "amtsblatt_urls": ranked_amtsblatt,
        "bekanntmachung_urls": ranked_bekanntmachung,
    }


