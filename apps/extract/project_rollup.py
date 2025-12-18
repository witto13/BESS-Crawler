"""
Best-field rollups: aggregate best values from linked procedures into project entities.
"""
from typing import Dict, List, Optional
from datetime import datetime, date


def compute_best_fields(
    procedures: List[Dict],
    signature: Dict
) -> Dict:
    """
    Compute best fields for a project entity from linked procedures.
    
    Args:
        procedures: List of procedure dicts linked to the project
        signature: Project signature with plan_token, parcel_token, etc.
    
    Returns:
        Dict with best field values
    """
    best = {
        "canonical_project_name": None,
        "site_location_best": None,
        "developer_company_best": None,
        "capacity_mw_best": None,
        "capacity_mwh_best": None,
        "area_hectares_best": None,
        "legal_basis_best": None,
    }
    
    # Canonical project name: prefer plan_token, else best title
    if signature.get("plan_token"):
        best["canonical_project_name"] = f"B-Plan {signature['plan_token']}"
    else:
        # Use longest informative title
        titles = [p.get("title_raw", "") for p in procedures if p.get("title_raw")]
        if titles:
            # Prefer titles with plan-related terms
            plan_titles = [t for t in titles if any(term in t.lower() for term in ["bebauungsplan", "b-plan", "plan"])]
            if plan_titles:
                best["canonical_project_name"] = max(plan_titles, key=len)
            else:
                best["canonical_project_name"] = max(titles, key=len)
    
    # Site location: prefer parcel_token expanded, else longest site_location_raw
    if signature.get("parcel_token"):
        best["site_location_best"] = signature["parcel_token"]
    else:
        locations = [p.get("site_location_raw") for p in procedures if p.get("site_location_raw")]
        if locations:
            best["site_location_best"] = max(locations, key=len)
    
    # Developer: most frequent non-empty
    developers = [p.get("developer_company") for p in procedures if p.get("developer_company")]
    if developers:
        # Count frequency
        from collections import Counter
        dev_counts = Counter(developers)
        best["developer_company_best"] = dev_counts.most_common(1)[0][0]
    
    # Capacities: max non-null
    capacities_mw = [p.get("capacity_mw") for p in procedures if p.get("capacity_mw") is not None]
    if capacities_mw:
        best["capacity_mw_best"] = max(capacities_mw)
    
    capacities_mwh = [p.get("capacity_mwh") for p in procedures if p.get("capacity_mwh") is not None]
    if capacities_mwh:
        best["capacity_mwh_best"] = max(capacities_mwh)
    
    # Area: max non-null
    areas = [p.get("area_hectares") for p in procedures if p.get("area_hectares") is not None]
    if areas:
        best["area_hectares_best"] = max(areas)
    
    # Legal basis: §35 beats §34 beats §36 beats unknown
    legal_bases = [p.get("legal_basis") for p in procedures if p.get("legal_basis")]
    if legal_bases:
        if "§35" in legal_bases:
            best["legal_basis_best"] = "§35"
        elif "§34" in legal_bases:
            best["legal_basis_best"] = "§34"
        elif "§36" in legal_bases:
            best["legal_basis_best"] = "§36"
        else:
            best["legal_basis_best"] = legal_bases[0]
    
    return best


def compute_project_dates(procedures: List[Dict]) -> tuple[Optional[date], Optional[date]]:
    """
    Compute first_seen_date and last_seen_date from procedures.
    """
    dates = []
    for proc in procedures:
        if proc.get("decision_date"):
            dates.append(proc["decision_date"])
        elif proc.get("created_at"):
            if isinstance(proc["created_at"], datetime):
                dates.append(proc["created_at"].date())
            elif isinstance(proc["created_at"], date):
                dates.append(proc["created_at"])
    
    if dates:
        return min(dates), max(dates)
    
    return None, None


def compute_project_confidence(procedures: List[Dict], classifier_results: List[Dict]) -> tuple[float, bool]:
    """
    Compute max_confidence and needs_review from procedures and classifier results.
    """
    max_conf = 0.0
    needs_review = False
    
    for proc, classifier in zip(procedures, classifier_results):
        # Get confidence from classifier
        if classifier and classifier.get("confidence_score"):
            max_conf = max(max_conf, classifier["confidence_score"])
        
        # Check review_recommended
        if classifier and classifier.get("review_recommended"):
            needs_review = True
    
    return max_conf, needs_review






