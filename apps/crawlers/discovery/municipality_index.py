"""
Municipality index with official website URLs and discovery paths.
Canonical list of all Brandenburg municipalities, cities, and Ämter.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Municipality:
    """Municipality entry with discovery information."""
    name: str
    municipality_key: str  # AGS/ARS
    type: str  # Stadt / Gemeinde / Amt
    landkreis: str
    official_website: Optional[str] = None
    amtsblatt_url: Optional[str] = None
    ris_url: Optional[str] = None
    ris_type: Optional[str] = None  # ALLRIS, SessionNet, etc.


# Discovery paths for municipal websites
MUNICIPAL_DISCOVERY_PATHS = [
    "/bekanntmachungen",
    "/amtliche-bekanntmachungen",
    "/oeffentliche-bekanntmachungen",
    "/öffentliche-bekanntmachungen",
    "/aktuelles/bekanntmachungen",
    "/bauleitplanung",
    "/stadtplanung",
    "/bebauungsplaene",
    "/bebauungspläne",
    "/bauleitplaene",
    "/bauleitpläne",
    "/planung-und-bauen",
    "/bauen-und-wohnen",
    "/b-plan",
    "/bebauungsplan",
    "/verfahren",
    "/beteiligung",
]

# RIS discovery patterns
RIS_URL_PATTERNS = [
    # SessionNet
    "{base}/sessionnet",
    "{base}/ris",
    "https://{municipality}.sessionnet.de",
    "https://ris.{municipality}.de",
    # ALLRIS
    "https://{municipality}.allris.de",
    "https://allris.{municipality}.de",
    # Generic RIS
    "{base}/ratsinformationssystem",
    "{base}/ris",
    "{base}/si0100.asp",  # Common ALLRIS entry point
    "{base}/si0100.php",
]

# RIS committee paths
RIS_COMMITTEE_PATHS = [
    "/si0100.asp",  # ALLRIS main
    "/si0100.php",
    "/index.php",
    "/sitzungen",
    "/gremien",
    "/tagesordnung",
    "/beschlussvorlagen",
    "/niederschriften",
    "/protokolle",
]

# RIS committee names to look for
RIS_COMMITTEE_NAMES = [
    "bauausschuss",
    "hauptausschuss",
    "gemeindevertretung",
    "stadtverordnetenversammlung",
    "ortsbeirat",
    "bau- und planungsausschuss",
    "planungsausschuss",
]

# Amtsblatt discovery patterns
AMTSBLATT_PATTERNS = [
    "/amtsblatt",
    "/amtliches-mitteilungsblatt",
    "/bekanntmachungen",
    "/amtliche-bekanntmachungen",
    "/veröffentlichungen",
    "/veroeffentlichungen",
]


def discover_municipal_paths(base_url: str) -> List[str]:
    """
    Discover municipal website paths for B-Plan and announcements.
    Returns list of URLs to crawl.
    """
    urls = []
    base_url = base_url.rstrip("/")
    
    for path in MUNICIPAL_DISCOVERY_PATHS:
        url = f"{base_url}{path}"
        urls.append(url)
    
    return urls


def _sanitize_name_for_url(name: str) -> str:
    """Sanitize municipality name for URL generation."""
    if not name:
        return ""
    # Remove parentheses and their contents
    import re
    sanitized = re.sub(r'\([^)]*\)', '', name)
    # Convert to lowercase and remove special chars
    sanitized = sanitized.lower().replace(" ", "").replace("(", "").replace(")", "")
    sanitized = sanitized.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    # Remove any remaining non-alphanumeric except dots and dashes
    sanitized = re.sub(r'[^a-z0-9\-.]', '', sanitized)
    return sanitized


def discover_ris_urls(municipality_name: str, base_url: Optional[str] = None) -> List[str]:
    """
    Discover RIS URLs for a municipality.
    Returns list of potential RIS URLs to try.
    """
    urls = []
    
    if municipality_name:
        muni_lower = _sanitize_name_for_url(municipality_name)
        if muni_lower:
            # Try SessionNet patterns
            urls.append(f"https://{muni_lower}.sessionnet.de")
            urls.append(f"https://ris.{muni_lower}.de")
            
            # Try ALLRIS patterns
            urls.append(f"https://{muni_lower}.allris.de")
            urls.append(f"https://allris.{muni_lower}.de")
    
    # If base_url provided, try RIS paths
    if base_url and (base_url.startswith("http://") or base_url.startswith("https://")):
        base_url = base_url.rstrip("/")
        muni_lower = _sanitize_name_for_url(municipality_name) if municipality_name else ""
        for pattern in RIS_URL_PATTERNS:
            try:
                url = pattern.format(base=base_url, municipality=muni_lower)
                urls.append(url)
            except (KeyError, ValueError):
                # Skip patterns that don't match format
                continue
    
    return urls


def discover_amtsblatt_urls(municipality_name: str, base_url: Optional[str] = None) -> List[str]:
    """
    Discover Amtsblatt URLs for a municipality.
    Returns list of potential Amtsblatt URLs to try.
    """
    urls = []
    
    # If base_url provided, try Amtsblatt paths
    if base_url and (base_url.startswith("http://") or base_url.startswith("https://")):
        base_url = base_url.rstrip("/")
        for pattern in AMTSBLATT_PATTERNS:
            url = f"{base_url}{pattern}"
            urls.append(url)
    
    # Common Amtsblatt patterns using municipality name
    if municipality_name:
        # Use dash-separated format for Amtsblatt URLs
        muni_sanitized = municipality_name.lower()
        # Remove parentheses
        import re
        muni_sanitized = re.sub(r'\([^)]*\)', '', muni_sanitized)
        # Replace spaces and special chars with dashes
        muni_sanitized = re.sub(r'[\s_]+', '-', muni_sanitized)
        muni_sanitized = re.sub(r'-+', '-', muni_sanitized).strip('-')
        
        if muni_sanitized:
            urls.append(f"https://{muni_sanitized}.de/amtsblatt")
            urls.append(f"https://www.{muni_sanitized}.de/amtsblatt")
    
    return urls





