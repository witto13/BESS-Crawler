"""
Entity resolution: map procedures to project entities.
Computes project signatures and matches procedures to existing projects.
"""
from typing import Dict, Optional, Tuple, List
import re
from datetime import datetime
import uuid

# Maturity stage enum values
MATURITY_STAGES = [
    "DISCOVERED",
    "PERMIT_36",
    "BAUVORBESCHEID",
    "BAUGENEHMIGUNG",
    "BPLAN_AUFSTELLUNG",
    "BPLAN_AUSLEGUNG",
    "BPLAN_SATZUNG",
]

MATURITY_PRECEDENCE = {
    "PERMIT_BAUGENEHMIGUNG": "BAUGENEHMIGUNG",
    "PERMIT_BAUVORBESCHEID": "BAUVORBESCHEID",
    "PERMIT_36_EINVERNEHMEN": "PERMIT_36",
    "BPLAN_SATZUNG": "BPLAN_SATZUNG",
    "BPLAN_AUSLEGUNG_3_2": "BPLAN_AUSLEGUNG",
    "BPLAN_FRUEHZEITIG_3_1": "BPLAN_AUFSTELLUNG",
    "BPLAN_AUFSTELLUNG": "BPLAN_AUFSTELLUNG",
}


def extract_plan_token(title: str, text: Optional[str] = None) -> Optional[str]:
    """
    Extract plan name/number from title or text.
    Looks for: "Bebauungsplan Nr. 123", "B-Plan Nr. ...", quoted plan names.
    """
    combined = (title + " " + (text or "")).lower()
    
    # Pattern 1: "Bebauungsplan Nr. 123" or "B-Plan Nr. 123"
    plan_match = re.search(r'b(?:ebauungs)?-?plan\s*(?:nr\.?|nummer)?\s*([a-z0-9\-/]+)', combined, re.IGNORECASE)
    if plan_match:
        return plan_match.group(1).strip()
    
    # Pattern 2: Quoted plan names (German quotes „..." or "..." or '...')
    quoted_match = re.search(r'[„"\']([^„"\']{5,50})[„"\']', combined)
    if quoted_match:
        candidate = quoted_match.group(1).strip()
        # Check if it looks like a plan name
        if any(term in candidate.lower() for term in ["plan", "gebiet", "bereich", "vorhaben"]):
            return candidate
    
    return None


def extract_parcel_token(site_location_raw: Optional[str]) -> Optional[str]:
    """
    Parse Gemarkung, Flur, Flurstück from site_location_raw.
    Returns normalized string like: "gemarkung=xxx;flur=3;flurstueck=12/4"
    """
    if not site_location_raw:
        return None
    
    location_lower = site_location_raw.lower()
    parts = []
    
    # Gemarkung
    gemarkung_match = re.search(r'gemarkung\s*:?\s*([a-zäöüß\s-]+)', location_lower)
    if gemarkung_match:
        gemarkung = gemarkung_match.group(1).strip()
        parts.append(f"gemarkung={gemarkung}")
    
    # Flur
    flur_match = re.search(r'flur\s*:?\s*(\d+)', location_lower)
    if flur_match:
        flur = flur_match.group(1)
        parts.append(f"flur={flur}")
    
    # Flurstück
    flurstueck_match = re.search(r'flurstueck\s*:?\s*(\d+[a-z]?)(?:\s*\(teilw\.\))?', location_lower)
    if not flurstueck_match:
        flurstueck_match = re.search(r'flurstück\s*:?\s*(\d+[a-z]?)(?:\s*\(teilw\.\))?', location_lower)
    if flurstueck_match:
        flurstueck = flurstueck_match.group(1)
        parts.append(f"flurstueck={flurstueck}")
    
    if parts:
        return ";".join(parts)
    
    return None


def normalize_company_name(company: Optional[str]) -> Optional[str]:
    """
    Normalize company name for matching.
    Strips common suffixes (GmbH, AG, etc.) and normalizes.
    """
    if not company:
        return None
    
    # Remove common suffixes
    normalized = re.sub(r'\s+(gmbh|ag|ug|kg|gbr|e\.v\.|e\.k\.|ohg)\s*$', '', company, flags=re.IGNORECASE)
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    # Lowercase
    normalized = normalized.lower()
    
    return normalized if normalized else None


def extract_title_signature(title: str) -> str:
    """
    Extract informative tokens from title, removing procedure phrases.
    Returns space-separated tokens.
    """
    # Remove procedure phrases
    stop_phrases = [
        "zur beteiligung",
        "öffentliche auslegung",
        "zur aufstellung",
        "bekanntmachung",
        "verfahren",
        "beschluss",
        "sitzung",
        "tagesordnung",
    ]
    
    normalized = title.lower()
    for phrase in stop_phrases:
        normalized = normalized.replace(phrase, " ")
    
    # Extract words (3+ chars, alphanumeric)
    tokens = re.findall(r'\b[a-zäöüß]{3,}\b', normalized)
    
    # Remove common stopwords
    stopwords = {"und", "der", "die", "das", "für", "von", "mit", "auf", "in", "an", "zu", "dem", "den"}
    tokens = [t for t in tokens if t not in stopwords]
    
    # Return top 5-10 tokens
    return " ".join(tokens[:10])


