"""
Extract MW/MWh quantities via regex.
"""
import re
from typing import List, Tuple, Optional

MW_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:mw|megawatt|m\.?w\.?)", re.IGNORECASE)
MWH_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:mwh|megawattstunden|m\.?w\.?h\.?)", re.IGNORECASE)
KW_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:kw|kilowatt|k\.?w\.?)", re.IGNORECASE)
KWH_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:kwh|kilowattstunden|k\.?w\.?h\.?)", re.IGNORECASE)


def extract(text: str) -> List[Tuple[str, float]]:
    """
    Extract all power/energy quantities from text.
    Returns list of (unit, value) tuples.
    """
    results: List[Tuple[str, float]] = []
    
    for match in MW_PATTERN.finditer(text):
        try:
            val = float(match.group(1).replace(",", "."))
            results.append(("MW", val))
        except (ValueError, TypeError):
            continue
    
    for match in MWH_PATTERN.finditer(text):
        try:
            val = float(match.group(1).replace(",", "."))
            results.append(("MWh", val))
        except (ValueError, TypeError):
            continue
    
    for match in KW_PATTERN.finditer(text):
        try:
            val = float(match.group(1).replace(",", "."))
            # Convert kW to MW
            results.append(("MW", val / 1000.0))
        except (ValueError, TypeError):
            continue
    
    for match in KWH_PATTERN.finditer(text):
        try:
            val = float(match.group(1).replace(",", "."))
            # Convert kWh to MWh
            results.append(("MWh", val / 1000.0))
        except (ValueError, TypeError):
            continue
    
    return results


def find_capacity_mw(text: str) -> Optional[float]:
    """
    Find the largest MW value (likely the project capacity).
    """
    quantities = extract(text)
    mw_values = [val for unit, val in quantities if unit == "MW"]
    return max(mw_values) if mw_values else None


def find_capacity_mwh(text: str) -> Optional[float]:
    """
    Find the largest MWh value (likely the storage capacity).
    """
    quantities = extract(text)
    mwh_values = [val for unit, val in quantities if unit == "MWh"]
    return max(mwh_values) if mwh_values else None

