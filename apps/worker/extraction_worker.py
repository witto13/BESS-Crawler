"""
Extraction worker: processes candidates, downloads PDFs, extracts text, classifies, and saves procedures.
Uses progressive extraction, caching, and batch writes for performance.
"""
import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
from urllib.parse import urlparse

from apps.db.dao_candidates import get_candidates_for_extraction, update_candidate_status
from apps.db.dao_stats import insert_crawl_stats
from apps.db.dao_batch import upsert_procedures_batch, insert_sources_batch
from apps.db.dao import with_connection, insert_document
from apps.downloader.fetch_cached import download_cached, head_cached
from apps.parser.pdf_text import extract_progressive
from apps.parser.html_text import extract_text as extract_html_text
from apps.extract.classifier_bess import classify_relevance
from apps.extract.container_detection import is_valid_procedure
from apps.extract.quantities import find_capacity_mw, find_capacity_mwh
from apps.extract.area import find_largest_area
from apps.extract.dates import find_decision_date
from apps.extract.entities_company import find_companies
from apps.extract.location import extract_location
from apps.downloader.storage import save_bytes_fs
from apps.downloader.fetch import sha256_bytes
from apps.worker.project_linking import link_procedure_to_project_entity
from apps.orchestrator.config import settings

logger = logging.getLogger(__name__)


