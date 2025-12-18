"""
Wrap values with evidence snippets for auditability.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Evidence:
    value: str
    snippet: str
    page: Optional[int] = None







