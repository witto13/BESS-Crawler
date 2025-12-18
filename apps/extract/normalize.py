"""
Text normalization for German keyword matching.
"""
import re
import unicodedata


def normalize_umlauts(text: str) -> tuple[str, str]:
    """
    Normalize umlauts: ä->ae, ö->oe, ü->ue, ß->ss
    Returns (normalized, original) tuple.
    """
    normalized = text
    # Replace umlauts
    normalized = normalized.replace("ä", "ae")
    normalized = normalized.replace("ö", "oe")
    normalized = normalized.replace("ü", "ue")
    normalized = normalized.replace("Ä", "Ae")
    normalized = normalized.replace("Ö", "Oe")
    normalized = normalized.replace("Ü", "Ue")
    normalized = normalized.replace("ß", "ss")
    normalized = normalized.replace("ẞ", "Ss")
    
    return normalized, text


def normalize_text(text: str) -> tuple[str, str]:
    """
    Normalize text for matching:
    - lowercase
    - normalize umlauts (keep both versions)
    - collapse whitespace
    
    Returns (normalized, original) tuple.
    """
    original = text
    
    # Lowercase
    normalized = text.lower()
    
    # Normalize umlauts
    normalized, _ = normalize_umlauts(normalized)
    
    # Collapse whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()
    
    return normalized, original


def extract_text_variants(text: str) -> list[str]:
    """
    Extract all text variants for matching (original + normalized).
    """
    normalized, original = normalize_text(text)
    variants = [normalized]
    
    # Also add original if different
    if original.lower() != normalized:
        variants.append(original.lower())
    
    return variants