def process_extraction_job(payload: dict, run_id: str) -> None:
    """
    Process extraction job: download PDFs, extract text, classify, save procedures.
    """
    candidate_id = payload.get("candidate_id")
    region = payload.get("region", "BB")
    source = payload.get("source", "unknown")
    municipality_key = payload.get("municipality_key", "")
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
    
    try:
        # Get candidate from DB
        @with_connection
        def get_candidate(cur):
            cur.execute("""
                SELECT candidate_id, run_id, municipality_key, discovery_source, discovery_path,
                       title, date_hint, url, doc_urls, prefilter_score
                FROM crawl_candidates
                WHERE candidate_id = %s
            """, (candidate_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "candidate_id": row[0],
                "run_id": row[1],
                "municipality_key": row[2],
                "discovery_source": row[3],
                "discovery_path": row[4],
                "title": row[5],
                "date_hint": row[6],
                "url": row[7],
                "doc_urls": row[8],
                "prefilter_score": float(row[9]) if row[9] else 0.0,
            }
        
        candidate = get_candidate()
        if not candidate:
            logger.warning("Candidate %s not found", candidate_id)
            return
        
        title = candidate["title"]
        url = candidate["url"]
        doc_urls = candidate.get("doc_urls") or []
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Download HTML page
        t0 = time.time()
        html_result = download_cached(url, mode=mode, use_cache=True)
        timings["fetch_html_ms"] = (time.time() - t0) * 1000
        
        html_text = ""
        if html_result:
            html_content, _ = html_result
            html_text = extract_html_text(html_content.decode("utf-8", errors="ignore"))
            counts["pages_fetched"] = 1
        
        # Download PDFs (with size check and progressive extraction)
        # For RIS: if no doc_urls but agenda has privileged terms, fetch agenda item to get attachments
        if not doc_urls and candidate.get("discovery_source") == "RIS":
            privileged_agenda_terms = [
                "einvernehmen", "bauantrag", "bauvorbescheid", "vorbescheid",
                "stellungnahme", "energie", "speicher", "photovoltaik", "umspannwerk",
            ]
            title_lower = title.lower()
            has_privileged_term = any(term in title_lower for term in privileged_agenda_terms)
            
            if has_privileged_term:
                # Fetch agenda item to get attachments
                try:
                    from apps.crawlers.ris.sessionnet import fetch_agenda_item
                    agenda_data = fetch_agenda_item(url)
                    doc_urls = [doc.get("doc_url") for doc in agenda_data.get("documents", []) if doc.get("doc_url")]
                except Exception as e:
                    logger.warning("Failed to fetch agenda item %s: %s", url, e)
        
        all_text = title + " " + html_text
        docs = []
        storage_base = Path(settings.storage_base_path)
        cache_base = Path(settings.crawl_cache_base)
        text_cache_base = Path(settings.crawl_text_cache_base)
        
        pdf_download_time = 0
        pdf_extract_time = 0
        
        for doc_url in (doc_urls or [])[:5]:  # Limit to 5 PDFs per candidate
            try:
                # HEAD request to check size
                t0 = time.time()
                headers = head_cached(doc_url, mode=mode)
                head_time = (time.time() - t0) * 1000
                
                if headers:
                    content_length = headers.get("Content-Length")
                    if content_length:
                        size_mb = int(content_length) / (1024 * 1024)
                        if size_mb > settings.crawl_pdf_max_size_mb and mode == "fast" and candidate["prefilter_score"] < 0.8:
                            logger.debug("Skipping large PDF %s (%.1f MB) in fast mode", doc_url, size_mb)
                            counts["pdfs_skipped"] += 1
                            continue
                
                # Download PDF
                t0 = time.time()
                pdf_result = download_cached(doc_url, mode=mode, use_cache=True)
                pdf_download_time += (time.time() - t0) * 1000
                
                if not pdf_result:
                    continue
                
                pdf_content, _ = pdf_result
                counts["pdfs_downloaded"] += 1
                
                # Progressive extraction
                t0 = time.time()
                initial_pages = 3 if mode == "fast" else 5
                pdf_text, has_triggers = extract_progressive(
                    pdf_content,
                    initial_pages=initial_pages,
                    url=doc_url,
                    cache_base=text_cache_base
                )
                pdf_extract_time += (time.time() - t0) * 1000
                
                if pdf_text:
                    all_text += " " + pdf_text
                
                # Save PDF
                sha = sha256_bytes(pdf_content)
                rel_path = f"docs/{sha[:2]}/{sha}.bin"
                save_bytes_fs(base_path=storage_base, relative_path=rel_path, data=pdf_content)
                
                docs.append({
                    "doc_url": doc_url,
                    "sha256": sha,
                    "file_path": rel_path,
                    "text_extracted": pdf_text,
                })
                
            except Exception as e:
                logger.warning("Failed to process PDF %s: %s", doc_url, e)
                continue
        
        timings["fetch_pdf_ms"] = pdf_download_time
        timings["extract_pdf_ms"] = pdf_extract_time
        
        # Classify
        t0 = time.time()
        from datetime import datetime
        proc_date = candidate.get("date_hint") or datetime.now()
        classifier_result = classify_relevance(all_text, title=title, date=proc_date)
        timings["classify_ms"] = (time.time() - t0) * 1000
        
        # Check if valid procedure (pass extracted text for relaxed gating)
        is_valid, skip_reason = is_valid_procedure(
            title.lower(),
            url,
            candidate.get("discovery_source"),
            classifier_result,
            classifier_result.get("confidence_score", 0.0),
            extracted_text=all_text
        )
        
        if not is_valid:
            @with_connection
            def mark_skipped(cur):
                update_candidate_status(cur, candidate_id, "SKIPPED", skip_reason)
            mark_skipped()
            counts["procedures_skipped"] += 1
            return
        
        # Create procedure
        proc_norm = {
            "procedure_id": str(uuid.uuid4()),
            "title_raw": title,
            "title_norm": title.lower(),
            "state": region,
            "municipality_key": municipality_key,
            "source_system": source,
            "discovery_source": candidate.get("discovery_source"),
            "discovery_path": candidate.get("discovery_path"),
        }
        
        # Extract additional info
        if all_text:
            capacity_mw = find_capacity_mw(all_text)
            capacity_mwh = find_capacity_mwh(all_text)
            area_ha = find_largest_area(all_text)
            decision_date = find_decision_date(all_text)
            companies = find_companies(all_text)
            location = extract_location(all_text)
            
            if capacity_mw:
                proc_norm["capacity_mw"] = capacity_mw
            if capacity_mwh:
                proc_norm["capacity_mwh"] = capacity_mwh
            if area_ha:
                proc_norm["area_hectares"] = area_ha
            if decision_date:
                proc_norm["decision_date"] = decision_date.date()
            if companies:
                proc_norm["developer_company"] = companies[0] if len(companies) == 1 else ", ".join(companies[:3])
            if location:
                proc_norm["site_location_raw"] = location
        
        # Set classifier fields
        if classifier_result.get("is_relevant") or classifier_result.get("is_candidate"):
            proc_type = classifier_result.get("procedure_type")
            # If procedure_type cannot be tagged confidently, set to UNKNOWN
            if not proc_type:
                proc_type = "UNKNOWN"
                proc_norm["review_recommended"] = True
            else:
                proc_norm["review_recommended"] = classifier_result.get("review_recommended", False)
            
            proc_norm["procedure_type"] = proc_type
            proc_norm["legal_basis"] = classifier_result.get("legal_basis")
            proc_norm["project_components"] = classifier_result.get("project_components")
            proc_norm["ambiguity_flag"] = classifier_result.get("ambiguity_flag", False)
            
            import json as json_lib
            if classifier_result.get("evidence_snippets"):
                # In fast mode, only store evidence for high confidence
                if mode == "fast" and classifier_result.get("confidence_score", 0) < 0.7:
                    proc_norm["evidence_snippets"] = None
                else:
                    proc_norm["evidence_snippets"] = json_lib.dumps(classifier_result["evidence_snippets"])
        
        # Batch write (accumulate for batch)
        t0 = time.time()
        @with_connection
        def save_procedure(cur):
            # For now, use single insert (batch would need accumulator)
            from apps.db.dao import upsert_procedure, insert_source
            upsert_procedure(cur, proc_norm)
            
            source_id = str(uuid.uuid4())
            insert_source(cur, {
                "source_id": source_id,
                "procedure_id": proc_norm["procedure_id"],
                "source_system": source,
                "source_url": url,
                "http_status": 200,
                "discovery_source": candidate.get("discovery_source"),
                "discovery_path": candidate.get("discovery_path"),
            })
            
            # Save documents
            for doc in docs:
                doc_id = str(uuid.uuid4())
                insert_document(cur, {
                    "document_id": doc_id,
                    "source_id": source_id,
                    "doc_url": doc["doc_url"],
                    "doc_type": "pdf",
                    "sha256": doc["sha256"],
                    "file_path": doc["file_path"],
                    "text_extracted": doc["text_extracted"],
                    "ocr_used": False,
                    "page_map": None,
                })
            
            # Link to project
            try:
                link_procedure_to_project_entity(
                    proc_norm,
                    classifier_result,
                    region,
                    source,
                    {"url": url, "discovery_source": candidate.get("discovery_source"), "discovery_path": candidate.get("discovery_path")},
                    cur
                )
            except Exception as e:
                logger.warning("Failed to link to project: %s", e)
            
            # Mark candidate as done
            update_candidate_status(cur, candidate_id, "DONE")
        
        save_procedure()
        timings["db_write_ms"] = (time.time() - t0) * 1000
        counts["procedures_saved"] = 1
        
        # Save stats
        total_ms = (time.time() - start_time) * 1000
        timings["total_ms"] = total_ms
        
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
        
        logger.debug("Extraction completed for candidate %s: %d PDFs, %.1fms", candidate_id, counts["pdfs_downloaded"], total_ms)
        
    except Exception as e:
        logger.error("Extraction job failed for candidate %s: %s", candidate_id, e, exc_info=True)
        @with_connection
        def mark_error(cur):
            update_candidate_status(cur, candidate_id, "ERROR", str(e))
        mark_error()
        raise

