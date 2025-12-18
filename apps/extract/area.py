"""
Extract area/hectare information from text.
"""
import re
from typing import List, Tuple, Optional

# Area patterns
HECTARE_PATTERNS = [
    re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:ha|hektar|hektare)", re.IGNORECASE),
    re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:qm|m²|quadratmeter)", re.IGNORECASE),
    re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:km²|quadratkilometer)", re.IGNORECASE),
]

# Conversion factors to hectares
CONVERSIONS = {
    "qm": 0.0001,
    "m²": 0.0001,
    "quadratmeter": 0.0001,
    "km²": 100,
    "quadratkilometer": 100,
    "ha": 1,
    "hektar": 1,
    "hektare": 1,
}


def extract_area(text: str) -> List[Tuple[float, str]]:
    """
    Extract area values from text.
    Returns list of (area_in_hectares, unit) tuples.
    """
    results = []
    
    for pattern in HECTARE_PATTERNS:
        for match in pattern.finditer(text):
            try:
                value_str = match.group(1).replace(",", ".")
                value = float(value_str)
                
                # Determine unit from match
                unit = "ha"  # default
                for u in CONVERSIONS.keys():
                    if u.lower() in match.group(0).lower():
                        unit = u
                        break
                
                # Convert to hectares
                hectares = value * CONVERSIONS.get(unit, 1)
                results.append((hectares, unit))
            except (ValueError, TypeError):
                continue
    
    return results


def find_largest_area(text: str) -> Optional[float]:
    """
    Find the largest area mentioned (likely the project area).
    Returns area in hectares.
    """
    areas = extract_area(text)
    if not areas:
        return None
    
    # Return largest area
    return max(area[0] for area in areas)







