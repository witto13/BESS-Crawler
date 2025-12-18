"""
Improved keyword-based BESS scoring with comprehensive rule system.
Erkennt sowohl BESS als auch PV/Solarparks (beide sind relevant für MS/HS).
Uses improved classifier for Brandenburg planning/permitting procedures.
"""
from .classifier_bess import is_candidate, classify_relevance
from .normalize import normalize_text
POSITIVE = {
    # Direct BESS keywords (HIGH PRIORITY)
    "batteriespeicher": 10,
    "bess": 10,
    "batterie-energiespeicher": 10,
    "batterie energiespeicher": 10,
    "batteriespeicheranlage": 10,
    "batterie-speicher": 8,
    "batteriespeicher-system": 8,
    "stromspeicher": 6,
    "energiespeicher": 5,
    "netzdienlicher speicher": 6,
    "netzdienlicher energiespeicher": 6,
    "netzdienliche speicher": 6,
    "container": 3,
    "speichercontainer": 4,
    "batteriecontainer": 5,
    "lithium": 4,
    "lithium-ionen": 4,
    "lithium-ion": 4,
    "lithiumbatterie": 5,
    # Storage infrastructure
    "speicheranlage": 4,
    "speichersystem": 4,
    "energiespeichersystem": 5,
    # PV/Solar keywords (ALSO RELEVANT - für MS/HS)
    "solarpark": 5,  # PV ist relevant für MS/HS
    "photovoltaik": 5,
    "pv-anlage": 5,
    "pv anlage": 5,
    "solaranlage": 4,
    "freiflächenphotovoltaik": 5,
    "freiflächen-pv": 5,
    "solarfeld": 4,
    "solarfarm": 4,
    # Wind (auch relevant)
    "windpark": 4,
    "windenergie": 3,
    "windenergieanlage": 4,
    # Generic energy
    "speicher": 1,  # Generic - needs combination
    "energiepark": 3,
    "energieanlage": 2,
}

NEGATIVE = {
    "wärmespeicher": -5,
    "wasserspeicher": -5,
    "regenrückhaltebecken": -5,
    "regenwasser": -3,
    "abwasser": -3,
}


def score(text: str, title: str = "", use_improved: bool = True) -> int:
    # Use improved classifier if enabled
    if use_improved:
        normalized, _ = normalize_text(text)
        normalized_title, _ = normalize_text(title)
        combined = normalized + " " + normalized_title
        
        # Check if candidate
        if not is_candidate(combined, normalized_title):
            return 0
        
        # Classify
        from datetime import datetime
        result = classify_relevance(combined, normalized_title, date=datetime.now())
        
        if result["is_relevant"]:
            # Convert confidence (0-1) to score (0-100)
            base_score = int(result["confidence_score"] * 50)
            
            # Add bonuses for explicit terms
            if any(term in combined for term in ["batteriespeicher", "energiespeicher", "stromspeicher"]):
                base_score += 20
            if any(term in combined for term in ["umspannwerk", "110 kv", "220 kv", "380 kv"]):
                base_score += 15
            
            return min(100, base_score)
        else:
            return 0
    
    # Fallback to original scoring
    lowered = text.lower()
    total = 0
    
    # Check for direct BESS keywords first (highest priority)
    has_direct_bess = any(
        keyword in lowered 
        for keyword in ["batteriespeicher", "bess", "batterie-energiespeicher", 
                       "batteriespeicheranlage", "batterie-speicher", "batteriespeicher-system"]
    )
    
    # Direct matches
    for token, val in POSITIVE.items():
        if token in lowered:
            total += val
    
    # Negative matches
    for token, val in NEGATIVE.items():
        if token in lowered:
            total -= val
    
    # Solar/Wind sind relevant (auch ohne Speicher, da MS/HS relevant)
    has_solar = any(kw in lowered for kw in ["solarpark", "photovoltaik", "pv-anlage", "pv anlage", "solaranlage", "freiflächenphotovoltaik"])
    has_wind = any(kw in lowered for kw in ["windpark", "windenergie", "windenergieanlage"])
    has_storage = any(kw in lowered for kw in ["speicher", "batterie", "energiespeicher"])
    
    # Bonus für Kombinationen (höhere Relevanz)
    if has_solar and has_storage:
        total += 6  # Solar + storage combo (sehr hoher Bonus)
    elif has_solar:
        # Solar allein ist auch relevant (PV für MS/HS)
        pass  # Bereits durch POSITIVE keywords abgedeckt
    
    if has_wind and has_storage:
        total += 5  # Wind + storage combo
    elif has_wind:
        # Wind allein ist auch relevant
        pass  # Bereits durch POSITIVE keywords abgedeckt
    
    # Strong bonus for energy park + storage
    if "energiepark" in lowered and has_storage:
        total += 5
    
    # Strong bonus for battery + storage combinations
    if "batterie" in lowered and "speicher" in lowered:
        total += 5  # Battery storage combo
    
    # Extra boost for direct BESS mentions
    if has_direct_bess:
        total += 3  # Extra confidence for explicit BESS
    
    return max(0, total)  # Don't go negative

