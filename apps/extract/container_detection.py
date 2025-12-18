"""
Container detection: identify and reject container-like entries (Amtsblatt issues, generic PDFs).
"""
from typing import Dict, Optional
import re


def is_container(title_norm: str, url: str, discovery_source: Optional[str] = None) -> bool:
    """
    Returns True if title or URL indicates a "container issue" rather than a procedure item.
    
    Patterns include:
    - amtsblatt, sonderamtsblatt, bekanntmachungsblatt
    - "ausgabe", "nr." without any procedure terms
    """
    combined = (title_norm + " " + url.lower()).lower()
    
    # Container keywords
    container_keywords = [
        "amtsblatt",
        "sonderamtsblatt",
        "bekanntmachungsblatt",
        "bekanntmachung",
        "veröffentlichung",
        "ausgabe",
        "nummer",
        "nr.",
        "jahrgang",
    ]
    
    # Procedure keywords (if present, it's likely a real procedure)
    procedure_keywords = [
        "bebauungsplan",
        "b-plan",
        "bauleitplanung",
        "aufstellungsbeschluss",
        "satzungsbeschluss",
        "öffentliche auslegung",
        "bauvorbescheid",
        "baugenehmigung",
        "einvernehmen",
        "§ 35",
        "§ 34",
        "§ 36",
        "batteriespeicher",
        "energiespeicher",
        "speicheranlage",
    ]
    
    # Check for container keywords
    has_container_keyword = any(keyword in combined for keyword in container_keywords)
    
    # Check for procedure keywords
    has_procedure_keyword = any(keyword in combined for keyword in procedure_keywords)
    
    # If it has container keywords but no procedure keywords, it's likely a container
    if has_container_keyword and not has_procedure_keyword:
        # Exception: if it's just "ausgabe" or "nr." with a number, might be a container
        if re.search(r'\b(ausgabe|nummer|nr\.)\s*\d+', combined) and not has_procedure_keyword:
            return True
        # If it's clearly an Amtsblatt issue
        if "amtsblatt" in combined and not has_procedure_keyword:
            return True
    
    return False


def has_required_procedure_signal(classifier_result: Dict) -> bool:
    """
    Returns True if procedure_type is not null AND at least one evidence snippet contains the trigger.
    """
    if not classifier_result:
        return False
    
    # Must have a procedure type
    procedure_type = classifier_result.get("procedure_type")
    if not procedure_type:
        return False
    
    # Must have evidence snippets
    evidence_snippets = classifier_result.get("evidence_snippets", [])
    if not evidence_snippets:
        # If no evidence snippets but procedure_type exists, still consider it valid
        # (might be from title-only classification)
        return True
    
    # At least one evidence snippet should contain procedure-related terms
    procedure_terms = [
        "bebauungsplan", "b-plan", "bauleitplanung",
        "aufstellungsbeschluss", "satzungsbeschluss",
        "öffentliche auslegung", "auslegung",
        "bauvorbescheid", "baugenehmigung",
        "einvernehmen", "§ 35", "§ 34", "§ 36",
    ]
    
    for snippet in evidence_snippets:
        snippet_lower = snippet.lower() if isinstance(snippet, str) else ""
        if any(term in snippet_lower for term in procedure_terms):
            return True
    
    return True


def is_valid_procedure(
    title_norm: str,
    url: str,
    discovery_source: Optional[str],
    classifier_result: Optional[Dict],
    confidence_score: float = 0.0,
    extracted_text: Optional[str] = None
) -> tuple[bool, str]:
    """
    Determines if a procedure should be persisted.
    RELAXED: Allows more items through, especially from RIS.
    
    Returns:
        (is_valid, skip_reason)
        skip_reason is one of: None, "SKIP_CONTAINER", "SKIP_NO_PROCEDURE_SIGNAL", "SKIP_LOW_CONFIDENCE_NO_SIGNAL"
    """
    combined_text = (title_norm + " " + (extracted_text or "")).lower()
    
    # Check if it's a container - only skip if NO procedure signal in title OR extracted text
    if is_container(title_norm, url, discovery_source):
        # Check for procedure signals in title or extracted text
        procedure_signals = [
            "bebauungsplan", "b-plan", "bauleitplanung",
            "aufstellungsbeschluss", "satzungsbeschluss",
            "öffentliche auslegung", "auslegung",
            "bauvorbescheid", "baugenehmigung",
            "einvernehmen", "§ 35", "§ 34", "§ 36",
            "bauantrag", "bauvoranfrage", "stellungnahme",
        ]
        has_signal_in_text = any(term in combined_text for term in procedure_signals)
        
        if has_signal_in_text or (classifier_result and has_required_procedure_signal(classifier_result)):
            return True, None  # Container but has procedure content
        return False, "SKIP_CONTAINER"
    
    # RELAXED: Allow if classifier says is_candidate AND has BESS signal
    if classifier_result:
        is_candidate = classifier_result.get("is_candidate", False)
        is_relevant = classifier_result.get("is_relevant", False)
        
        # Check for BESS signals (explicit or ambiguous-with-grid)
        bess_signals = [
            "batteriespeicher", "energiespeicher", "stromspeicher",
            "speicheranlage", "speicherpark", "containeranlage",
            "anlage zur energiespeicherung",
        ]
        grid_signals = [
            "umspannwerk", "netzanschluss", "trafostation",
            "mittelspannung", "hochspannung", "110 kv", "220 kv",
        ]
        has_bess = any(term in combined_text for term in bess_signals)
        has_grid = any(term in combined_text for term in grid_signals)
        
        # Rule A: is_candidate AND has BESS signal
        if is_candidate and (has_bess or (has_grid and "speicher" in combined_text)):
            return True, None
        
        # Rule B: RIS with privileged project language
        if discovery_source == "RIS" or discovery_source == "ris":
            privileged_terms = [
                "einvernehmen", "stellungnahme", "bauantrag",
                "bauvoranfrage", "vorhaben", "kenntnisnahme",
                "antrag auf errichtung",
            ]
            has_privileged_term = any(term in combined_text for term in privileged_terms)
            
            if has_privileged_term:
                # Even if procedure_type is null, allow it (will be set to UNKNOWN)
                return True, None
    
    # Check for procedure signal (original logic)
    if classifier_result and has_required_procedure_signal(classifier_result):
        return True, None
    
    # If we get here and it's RIS with privileged terms, still allow
    if discovery_source in ["RIS", "ris"]:
        privileged_terms = ["einvernehmen", "stellungnahme", "bauantrag", "bauvoranfrage"]
        if any(term in combined_text for term in privileged_terms):
            return True, None
    
    # Default: require procedure signal
    if not classifier_result or not has_required_procedure_signal(classifier_result):
        return False, "SKIP_NO_PROCEDURE_SIGNAL"
    
    return True, None

