"""
Parse DiPlanung records into normalized procedures.
"""
from typing import Dict, Optional
from apps.parser.normalize import normalize_title
from apps.dedupe.match import compute_procedure_hash


def parse_procedure(raw: Dict, municipality_key: Optional[str] = None) -> Dict:
    title_raw = raw.get("title") or raw.get("title_raw") or ""
    title_norm = normalize_title(title_raw)
    proc_hash = compute_procedure_hash(title_raw, municipality_key or "")
    return {
        "title_raw": title_raw,
        "title_norm": title_norm,
        "procedure_hash": proc_hash,
        "source_url": raw.get("url"),
        "municipality_key": municipality_key,
    }

