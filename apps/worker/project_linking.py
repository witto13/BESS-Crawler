"""
Project linking logic: integrates container detection and entity resolution into worker pipeline.
"""
import logging
from typing import Dict, Optional, Tuple
import uuid

from apps.extract.container_detection import is_valid_procedure
from apps.extract.entity_resolution import (
    compute_project_signature,
    find_matching_project,
    compute_maturity_stage,
)
from apps.extract.project_rollup import (
    compute_best_fields,
    compute_project_dates,
    compute_project_confidence,
)
from apps.db.dao import (
    upsert_project_entity,
    link_procedure_to_project,
    insert_source,
)

logger = logging.getLogger(__name__)


def link_procedure_to_project_entity(
    proc_norm: Dict,
    classifier_result: Optional[Dict],
    region: str,
    source: str,
    raw: Dict,
    db_cursor
) -> Optional[str]:
    """
    Link a procedure to a project entity, creating one if needed.
    
    Returns:
        project_id if successful, None if skipped
    """
    # Container detection and validation
    discovery_source = raw.get("discovery_source") or proc_norm.get("discovery_source")
    confidence_score = classifier_result.get("confidence_score", 0.0) if classifier_result else 0.0
    
    # Get extracted text if available
    extracted_text = None
    if "extracted_text" in raw:
        extracted_text = raw["extracted_text"]
    elif "all_text" in raw:
        extracted_text = raw["all_text"]
    
    is_valid, skip_reason = is_valid_procedure(
        proc_norm.get("title_norm", ""),
        raw.get("url", ""),
        discovery_source,
        classifier_result,
        confidence_score,
        extracted_text=extracted_text
    )
    
    if not is_valid:
        logger.info("Skipping procedure %s: %s", proc_norm.get("procedure_id"), skip_reason)
        # Still store source for audit trail
        try:
            insert_source(db_cursor, {
                "source_id": str(uuid.uuid4()),
                "procedure_id": None,  # No procedure
                "source_system": source,
                "source_url": raw.get("url", ""),
                "source_date": None,
                "http_status": 200,
                "discovery_source": discovery_source,
                "discovery_path": raw.get("discovery_path") or proc_norm.get("discovery_path"),
            })
        except Exception as e:
            logger.warning("Failed to store skipped source: %s", e)
        return None
    
    # Compute project signature
    signature = compute_project_signature(proc_norm, classifier_result)
    municipality_key = proc_norm.get("municipality_key", "")
    procedure_type = proc_norm.get("procedure_type")
    
    # Special handling for §36: always attempt to create/link
    if procedure_type == "PERMIT_36_EINVERNEHMEN":
        # Get connection from cursor
        conn = db_cursor.connection if hasattr(db_cursor, 'connection') else db_cursor
        match_result = find_matching_project(signature, municipality_key, procedure_type, conn)
        if not match_result:
            # Create new project with §36 maturity
            project_data = {
                "state": region,
                "municipality_key": municipality_key,
                "municipality_name": proc_norm.get("municipality"),
                "county": proc_norm.get("county"),
                "maturity_stage": "PERMIT_36",
                "legal_basis_best": "§36",
                "project_components": proc_norm.get("project_components"),
                "max_confidence": confidence_score,
                "needs_review": classifier_result.get("review_recommended", False) if classifier_result else False,
            }
            best_fields = compute_best_fields([proc_norm], signature)
            project_data.update(best_fields)
            first_seen, last_seen = compute_project_dates([proc_norm])
            project_data["first_seen_date"] = first_seen
            project_data["last_seen_date"] = last_seen
            
            project_id = upsert_project_entity(db_cursor, project_data)
            link_procedure_to_project(db_cursor, project_id, proc_norm["procedure_id"], 0.85, "PERMIT_36_NEW")
            logger.debug("Created new §36 project %s for procedure %s", project_id, proc_norm["procedure_id"])
            return project_id
        else:
            project_id, link_conf, link_reason = match_result
            link_procedure_to_project(db_cursor, project_id, proc_norm["procedure_id"], link_conf, link_reason)
            return project_id
    else:
        # Normal matching
        # Get connection from cursor
        conn = db_cursor.connection if hasattr(db_cursor, 'connection') else db_cursor
        match_result = find_matching_project(signature, municipality_key, procedure_type, conn)
        if match_result:
            project_id, link_conf, link_reason = match_result
            link_procedure_to_project(db_cursor, project_id, proc_norm["procedure_id"], link_conf, link_reason)
            logger.debug("Linked procedure %s to project %s (%s)", proc_norm["procedure_id"], project_id, link_reason)
            return project_id
        else:
            # Create new project
            project_data = {
                "state": region,
                "municipality_key": municipality_key,
                "municipality_name": proc_norm.get("municipality"),
                "county": proc_norm.get("county"),
                "maturity_stage": compute_maturity_stage([procedure_type] if procedure_type else [], proc_norm.get("legal_basis")),
                "legal_basis_best": proc_norm.get("legal_basis"),
                "project_components": proc_norm.get("project_components"),
                "max_confidence": confidence_score,
                "needs_review": classifier_result.get("review_recommended", False) if classifier_result else False,
            }
            best_fields = compute_best_fields([proc_norm], signature)
            project_data.update(best_fields)
            first_seen, last_seen = compute_project_dates([proc_norm])
            project_data["first_seen_date"] = first_seen
            project_data["last_seen_date"] = last_seen
            
            project_id = upsert_project_entity(db_cursor, project_data)
            link_procedure_to_project(db_cursor, project_id, proc_norm["procedure_id"], 1.0, "NEW_PROJECT")
            logger.debug("Created new project %s for procedure %s", project_id, proc_norm["procedure_id"])
            return project_id

