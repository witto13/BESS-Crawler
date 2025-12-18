"""
Extract dates (Aufstellungsbeschluss, etc.) from text.
"""
import re
from typing import List, Tuple, Optional
from datetime import datetime

# German date patterns
DATE_PATTERNS = [
    # DD.MM.YYYY
    re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})"),
    # DD.MM.YY
    re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{2})\b"),
    # DD/MM/YYYY
    re.compile(r"(\d{1,2})[/-]\s*(\d{1,2})[/-]\s*(\d{4})"),
]

# Keywords that indicate decision dates
DECISION_KEYWORDS = [
    "aufstellungsbeschluss",
    "beschluss",
    "satzungsbeschluss",
    "beschlossen am",
    "beschlossen",
    "beschlussfassung",
    "beschluss vom",
    "beschlussfassung am",
]


def extract_dates(text: str) -> List[Tuple[str, datetime]]:
    """
    Extract dates from text, with context.
    Returns list of (context, date) tuples.
    """
    results = []
    text_lower = text.lower()
    
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            try:
                day, month, year = match.groups()
                # Handle 2-digit years
                if len(year) == 2:
                    year_int = int(year)
                    if year_int < 50:
                        year = f"20{year}"
                    else:
                        year = f"19{year}"
                
                date_obj = datetime(int(year), int(month), int(day))
                
                # Check if date is in reasonable range (2020-2030 for recent procedures)
                if 2020 <= date_obj.year <= 2030:
                    # Get context (50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()
                    
                    results.append((context, date_obj))
            except (ValueError, TypeError):
                continue
    
    return results


def find_decision_date(text: str) -> Optional[datetime]:
    """
    Find Aufstellungsbeschluss or similar decision date.
    """
    text_lower = text.lower()
    dates = extract_dates(text)
    
    # Look for dates near decision keywords
    for keyword in DECISION_KEYWORDS:
        keyword_pos = text_lower.find(keyword)
        if keyword_pos != -1:
            # Find nearest date within 200 chars
            for context, date_obj in dates:
                date_pos = text_lower.find(context.lower())
                if date_pos != -1 and abs(date_pos - keyword_pos) < 200:
                    return date_obj
    
    # If no keyword match, return first date found (if any)
    if dates:
        return dates[0][1]
    
    return None







