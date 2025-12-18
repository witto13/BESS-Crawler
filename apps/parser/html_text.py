"""
HTML text extraction placeholder.
"""
from bs4 import BeautifulSoup
from typing import Optional


def extract_text(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")







