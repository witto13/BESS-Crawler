"""
Detect simple company patterns; placeholder for NER.
"""
import re
from typing import List

COMPANY_PATTERNS = [
    r"\b[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9\s,&.-]+?(?:GmbH|AG|UG|GmbH & Co\. KG|KG)\b",
]


def find_companies(text: str) -> List[str]:
    companies = []
    for pattern in COMPANY_PATTERNS:
        companies.extend(re.findall(pattern, text))
    return companies







