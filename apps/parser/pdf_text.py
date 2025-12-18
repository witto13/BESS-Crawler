"""
PDF text extraction using pdfplumber.
Supports progressive extraction (first N pages) and text caching.
"""
from typing import Optional, Tuple
import io
import logging
import hashlib
import json
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available, PDF extraction will fail")


def _text_cache_key(pdf_bytes: bytes, url: str = "") -> str:
    """Generate cache key for PDF text."""
    if url:
        return hashlib.sha256((url + str(len(pdf_bytes))).encode()).hexdigest()
    return hashlib.sha256(pdf_bytes).hexdigest()


def get_cached_text(pdf_bytes: bytes, url: str, cache_base: Path) -> Optional[str]:
    """Get cached extracted text if available."""
    cache_key = _text_cache_key(pdf_bytes, url)
    cache_dir = cache_base / cache_key[:2]
    cache_file = cache_dir / f"{cache_key}.txt"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.debug("Error reading text cache: %s", e)
    
    return None


def set_cached_text(pdf_bytes: bytes, url: str, text: str, cache_base: Path) -> None:
    """Store extracted text in cache."""
    cache_key = _text_cache_key(pdf_bytes, url)
    cache_dir = cache_base / cache_key[:2]
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{cache_key}.txt"
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        logger.warning("Error writing text cache: %s", e)


def extract_text(
    pdf_bytes: bytes,
    max_pages: Optional[int] = None,
    url: str = "",
    cache_base: Optional[Path] = None
) -> Optional[str]:
    """
    Extract text from PDF.
    
    Args:
        pdf_bytes: PDF content
        max_pages: Maximum pages to extract (None = all pages)
        url: URL for cache key
        cache_base: Base path for text cache
    
    Returns:
        Extracted text or None
    """
    if not PDFPLUMBER_AVAILABLE:
        return None
    
    # Check cache
    if cache_base and url:
        cached = get_cached_text(pdf_bytes, url, cache_base)
        if cached:
            logger.debug("Text cache hit: %s", url)
            return cached
    
    try:
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_to_extract = pdf.pages[:max_pages] if max_pages else pdf.pages
            
            for page in pages_to_extract:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        text = "\n\n".join(text_parts) if text_parts else None
        
        # Store in cache
        if text and cache_base and url:
            set_cached_text(pdf_bytes, url, text, cache_base)
        
        return text
    except Exception as e:
        logger.warning("Failed to extract PDF text: %s", e)
        return None


def extract_progressive(
    pdf_bytes: bytes,
    initial_pages: int = 3,
    url: str = "",
    cache_base: Optional[Path] = None
) -> Tuple[Optional[str], bool]:
    """
    Extract text progressively: first N pages, then check for triggers.
    
    Returns:
        (text, has_triggers)
    """
    if not PDFPLUMBER_AVAILABLE:
        return None, False
    
    # Check cache first
    if cache_base and url:
        cached = get_cached_text(pdf_bytes, url, cache_base)
        if cached:
            # Check for triggers in cached text
            triggers = ["batteriespeicher", "energiespeicher", "bebauungsplan", "aufstellungsbeschluss"]
            has_triggers = any(trigger in cached.lower() for trigger in triggers)
            return cached, has_triggers
    
    # Extract first N pages
    initial_text = extract_text(pdf_bytes, max_pages=initial_pages, url="", cache_base=None)
    
    if not initial_text:
        return None, False
    
    # Check for triggers
    triggers = ["batteriespeicher", "energiespeicher", "bebauungsplan", "aufstellungsbeschluss"]
    has_triggers = any(trigger in initial_text.lower() for trigger in triggers)
    
    # If triggers found or we want full text, extract all
    if has_triggers:
        full_text = extract_text(pdf_bytes, max_pages=None, url=url, cache_base=cache_base)
        return full_text, True
    
    # Store initial text in cache
    if cache_base and url:
        set_cached_text(pdf_bytes, url, initial_text, cache_base)
    
    return initial_text, False


