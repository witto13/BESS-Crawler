#!/usr/bin/env python3
"""
Populate official_website_url in municipality_seed metadata.
Derives URLs from municipality names as fallback.
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool
import json

def sanitize_name_for_url(name: str) -> str:
    """Sanitize municipality name for URL generation."""
    if not name:
        return ""
    
    # Remove parentheses and their contents
    sanitized = re.sub(r'\([^)]*\)', '', name)
    
    # Convert to lowercase and replace special chars
    sanitized = sanitized.lower()
    sanitized = sanitized.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    sanitized = sanitized.replace("/", "-").replace("\\", "-")
    sanitized = sanitized.replace(".", "").replace(",", "")
    
    # Replace spaces with dashes
    sanitized = re.sub(r'[\s_]+', '-', sanitized)
    sanitized = re.sub(r'-+', '-', sanitized)
    sanitized = sanitized.strip('-').strip()
    
    # Remove invalid characters
    sanitized = re.sub(r'[^a-z0-9\-]', '', sanitized)
    
    return sanitized

def generate_official_url(municipality_name: str) -> str:
    """Generate likely official website URL from municipality name."""
    sanitized = sanitize_name_for_url(municipality_name)
    if not sanitized:
        return ""
    
    # Try common patterns
    patterns = [
        f"https://www.{sanitized}.de",
        f"https://{sanitized}.de",
    ]
    
    return patterns[0]  # Return first pattern

def populate_official_urls():
    """Populate official_website_url in municipality_seed metadata."""
    pool = get_pool()
    updated = 0
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Get all Brandenburg municipalities
            cur.execute("""
                SELECT municipality_key, name, metadata
                FROM municipality_seed
                WHERE state = 'BB'
            """)
            
            municipalities = cur.fetchall()
            
            for muni_key, name, metadata in municipalities:
                # Check if already has official_website_url
                if metadata and metadata.get("official_website_url"):
                    continue
                
                # Generate URL from name
                official_url = generate_official_url(name)
                
                if not official_url:
                    continue
                
                # Update metadata
                if not metadata:
                    metadata = {}
                
                metadata["official_website_url"] = official_url
                
                cur.execute("""
                    UPDATE municipality_seed
                    SET metadata = %s
                    WHERE municipality_key = %s
                """, (json.dumps(metadata), muni_key))
                
                updated += 1
                
                if updated % 50 == 0:
                    print(f"Progress: {updated} municipalities updated...")
    
    print(f"✅ Updated {updated} municipalities with official_website_url")
    return updated

if __name__ == "__main__":
    populate_official_urls()


