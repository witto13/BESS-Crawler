"""
Deterministic rule-based classifier for BESS-related procedures.
Implements the improved rule system for Brandenburg planning/permitting.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

from .keywords_bess import (
    PLANNING_TERMS_STRONG,
    PLANNING_STEP_TERMS,
    PERMIT_TERMS_STRONG,
    BESS_TERMS_EXPLICIT,
    BESS_TERMS_CONTAINER_GRID,
    ENERGY_CONTEXT_TERMS,
    ZONING_TERMS,
    NEGATIVE_STORAGE_TERMS,
    NEGATIVE_UNRELATED_TERMS,
    LEGAL_BASIS_TERMS,
    PERMIT_DOC_CONTEXT_TERMS,
)
from .normalize import normalize_text


def is_candidate(text: str, title: str = "") -> bool:
    """
    4.1 Candidate gating (fast prefilter)
    A document becomes a candidate if it contains procedure terms AND BESS/energy terms.
    Excludes documents with strong negative signals.
    """
    normalized_text, _ = normalize_text(text)
    normalized_title, _ = normalize_text(title)
    combined = normalized_text + " " + normalized_title
    
    # Check for strong negative signals FIRST
    has_negative = any(term in combined for term in NEGATIVE_STORAGE_TERMS + NEGATIVE_UNRELATED_TERMS)
    has_bess_explicit = any(term in combined for term in BESS_TERMS_EXPLICIT)
    
    # If negative terms present without explicit BESS, reject early
    if has_negative and not has_bess_explicit:
        return False
    
    # Check for procedure terms
    has_procedure = any(
        term in combined 
        for term in PLANNING_TERMS_STRONG + PLANNING_STEP_TERMS + PERMIT_TERMS_STRONG
    )
    
    if not has_procedure:
        return False
    
    # Check for BESS/energy terms
    has_speicher_energy = (
        "speicher" in combined and 
        any(term in combined for term in ENERGY_CONTEXT_TERMS)
    )
    has_zoning_energy = (
        any(term in combined for term in ZONING_TERMS) and
        any(term in combined for term in ENERGY_CONTEXT_TERMS)
    )
    
    return has_bess_explicit or has_speicher_energy or has_zoning_energy


def classify_relevance(text: str, title: str = "", date: Optional[datetime] = None) -> Dict:
    """
    4.2 Confirmed relevance (high precision)
    Returns classification result with procedure_type, legal_basis, etc.
    """
    normalized_text, original_text = normalize_text(text)
    normalized_title, original_title = normalize_text(title)
    combined = normalized_text + " " + normalized_title
    
    # Also check original (non-normalized) text for negative terms
    original_combined = (original_text + " " + original_title).lower()
    
    result = {
        "is_relevant": False,
        "procedure_type": None,
        "legal_basis": None,
        "project_components": None,
        "confidence_score": 0.0,
        "ambiguity_flag": False,
        "review_recommended": False,
        "evidence_snippets": [],
    }
    
    # Check for negative terms FIRST - if present without explicit BESS, reject early
    # Check both normalized and original text
    has_negative = (
        any(term in combined for term in NEGATIVE_STORAGE_TERMS + NEGATIVE_UNRELATED_TERMS) or
        any(term in original_combined for term in NEGATIVE_STORAGE_TERMS + NEGATIVE_UNRELATED_TERMS)
    )
    
    # Rule R1: Explicit BESS + procedure
    # Strong BESS terms only (not medium terms like "speicheranlage")
    strong_bess_terms = ["batteriespeicher", "batterie-speicher", "energiespeicher", "stromspeicher", "grossspeicher", "großspeicher", "bess"]
    has_bess_explicit = any(term in combined for term in strong_bess_terms)
    
    # Medium terms (ambiguous, need context)
    medium_bess_terms = ["speicheranlage", "speicherpark", "speicherkraftwerk"]
    has_medium_bess = any(term in combined for term in medium_bess_terms)
    
    has_procedure = any(
        term in combined 
        for term in PLANNING_TERMS_STRONG + PLANNING_STEP_TERMS + PERMIT_TERMS_STRONG
    )
    
    # If negative terms present without explicit BESS, reject
    if has_negative and not has_bess_explicit:
        result["is_relevant"] = False
        result["confidence_score"] = 0.0
        return result
    
    # Rule R1: Only strong explicit BESS terms
    if has_bess_explicit and has_procedure and not has_negative:
        result["is_relevant"] = True
    
    # Rule R2: Explicit "Batteriespeicher/Energiespeicher" in title
    if date and date >= datetime(2023, 1, 1):
        if any(term in normalized_title for term in ["batteriespeicher", "energiespeicher"]):
            result["is_relevant"] = True
    
    # Rule R3: Ambiguous "Speicher" but strong grid context
    # Applies to: "speicher" (generic) OR medium terms like "speicheranlage" (without strong BESS terms)
    # Only apply if no negative terms (already checked above) and not already relevant
    if (("speicher" in combined or has_medium_bess) and not result["is_relevant"] and not has_negative):
        grid_terms_count = sum(1 for term in BESS_TERMS_CONTAINER_GRID if term in combined)
        has_procedure_term = any(
            term in combined 
            for term in PLANNING_STEP_TERMS + PERMIT_TERMS_STRONG
        )
        
        if grid_terms_count >= 2 and has_procedure_term:
            result["is_relevant"] = True
            result["ambiguity_flag"] = True  # Set flag here for Rule R3
    
    if not result["is_relevant"]:
        return result
    
    # Tag procedure type
    result["procedure_type"] = tag_procedure_type(combined)
    result["legal_basis"] = tag_legal_basis(combined)
    result["project_components"] = tag_project_components(combined)
    
    # Calculate confidence score
    result["confidence_score"] = calculate_confidence(
        combined, normalized_title, has_bess_explicit, date
    )
    
    # Set flags
    # Check if BESS is explicit (strong terms only, not medium terms like "speicheranlage")
    strong_bess_terms = ["batteriespeicher", "batterie-speicher", "energiespeicher", "stromspeicher", "grossspeicher", "großspeicher", "bess"]
    has_bess_explicit_final = any(term in combined for term in strong_bess_terms)
    
    # Set ambiguity flag if not already set (Rule R3 might have set it)
    # If no explicit BESS terms, it's ambiguous
    if not has_bess_explicit_final:
        result["ambiguity_flag"] = True
    
    if 0.35 <= result["confidence_score"] <= 0.65:
        result["review_recommended"] = True
    
    # Extract evidence snippets
    result["evidence_snippets"] = extract_evidence_snippets(
        original_text, original_title, combined
    )
    
    return result


def tag_procedure_type(text: str) -> str:
    """Tag procedural step type."""
    # Check permit types FIRST (before B-Plan, as they can overlap)
    if "bauvorbescheid" in text or "vorbescheid" in text:
        return "PERMIT_BAUVORBESCHEID"
    elif "baugenehmigung" in text:
        return "PERMIT_BAUGENEHMIGUNG"
    elif "§ 36 baugb" in text or ("gemeindliches einvernehmen" in text and "§ 36" in text):
        return "PERMIT_36_EINVERNEHMEN"
    elif "bauantrag" in text or ("antrag auf" in text and any(p in text for p in PERMIT_TERMS_STRONG)):
        return "PERMIT_OTHER"
    # Expanded privileged project language
    elif "bauvoranfrage" in text or "bauvorantrag" in text:
        return "PERMIT_OTHER"
    elif "kenntnisnahme" in text and ("bauantrag" in text or "vorhaben" in text):
        return "PERMIT_OTHER"
    elif "antrag auf errichtung" in text:
        return "PERMIT_OTHER"
    
    # B-Plan types (check after permits)
    if "aufstellungsbeschluss" in text or "beschluss zur aufstellung" in text or "§ 2 abs. 1 baugb" in text:
        return "BPLAN_AUFSTELLUNG"
    elif "§ 3 abs. 1 baugb" in text or "frühzeitige beteiligung" in text or "fruehzeitige beteiligung" in text:
        return "BPLAN_FRUEHZEITIG_3_1"
    elif "§ 3 abs. 2 baugb" in text or "öffentliche auslegung" in text or "oeffentliche auslegung" in text:
        return "BPLAN_AUSLEGUNG_3_2"
    elif "satzungsbeschluss" in text or "§ 10 baugb" in text or "inkrafttreten" in text:
        return "BPLAN_SATZUNG"
    elif any(term in text for term in PLANNING_TERMS_STRONG):
        return "BPLAN_OTHER"
    
    return "UNKNOWN"


def tag_legal_basis(text: str) -> str:
    """Tag legal basis (§35/§34/§36). Handles broken whitespace in RIS PDFs."""
    # Normalize text to handle broken whitespace (RIS PDFs often split words)
    text_normalized = text.replace("\n", " ").replace("\t", " ").replace("  ", " ")
    
    # Check for §35 patterns (with and without spaces)
    if ("§ 35 baugb" in text_normalized or "§35 baugb" in text_normalized or 
        "§ 35bau gb" in text_normalized or "§35bau gb" in text_normalized or
        "außenbereich" in text_normalized or "aussenbereich" in text_normalized):
        return "§35"
    # Check for §34 patterns
    elif ("§ 34 baugb" in text_normalized or "§34 baugb" in text_normalized or
          "§ 34bau gb" in text_normalized or "§34bau gb" in text_normalized or
          "innenbereich" in text_normalized):
        return "§34"
    # Check for §36 patterns
    elif ("§ 36 baugb" in text_normalized or "§36 baugb" in text_normalized or
          "§ 36bau gb" in text_normalized or "§36bau gb" in text_normalized):
        return "§36"
    return "unknown"


def tag_project_components(text: str) -> str:
    """Tag project components (PV+BESS, WIND+BESS, etc.)."""
    # Handle broken whitespace
    text_normalized = text.replace("\n", " ").replace("\t", " ")
    
    has_pv = any(term in text_normalized for term in ["photovoltaik", "pv", "solarpark"])
    has_wind = any(term in text_normalized for term in ["windenergie", "windpark"])
    has_bess = any(term in text_normalized for term in BESS_TERMS_EXPLICIT) or "speicher" in text_normalized
    
    # Check for containeranlage with grid context
    has_container = "containeranlage" in text_normalized
    has_grid = any(term in text_normalized for term in ["netz", "umspannwerk", "trafostation", "mittelspannung", "hochspannung"])
    if has_container and has_grid:
        has_bess = True  # Treat as BESS
    
    # Check for "anlage zur energiespeicherung"
    if "anlage zur energiespeicherung" in text_normalized:
        has_bess = True
    
    if has_pv and has_bess:
        return "PV+BESS"
    elif has_wind and has_bess:
        return "WIND+BESS"
    elif has_bess:
        return "BESS_ONLY"
    return "OTHER/UNCLEAR"


def calculate_confidence(text: str, title: str, has_bess_explicit: bool, date: Optional[datetime]) -> float:
    """
    5) Confidence scoring (0–1)
    """
    score = 0.0
    
    # BESS explicitness
    if any(term in text for term in ["batteriespeicher", "energiespeicher", "stromspeicher"]):
        score += 0.55
    elif any(term in text for term in ["speicheranlage", "grossspeicher", "großspeicher", "speicherpark"]):
        score += 0.35
    elif "speicher" in text and any(term in text for term in ENERGY_CONTEXT_TERMS):
        score += 0.15
    
    # Procedure strength
    if any(term in text for term in PLANNING_STEP_TERMS):
        score += 0.25
    if "bauvorbescheid" in text or "baugenehmigung" in text:
        score += 0.25
    if "§ 36 baugb" in text or "gemeindliches einvernehmen" in text:
        score += 0.20
    
    # Grid/infrastructure support
    grid_terms = ["umspannwerk", "netzanschluss", "trafostation", "mittelspannung", "hochspannung", "netzverknuepfungspunkt", "netzverknüpfungspunkt"]
    if any(term in text for term in grid_terms):
        score += 0.10
    
    # False-positive penalties (apply BEFORE adding positive points if negative terms present)
    has_negative = any(term in text for term in NEGATIVE_STORAGE_TERMS)
    if has_negative and not has_bess_explicit:
        # Strong penalty - set score very low
        score = 0.0
        return 0.0  # Early return for strong negatives
    
    if "speicher" in text and not any(term in text for term in BESS_TERMS_CONTAINER_GRID):
        score -= 0.25
    if date is None:
        score -= 0.15
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, score))


def extract_evidence_snippets(text: str, title: str, normalized: str, max_snippets: int = 5) -> List[str]:
    """
    Extract evidence snippets around matched triggers.
    """
    snippets = []
    max_len = 250
    
    # Find BESS terms
    for term in BESS_TERMS_EXPLICIT:
        if term in normalized:
            idx = normalized.find(term)
            start = max(0, idx - 100)
            end = min(len(text), idx + len(term) + 100)
            snippet = text[start:end].strip()
            if snippet and len(snippet) <= max_len:
                snippets.append(snippet)
                break
    
    # Find procedure terms
    for term in PLANNING_STEP_TERMS + PERMIT_TERMS_STRONG:
        if term in normalized:
            idx = normalized.find(term)
            start = max(0, idx - 100)
            end = min(len(text), idx + len(term) + 100)
            snippet = text[start:end].strip()
            if snippet and len(snippet) <= max_len:
                snippets.append(snippet)
                break
    
    # Find legal basis
    for term in LEGAL_BASIS_TERMS:
        if term in normalized:
            idx = normalized.find(term)
            start = max(0, idx - 100)
            end = min(len(text), idx + len(term) + 100)
            snippet = text[start:end].strip()
            if snippet and len(snippet) <= max_len:
                snippets.append(snippet)
                break
    
    return snippets[:max_snippets]

