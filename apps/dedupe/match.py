"""
Simple title + key matcher placeholder.
"""
from typing import Dict
from apps.parser.normalize import normalize_title


def compute_procedure_hash(title: str, municipality_key: str) -> str:
    norm = normalize_title(title)
    return f"{municipality_key}:{norm}"


def is_duplicate(existing: Dict, candidate: Dict) -> bool:
    return (
        existing.get("procedure_hash") == candidate.get("procedure_hash")
    )







