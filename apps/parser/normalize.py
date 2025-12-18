"""
Normalization helpers for titles and text.
"""
import re
import unicodedata


def normalize_title(title: str) -> str:
    text = unicodedata.normalize("NFKD", title).lower()
    text = re.sub(r"[^a-z0-9äöüß ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text







