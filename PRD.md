# PRD – BESS Forensic Crawler DE

## Ziel
Bundesweite, forensisch nachvollziehbare Datenbank aller Verfahren ab 2023 mit Bezug zu Batteriespeicher/Stromspeicher (BESS) und Mittel-/Hochspannung. Jede Zeile besitzt Primärquelle, Datum und Dokument-Hash.

## Nutzer
- Grid/BD/M&A Teams
- Legal/Permitting
- Data/Market Intel

## Output
- Postgres/PostGIS als System-of-Record
- Excel (.xlsx) als Arbeitsformat
- Optional GeoJSON/Parquet

## Muss-Kriterien
- Felder: `source_url`, `source_date`, `doc_hash`
- Dokumente speichern oder hashen + Retrieval-Metadaten
- OCR-Fallback bei PDFs ohne Textlayer
- Dedup über Verfahrenstitel + Kommune + Geometrie/Flurstück/Umspannwerk

## Qualitätskriterien (forensisch)
- Vollständigkeit: best effort + messbar (Coverage je Bundesland/Quelle)
- Reproduzierbarkeit: gleiche Inputs ⇒ gleiche Outputs
- Audit-Trail: jedes Feld rückführbar auf Dokument/Abschnitt

## Nicht-Ziele
- Keine Rechtsberatung
- Keine Echtzeit-Garantie (tägliche/weekly Sync ok)

## Datenquellen-Connectoren
1) Planungs-/Beteiligungsportale (z. B. DiPlanung)  
2) XPlanung/WFS (strukturierte Plandaten)  
3) RIS (SessionNet/ALLRIS/Somacos/SD.NET)  
4) Amtsblätter/Bekanntmachungen (PDF/HTML)

## Datenmodell (minimal, auditfähig)
- `procedures`: id, Titel, Instrument, Status, Gebiet (state/county/municipality + Schlüssel), optional Geo, Scores, Firma
- `sources`: je Verfahren Quelle/System, URLs, Datum, Retrieval-Info
- `documents`: je Quelle Dokument-URL/Typ, Hash, Pfad, Text/OCR, Pagemap
- `extractions`: Feld, Wert, Methode, Evidence-Snippet

## Scoring
- BESS-Score: +5 batteriespeicher/BESS, +3 stromspeicher/energiespeicher, +2 container/lithium, -5 wärmespeicher etc.
- Grid-Score: +5 Umspannwerk/110–380 kV, +3 Mittelspannung/20–30 kV, +2 Schaltanlage, +1 Trafostation
- Aufnahme: `bess_score >= 3` und `grid_score >= 3`; Confidence hoch bei explizitem Batteriespeicher + Umspannwerk/110kV

## Dedup
Stabiler Hash über normierten Titel, municipality_key (ARS/AGS), optional Umspannwerk/Flurstück/bbox und Dokument-Hashes.

## Coverage & Metriken
- Quellen-Coverage je Bundesland, Fehlersummen (HTTP, Parsing), OCR-Quote.
- Re-Run-Fähigkeit mit fixiertem Input (Seeds, Crawl-Params, Code-Version).

## Betriebsanforderungen
- Containerisiert (docker-compose), PostGIS + Redis.
- Logs + Retry/Backoff, Idempotenz.
- Speicherkonzept für Dokumente (Filesystem oder S3/MinIO).







