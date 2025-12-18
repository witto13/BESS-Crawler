"""
Discovery worker: emits candidates without downloading PDFs.
"""
import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from pathlib import Path

import redis

from apps.crawlers.ris.sessionnet import list_procedures as ris_list_procedures
from apps.crawlers.gazette.spider import list_issues, fetch_issue
from apps.crawlers.discovery.municipal_website import (
    discover_municipal_sections,
    crawl_municipal_section,
)
from apps.extract.prefilter import prefilter_score, should_extract
from apps.db.dao_candidates import insert_candidate, update_candidate_status
from apps.db.dao_stats import insert_crawl_stats
from apps.db.dao import with_connection
from apps.orchestrator.config import settings
from apps.orchestrator.queues import enqueue_job
from apps.worker.municipality_aggregator import log_municipality_summary

logger = logging.getLogger(__name__)


def process_discovery_job(payload: dict, run_id: str) -> None:
    """
    Process discovery job: fetch listings, compute prefilter scores, emit candidates.
    """
    region = payload.get("region", "BB")
    source = payload.get("source")
    entrypoint = payload.get("entrypoint", "")
    municipality_key = payload.get("municipality_key", "")
    municipality_name = payload.get("municipality_name", "")
    mode = payload.get("mode", settings.crawl_mode)
    
    job_id = str(uuid.uuid4())
    start_time = time.time()
    
    timings = {
        "fetch_html_ms": 0,
        "fetch_pdf_ms": 0,
        "extract_pdf_ms": 0,
        "classify_ms": 0,
        "db_write_ms": 0,
    }
    
    counts = {
        "pages_fetched": 0,
        "pdfs_downloaded": 0,
        "pdfs_skipped": 0,
        "candidates_found": 0,
        "procedures_saved": 0,
        "procedures_skipped": 0,
    }
    
    domain = None
    candidates = []
    source_status = "SUCCESS"  # SUCCESS, ERROR_SSL, ERROR_OTHER, ERROR_NETWORK
    error_message = None
    discovery_diagnostics = {}  # Store diagnostics from discovery
    
    try:
        # Get official_website_url from municipality_seed if available
        official_website_url = None
        if municipality_key:
            @with_connection
            def get_official_url(cur):
                cur.execute("""
                    SELECT metadata->>'official_website_url' as official_url
                    FROM municipality_seed
                    WHERE municipality_key = %s
                """, (municipality_key,))
                row = cur.fetchone()
                if row and row[0]:
                    return row[0]
                return None
            official_website_url = get_official_url()
        
        # Route to appropriate discovery crawler
        if source == "ris" or source == "sessionnet":
            t0 = time.time()
            try:
                # Handle None or empty entrypoint - discovery will use municipality_name
                base_url = entrypoint if entrypoint and entrypoint.strip() else None
                
                # Create session with official_website_url for discovery
                import requests
                discovery_session = requests.Session()
                if official_website_url:
                    discovery_session.official_website_url = official_website_url
                
                procs, discovery_diagnostics = ris_list_procedures(base_url or "", municipality_name=municipality_name, session=discovery_session)
                discovery_diagnostics["source"] = "RIS"
                timings["fetch_html_ms"] = (time.time() - t0) * 1000
                counts["pages_fetched"] = 1
            except Exception as e:
                # Check if it's an SSL error
                error_str = str(e).lower()
                if "ssl" in error_str or "certificate" in error_str or "tls" in error_str:
                    source_status = "ERROR_SSL"
                    error_message = f"SSL error: {str(e)[:200]}"
                    logger.warning("RIS discovery failed with SSL error for %s: %s", municipality_name, e)
                elif "timeout" in error_str or "connection" in error_str:
                    source_status = "ERROR_NETWORK"
                    error_message = f"Network error: {str(e)[:200]}"
                    logger.warning("RIS discovery failed with network error for %s: %s", municipality_name, e)
                else:
                    source_status = "ERROR_OTHER"
                    error_message = f"Error: {str(e)[:200]}"
                    logger.warning("RIS discovery failed for %s: %s", municipality_name, e)
                procs = []  # Continue with empty list - don't return early
            
            # Parse domain from entrypoint if available, otherwise use municipality name
            if entrypoint and entrypoint.strip():
                parsed = urlparse(entrypoint)
                domain = parsed.netloc
            else:
                domain = municipality_name or "unknown"
            
            # Convert to candidates
            for raw in procs:
                title = raw.get("title", "")
                url = raw.get("url", "")
                date_hint = raw.get("date")
                doc_urls = raw.get("documents", [])
                
                # Use discovery_path from raw data if available, otherwise use entrypoint or municipality name
                discovery_path = raw.get("discovery_path") or entrypoint or municipality_name
                
                # For RIS: parse agenda item titles first, check for privileged terms
                # If agenda title contains privileged terms, download attachments
                privileged_agenda_terms = [
                    "einvernehmen", "bauantrag", "bauvorbescheid", "vorbescheid",
                    "stellungnahme", "energie", "speicher", "photovoltaik", "umspannwerk",
                ]
                title_lower = title.lower()
                has_privileged_term = any(term in title_lower for term in privileged_agenda_terms)
                
                # Compute prefilter score
                score = prefilter_score(title, url)
                
                # If agenda has privileged terms but no doc_urls, we'll need to fetch them
                # For now, create candidate and let extraction worker handle it
                
                candidate = {
                    "run_id": run_id,
                    "municipality_key": municipality_key,
                    "discovery_source": "RIS",
                    "discovery_path": discovery_path,
                    "title": title,
                    "date_hint": date_hint,
                    "url": url,
                    "doc_urls": doc_urls if doc_urls else None,
                    "prefilter_score": score,
                    "status": "NEW",
                }
                candidates.append(candidate)
                counts["candidates_found"] += 1
        
        elif source == "gazette" or source == "amtsblatt":
            t0 = time.time()
            try:
                # Handle None or empty entrypoint - discovery will use municipality_name
                feed_url = entrypoint if entrypoint and entrypoint.strip() else ""
                
                # Create session with official_website_url for discovery
                import requests
                discovery_session = requests.Session()
                if official_website_url:
                    discovery_session.official_website_url = official_website_url
                
                issues, discovery_diagnostics = list_issues(feed_url, municipality_name=municipality_name, session=discovery_session)
                discovery_diagnostics["source"] = "AMTSBLATT"
                timings["fetch_html_ms"] = (time.time() - t0) * 1000
                counts["pages_fetched"] = len(issues)
            except Exception as e:
                # Check if it's an SSL error
                error_str = str(e).lower()
                if "ssl" in error_str or "certificate" in error_str or "tls" in error_str:
                    source_status = "ERROR_SSL"
                    error_message = f"SSL error: {str(e)[:200]}"
                    logger.warning("Amtsblatt discovery failed with SSL error for %s: %s", municipality_name, e)
                elif "timeout" in error_str or "connection" in error_str:
                    source_status = "ERROR_NETWORK"
                    error_message = f"Network error: {str(e)[:200]}"
                    logger.warning("Amtsblatt discovery failed with network error for %s: %s", municipality_name, e)
                else:
                    source_status = "ERROR_OTHER"
                    error_message = f"Error: {str(e)[:200]}"
                    logger.warning("Amtsblatt discovery failed for %s: %s", municipality_name, e)
                issues = []  # Continue with empty list - don't return early
            
            # Parse domain from entrypoint if available, otherwise use municipality name
            if entrypoint and entrypoint.strip():
                parsed = urlparse(entrypoint)
                domain = parsed.netloc
            else:
                domain = municipality_name or "unknown"
            
            # Convert issues to candidates
            for issue in issues:
                title = issue.get("title", "")
                url = issue.get("url", "")
                date_hint = issue.get("date")
                
                # Use discovery_path from issue if available, otherwise use entrypoint or municipality name
                discovery_path = issue.get("discovery_path") or entrypoint or municipality_name
                
                # Fetch issue to get items (lightweight)
                try:
                    issue_data = fetch_issue(url)
                    items = issue_data.get("items", [])
                    
                    for item in items:
                        item_title = item.get("title", "")
                        item_url = item.get("url", "")
                        item_docs = item.get("documents", [])
                        
                        # Compute prefilter score
                        score = prefilter_score(item_title, item_url)
                        
                        candidate = {
                            "run_id": run_id,
                            "municipality_key": municipality_key,
                            "discovery_source": "AMTSBLATT",
                            "discovery_path": discovery_path,
                            "title": item_title,
                            "date_hint": date_hint,
                            "url": item_url,
                            "doc_urls": item_docs if item_docs else None,
                            "prefilter_score": score,
                            "status": "NEW",
                        }
                        candidates.append(candidate)
                        counts["candidates_found"] += 1
                except Exception as e:
                    logger.warning("Failed to fetch issue %s: %s", url, e)
                    continue
        
        elif source == "municipal_website":
            t0 = time.time()
            try:
                sections = discover_municipal_sections(entrypoint)
                timings["fetch_html_ms"] = (time.time() - t0) * 1000
            except Exception as e:
                # Check if it's an SSL error
                error_str = str(e).lower()
                if "ssl" in error_str or "certificate" in error_str or "tls" in error_str:
                    source_status = "ERROR_SSL"
                    error_message = f"SSL error: {str(e)[:200]}"
                    logger.warning("Municipal website discovery failed with SSL error for %s: %s", municipality_name, e)
                elif "timeout" in error_str or "connection" in error_str:
                    source_status = "ERROR_NETWORK"
                    error_message = f"Network error: {str(e)[:200]}"
                    logger.warning("Municipal website discovery failed with network error for %s: %s", municipality_name, e)
                else:
                    source_status = "ERROR_OTHER"
                    error_message = f"Error: {str(e)[:200]}"
                    logger.warning("Municipal website discovery failed for %s: %s", municipality_name, e)
                sections = []  # Continue with empty list - don't return early
            
            # Parse domain from entrypoint if available, otherwise use municipality name
            if entrypoint and entrypoint.strip():
                parsed = urlparse(entrypoint)
                domain = parsed.netloc
            else:
                domain = municipality_name or "unknown"
            
            # Crawl each section
            # Note: sections is a List[str] (URLs), not List[Dict]
            for section_url in sections:
                try:
                    items = crawl_municipal_section(section_url)
                    counts["pages_fetched"] += 1
                    
                    for item in items:
                        title = item.get("title", "")
                        url = item.get("url", "")
                        date_hint = item.get("date")
                        doc_urls = item.get("documents", [])
                        
                        # Compute prefilter score
                        score = prefilter_score(title, url)
                        
                        # Use section URL as discovery_path
                        discovery_path = section_url or entrypoint or municipality_name
                        
                        candidate = {
                            "run_id": run_id,
                            "municipality_key": municipality_key,
                            "discovery_source": "MUNICIPAL_WEBSITE",
                            "discovery_path": discovery_path,
                            "title": title,
                            "date_hint": date_hint,
                            "url": url,
                            "doc_urls": doc_urls if doc_urls else None,
                            "prefilter_score": score,
                            "status": "NEW",
                        }
                        candidates.append(candidate)
                        counts["candidates_found"] += 1
                except Exception as e:
                    logger.warning("Failed to crawl section %s: %s", section_url, e)
                    continue
        
        # Insert candidates and enqueue extraction jobs
        t0 = time.time()
        @with_connection
        def save_candidates(cur):
            enqueued = 0
            skipped = 0
            
            for candidate in candidates:
                try:
                    candidate_id = insert_candidate(cur, candidate)
                    
                    # Enqueue extraction if score passes threshold (source-aware)
                    discovery_source = candidate.get("discovery_source", source.upper())
                    if should_extract(candidate["prefilter_score"], mode, discovery_source):
                        enqueue_job(
                            settings.queue_name,  # Use same queue as discovery jobs
                            {
                                "candidate_id": candidate_id,
                                "run_id": run_id,
                                "region": region,
                                "source": source,
                                "municipality_key": municipality_key,
                                "mode": mode,
                            }
                        )
                        update_candidate_status(cur, candidate_id, "ENQUEUED")
                        enqueued += 1
                    else:
                        update_candidate_status(cur, candidate_id, "SKIPPED", f"prefilter_score {candidate['prefilter_score']:.2f} < threshold")
                        skipped += 1
                except Exception as e:
                    logger.warning("Failed to save candidate: %s", e)
                    continue
            
            return enqueued, skipped
        
        enqueued, skipped = save_candidates()
        timings["db_write_ms"] = (time.time() - t0) * 1000
        counts["procedures_saved"] = enqueued
        counts["procedures_skipped"] = skipped
        
        # Save stats with status
        total_ms = (time.time() - start_time) * 1000
        timings["total_ms"] = total_ms
        
        # Add status to counts_json
        counts["source_status"] = source_status
        if error_message:
            counts["error_message"] = error_message
        
        # Add discovery diagnostics if available
        if discovery_diagnostics:
            counts["discovery_diagnostics"] = discovery_diagnostics
        
        @with_connection
        def save_stats(cur):
            insert_crawl_stats(cur, {
                "run_id": run_id,
                "job_id": job_id,
                "municipality_key": municipality_key,
                "source_type": source.upper(),
                "domain": domain,
                "counts_json": counts,
                "timings_json": timings,
            })
        
        save_stats()
        
        # Log diagnostics at INFO level
        if discovery_diagnostics:
            logger.info(
                "Discovery diagnostics for %s (%s): method=%s, reason=%s, attempted=%d URLs, failed=%d",
                municipality_name,
                source,
                discovery_diagnostics.get("method", "unknown"),
                discovery_diagnostics.get("reason_code", "unknown"),
                len(discovery_diagnostics.get("attempted_urls", [])),
                len(discovery_diagnostics.get("failed_urls", {}))
            )
        
        logger.info("Discovery job completed: %d candidates found, %d enqueued, %d skipped, status=%s", 
                   counts["candidates_found"], enqueued, skipped, source_status)
        
        # Log per-municipality summary (aggregates across all sources)
        log_municipality_summary(municipality_key, municipality_name, run_id)
        
    except Exception as e:
        # Catch-all for unexpected errors - mark as ERROR_OTHER but don't raise
        # This ensures the worker continues processing other jobs
        source_status = "ERROR_OTHER"
        error_message = f"Unexpected error: {str(e)[:200]}"
        logger.error("Discovery job failed for %s (%s): %s", municipality_name, source, e, exc_info=True)
        
        # Still save stats with error status
        total_ms = (time.time() - start_time) * 1000
        timings["total_ms"] = total_ms
        counts["source_status"] = source_status
        counts["error_message"] = error_message
        counts["candidates_found"] = 0
        counts["procedures_saved"] = 0
        counts["procedures_skipped"] = 0
        
        @with_connection
        def save_stats_error(cur):
            insert_crawl_stats(cur, {
                "run_id": run_id,
                "job_id": job_id,
                "municipality_key": municipality_key,
                "source_type": source.upper(),
                "domain": domain or "unknown",
                "counts_json": counts,
                "timings_json": timings,
            })
        
        save_stats_error()
        
        logger.info("Discovery job completed with error: status=%s, candidates=0", source_status)
        
        # Log per-municipality summary even on error
        log_municipality_summary(municipality_key, municipality_name, run_id)

