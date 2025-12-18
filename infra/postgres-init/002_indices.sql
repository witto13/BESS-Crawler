-- Helpful indices
CREATE INDEX IF NOT EXISTS idx_procedures_title_norm ON procedures USING gin (to_tsvector('simple', title_norm));
CREATE INDEX IF NOT EXISTS idx_procedures_municipality_key ON procedures (municipality_key);
CREATE INDEX IF NOT EXISTS idx_procedures_geo ON procedures USING gist (geometry);
CREATE INDEX IF NOT EXISTS idx_procedures_bbox ON procedures USING gist (bbox);

CREATE INDEX IF NOT EXISTS idx_sources_procedure ON sources (procedure_id);
CREATE INDEX IF NOT EXISTS idx_sources_url ON sources (source_url);

CREATE INDEX IF NOT EXISTS idx_documents_source ON documents (source_id);
CREATE INDEX IF NOT EXISTS idx_documents_sha ON documents (sha256);
CREATE INDEX IF NOT EXISTS idx_documents_path ON documents (file_path);

CREATE INDEX IF NOT EXISTS idx_extractions_document ON extractions (document_id);
CREATE INDEX IF NOT EXISTS idx_extractions_field ON extractions (field);