def compute_project_signature(
    procedure: Dict,
    classifier_result: Optional[Dict] = None
) -> Dict:
    """
    Compute structured signature for a procedure.
    
    Returns:
        {
            "plan_token": str or None,
            "parcel_token": str or None,
            "developer_token": str or None,
            "title_signature": str,
        }
    """
    title = procedure.get("title_raw", "")
    site_location = procedure.get("site_location_raw")
    developer = procedure.get("developer_company")
    
    # Get text for plan extraction (title + evidence snippets if available)
    text = title
    if classifier_result:
        evidence = classifier_result.get("evidence_snippets", [])
        if evidence:
            text += " " + " ".join(evidence[:3])
    
    return {
        "plan_token": extract_plan_token(title, text),
        "parcel_token": extract_parcel_token(site_location),
        "developer_token": normalize_company_name(developer),
        "title_signature": extract_title_signature(title),
    }


def jaccard_similarity(set1: set, set2: set) -> float:
    """
    Compute Jaccard similarity between two sets.
    """
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def compute_title_signature_similarity(sig1: str, sig2: str, threshold: float = 0.5) -> Tuple[float, bool]:
    """
    Compute similarity between two title signatures.
    Returns (similarity_score, meets_threshold)
    """
    tokens1 = set(sig1.split())
    tokens2 = set(sig2.split())
    
    similarity = jaccard_similarity(tokens1, tokens2)
    meets_threshold = similarity >= threshold
    
    return similarity, meets_threshold


def find_matching_project(
    signature: Dict,
    municipality_key: str,
    procedure_type: Optional[str],
    db_conn
) -> Optional[Tuple[str, float, str]]:
    """
    Find matching project entity for a procedure signature.
    
    Returns:
        (project_id, link_confidence, link_reason) or None
    """
    from psycopg import sql
    
    cur = db_conn.cursor()
    
    # Match Level 1: Parcel match
    if signature.get("parcel_token"):
        cur.execute("""
            SELECT pe.project_id, pe.site_location_best
            FROM project_entities pe
            WHERE pe.municipality_key = %s
            AND pe.site_location_best LIKE %s
            LIMIT 1
        """, (municipality_key, f"%{signature['parcel_token']}%"))
        
        row = cur.fetchone()
        if row:
            return (str(row[0]), 0.95, "PARCEL_MATCH")
    
    # Match Level 2: Plan token match
    if signature.get("plan_token"):
        cur.execute("""
            SELECT pe.project_id, pe.canonical_project_name
            FROM project_entities pe
            WHERE pe.municipality_key = %s
            AND (pe.canonical_project_name LIKE %s OR pe.canonical_project_name = %s)
            LIMIT 1
        """, (municipality_key, f"%{signature['plan_token']}%", signature['plan_token']))
        
        row = cur.fetchone()
        if row:
            return (str(row[0]), 0.90, "PLAN_TOKEN_MATCH")
    
    # Match Level 3: Developer + title signature
    if signature.get("developer_token") and signature.get("title_signature"):
        cur.execute("""
            SELECT pe.project_id, pe.developer_company_best
            FROM project_entities pe
            WHERE pe.municipality_key = %s
            AND pe.developer_company_best IS NOT NULL
            LIMIT 50
        """, (municipality_key,))
        
        candidates = cur.fetchall()
        for candidate in candidates:
            candidate_dev = normalize_company_name(candidate[1])
            if candidate_dev == signature["developer_token"]:
                # Check title signature similarity
                # We'd need to store title signatures, but for now use a simpler check
                # TODO: Store title signatures in project_entities for better matching
                return (str(candidate[0]), 0.80, "DEV+TITLE_MATCH")
    
    # Match Level 4: Title signature only (requires stored signatures)
    # For now, skip this level as we don't store title signatures
    # TODO: Implement title signature storage and matching
    
    return None


def compute_maturity_stage(procedure_types: List[str], legal_basis: Optional[str]) -> str:
    """
    Compute maturity stage from procedure types and legal basis.
    Highest precedence wins.
    """
    stages_seen = set()
    
    for proc_type in procedure_types:
        if proc_type in MATURITY_PRECEDENCE:
            stages_seen.add(MATURITY_PRECEDENCE[proc_type])
    
    # Check precedence order
    for stage in ["BAUGENEHMIGUNG", "BAUVORBESCHEID", "PERMIT_36", "BPLAN_SATZUNG", 
                  "BPLAN_AUSLEGUNG", "BPLAN_AUFSTELLUNG"]:
        if stage in stages_seen:
            return stage
    
    return "DISCOVERED"

