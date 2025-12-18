"""
Prefilter scoring: fast keyword check without PDF downloads.
Returns prefilter_score in [0,1] based on title, URL, and optional HTML snippet.
"""
from typing import Optional
import re


def prefilter_score(
    title: str,
    url: str = "",
    html_snippet: Optional[str] = None
) -> float:
    """
    Compute prefilter_score in [0,1] using fast keyword checks.
    
    Rules:
    - +0.6 if title has strong BESS term
    - +0.3 if title has procedure signal
    - +0.2 if URL contains procedure-related terms
    - -0.7 if container-like title AND no procedure signal
    
    Returns:
        Score clamped to [0,1]
    """
    score = 0.0
    title_lower = title.lower()
    url_lower = url.lower()
    combined = title_lower + " " + url_lower
    
    if html_snippet:
        combined += " " + html_snippet.lower()
    
    # Strong BESS terms (+0.6)
    strong_bess_terms = [
        "batteriespeicher",
        "batterie-speicher",
        "energiespeicher",
        "stromspeicher",
        "grossspeicher",
        "großspeicher",
    ]
    if any(term in title_lower for term in strong_bess_terms):
        score += 0.6
    
    # TEMPORARY: Solar/Photovoltaik test (+0.4) - to verify pipeline works
    # Remove this after confirming pipeline is functional
    solar_terms = ["photovoltaik", "pv", "solarpark", "solaranlage", "solar"]
    if any(term in title_lower for term in solar_terms):
        score += 0.4
    
    # Procedure signals (+0.3)
    procedure_terms = [
        "aufstellungsbeschluss",
        "öffentliche auslegung",
        "oeffentliche auslegung",
        "satzungsbeschluss",
        "bauvorbescheid",
        "baugenehmigung",
        "§ 36",
        "§36",
        "einvernehmen",
    ]
    has_procedure_signal = any(term in title_lower for term in procedure_terms)
    if has_procedure_signal:
        score += 0.3
    
    # URL procedure terms (+0.2)
    url_procedure_terms = [
        "bauleitplanung",
        "bebauungsplan",
        "amtsblatt",
        "ris",
        "sessionnet",
    ]
    if any(term in url_lower for term in url_procedure_terms):
        score += 0.2
    
    # Container penalty (-0.7 if container AND no procedure signal)
    container_terms = [
        "amtsblatt",
        "sonderamtsblatt",
        "bekanntmachungsblatt",
        "ausgabe",
        "nummer",
        "nr.",
    ]
    is_container = any(term in title_lower for term in container_terms)
    if is_container and not has_procedure_signal:
        score -= 0.7
    
    # Clamp to [0,1]
    return max(0.0, min(1.0, score))


def should_extract(prefilter_score: float, mode: str = "fast", discovery_source: Optional[str] = None) -> bool:
    """
    Determine if candidate should be extracted based on prefilter_score, mode, and source.
    Source-aware thresholds: RIS gets lower threshold (BESS terms often in attachments).
    
    Args:
        prefilter_score: Score from prefilter_score()
        mode: "fast" (threshold 0.6) or "deep" (threshold 0.3)
        discovery_source: "RIS", "AMTSBLATT", "MUNICIPAL_WEBSITE"
    
    Returns:
        True if should extract
    """
    # Source-aware thresholds
    if discovery_source in ["RIS", "ris"]:
        # RIS: lower threshold because BESS terms often only in attachments
        if mode == "fast":
            return prefilter_score >= 0.35
        elif mode == "deep":
            return prefilter_score >= 0.2
    elif discovery_source in ["AMTSBLATT", "amtsblatt"]:
        # Amtsblatt: medium threshold (will extract TOC/first pages)
        if mode == "fast":
            return prefilter_score >= 0.5
        elif mode == "deep":
            return prefilter_score >= 0.3
    else:
        # Municipal websites: stricter threshold to avoid noise
        if mode == "fast":
            return prefilter_score >= 0.6
        elif mode == "deep":
            return prefilter_score >= 0.5
    
    # Default fallback
    if mode == "fast":
        return prefilter_score >= 0.6
    elif mode == "deep":
        return prefilter_score >= 0.3
    else:
        return prefilter_score >= 0.6

