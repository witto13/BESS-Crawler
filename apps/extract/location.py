"""
Extract location/parcel information from text.
"""
import re
from typing import Optional, List, Tuple

from .keywords_bess import PARCEL_TERMS
from .normalize import normalize_text


def extract_location(text: str) -> Optional[str]:
    """
    Extract location information (Gemarkung, Flur, Flurstück, address).
    Returns raw location string.
    """
    normalized, original = normalize_text(text)
    
    location_parts = []
    
    # Look for parcel information patterns
    # Gemarkung
    gemarkung_match = re.search(r"gemarkung\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß\s-]+)", normalized, re.IGNORECASE)
    if gemarkung_match:
        location_parts.append(f"Gemarkung: {gemarkung_match.group(1).strip()}")
    
    # Flur
    flur_match = re.search(r"flur\s+(\d+)", normalized, re.IGNORECASE)
    if flur_match:
        location_parts.append(f"Flur: {flur_match.group(1)}")
    
    # Flurstück
    flurstueck_match = re.search(r"flurstueck\s+(\d+[a-z]?)(?:\s*\(teilw\.\))?", normalized, re.IGNORECASE)
    if not flurstueck_match:
        flurstueck_match = re.search(r"flurstück\s+(\d+[a-z]?)(?:\s*\(teilw\.\))?", normalized, re.IGNORECASE)
    if flurstueck_match:
        location_parts.append(f"Flurstück: {flurstueck_match.group(1)}")
    
    # Address/Street
    strasse_match = re.search(r"(?:strasse|straße|str\.)\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß\s-]+)", normalized, re.IGNORECASE)
    if strasse_match:
        location_parts.append(f"Straße: {strasse_match.group(1).strip()}")
    
    # Coordinates (basic pattern)
    coord_match = re.search(r"(\d+[.,]\d+)\s*[°]?\s*[NSEW]?\s*[,/]\s*(\d+[.,]\d+)\s*[°]?\s*[NSEW]?", normalized)
    if coord_match:
        location_parts.append(f"Koordinaten: {coord_match.group(1)}, {coord_match.group(2)}")
    
    if location_parts:
        return "; ".join(location_parts)
    
    return None






