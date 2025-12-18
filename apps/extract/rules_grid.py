"""
Grid/Mittel-/Hochspannung scoring.
"""
TOKENS = {
    # High voltage
    "umspannwerk": 5,
    "110 kv": 5,
    "220 kv": 5,
    "380 kv": 5,
    "400 kv": 5,
    "hochspannung": 4,
    "hs": 3,  # Abbreviation
    # Medium voltage
    "mittelspannung": 3,
    "ms": 2,  # Abbreviation
    "20 kv": 3,
    "30 kv": 3,
    "10 kv": 2,
    # Grid infrastructure
    "schaltanlage": 2,
    "netzverknüpfungspunkt": 2,
    "netzanschluss": 2,
    "netzanschlusspunkt": 2,
    "trafostation": 1,
    "trafo": 1,
    "einspeisepunkt": 1,
    "einspeisung": 1,
    "netz": 1,  # Generic grid reference
    "stromnetz": 1,
    "energienetz": 1,
}


def score(text: str) -> int:
    lowered = text.lower()
    total = 0
    
    # Direct matches
    for token, val in TOKENS.items():
        if token in lowered:
            total += val
    
    # Bonus for combinations (higher confidence)
    if ("umspannwerk" in lowered or "schaltanlage" in lowered) and ("110" in lowered or "220" in lowered or "380" in lowered):
        total += 2  # Substation + voltage level
    if "netzanschluss" in lowered and ("solar" in lowered or "pv" in lowered or "wind" in lowered):
        total += 2  # Grid connection + renewable
    if "einspeisung" in lowered and ("solar" in lowered or "pv" in lowered or "wind" in lowered):
        total += 2  # Feed-in + renewable
    
    # Reduce score for generic "netz" if no other indicators
    if total == 1 and "netz" in lowered:
        # Check if there are other grid-related terms
        has_other = any(term in lowered for term in ["anschluss", "einspeisung", "trafo", "spannung", "kv"])
        if not has_other:
            total = 0  # Too generic, probably not relevant
    
    return max(0, total)

