# BESS Forensic Crawler DE

Forensisch nachvollziehbarer Crawler/ETL für batteriebezogene Verfahren (BESS) mit MS/HS-Bezug in Deutschland. Primärquelle-fokussiert, reproduzierbar, mit Audit-Trail bis auf Dokument- und Textstellen-Ebene.

## Ziele
- Bundesweite Abdeckung ab 2023, beginnend mit Brandenburg.
- System of Record in Postgres/PostGIS, Arbeitsformat als Excel-Export.
- Forensische Nachvollziehbarkeit: `source_url`, `source_date`, `doc_hash`, OCR-Fallback, Dedup.

## Architektur (Kurzüberblick)
- `apps/orchestrator`: Scheduling, Queueing, Backoff/Retry.
- `apps/crawlers`: Quellenspezifische Connectoren (DiPlanung, WFS/XPlanung, RIS, Amtsblätter).
- `apps/downloader`: Robustes Fetching (ETag, Hash, Storage).
- `apps/parser`: Text-/OCR-Pipeline.
- `apps/extract`: Scoring (BESS/Grid), Entitäten, Mengen.
- `apps/dedupe`: Titel/Schlüssel/Geo-Matching.
- `apps/export`: Excel/Parquet Writer.
- `infra/postgres-init`: SQL-Schema + Indizes.

## Schnellstart
1) `.env` aus `.env.example` kopieren und Variablen setzen.  
2) `docker-compose up -d db redis orchestrator worker` (Code wird ins Image gebaut, lokale Mounts aktiv).  
3) `psql` gegen Container und Schema prüfen (`infra/postgres-init`).  
4) Brandenburg-Runbook lesen: `docs/runbook_brandenburg.md`.

## Services (docker-compose)
- `db`: Postgres 15 + PostGIS 3.4
- `redis`: Queue/Backoff
- `orchestrator`: Python-Service (Jobs in Redis Queue)
- `worker`: Python-Service (BLPOP + Verarbeitung)
- `minio`: Optionaler S3-kompatibler Storage für Dokumente

## ENV
- `POSTGRES_DSN` e.g. `postgresql://bess:bess@db:5432/bess`
- `REDIS_URL` e.g. `redis://redis:6379/0`
- `QUEUE_NAME` default `crawl`
- `STORAGE_BASE_PATH` default `/data/documents`
- `S3_ENDPOINT` (optional), `S3_ACCESS_KEY`, `S3_SECRET_KEY`

## Datenquellen (erste Welle)
- DiPlanung/Planungsportale (Beteiligung)
- XPlanung/WFS (B-Plan/FNP-Layer)
- RIS (SessionNet/ALLRIS/Somacos/SD.NET)
- Amtsblätter/Bekanntmachungen

## Scoring (vereinfacht)
- BESS-Score: Batteriespeicher/Container/Lithium vs. Negationen (Wärmespeicher etc.)
- Grid-Score: Umspannwerk/110–380 kV/Mittelspannung/Schaltanlage
- Aufnahme: `bess_score >= 3` **und** `grid_score >= 3`

## Deduplizierung
Stabiler Hash über normierten Titel, amtlichen Schlüssel (AGS/ARS), optional Geo/Umspannwerk/Flurstück und Dokument-Hashes.

## Compliance & Forensik
- Jede Zeile rückführbar auf Primärquelle.
- OCR nur bei fehlendem Textlayer, Hashes werden gespeichert.
- Coverage-Metriken je Bundesland/Quelle (noch umzusetzen).

## SSL/TLS Troubleshooting

If you encounter SSL/TLS errors when crawling, use the diagnostic tool to identify the issue:

```bash
# Basic SSL diagnostic (inside Docker)
docker compose exec worker python scripts/ssl_diagnose.py https://example.com

# With insecure mode (tests verify=False to determine if it's a CA bundle issue)
docker compose exec worker python scripts/ssl_diagnose.py https://ssl.ratsinfo-online.net/... --insecure
```

The diagnostic tool will:
- Show DNS resolution
- Test HTTPS with default certifi bundle
- Test HTTPS with explicit certifi CA bundle
- Optionally test with `verify=False` (if `--insecure` flag is used)
- Provide diagnosis summary (CA bundle issue vs server TLS misconfiguration)

**Common Issues:**
- **CA Bundle Issue**: Connection works with `verify=False` but fails with `verify=True`
  - Fix: Update certifi or use SSL fallback mechanism for known-bad domains
- **Server TLS Misconfiguration**: Connection fails even with `verify=False`
  - Fix: Server-side TLS configuration issue (not fixable from client)

## Nächste Schritte
- Dockerfile für Worker hinzufügen.
- Erste Connectoren für Brandenburg füllen (`apps/crawlers/diplanung`, `.../ris`, `.../gazette`).
- Seed-Liste aus Destatis/BKG laden (`docs/seed_municipalities.md`).

