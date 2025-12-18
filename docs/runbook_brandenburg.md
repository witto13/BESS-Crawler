# Runbook – Brandenburg First Crawl

## Ziel
Schneller MVP-Run für Brandenburg mit amtlichen Gemeindeseeds, DiPlanung-Harvest und Amtsblatt/RIS-Heuristiken.

## Inputs
- Gemeindeliste (Destatis-Auszug oder BKG VG250) → `docs/seed_municipalities.md`
- Portal-Start: `https://bb.beteiligung.diplanung.de/`
- RIS-Heuristiken: SessionNet/ALLRIS/Somacos per Gemeinde
- Amtsblatt-Patterns: meist PDF, häufig `/amtsblatt` oder `/bekanntmachungen`

## Schritte
1) **Seeds laden**  
   - Destatis-Gemeindeverzeichnis oder BKG VG250 herunterladen.  
   - Auf Brandenburg filtern (`state = BB`).  
   - In `municipality_seed` importieren (siehe SQL in `docs/seed_municipalities.md`).

2) **DiPlanung-Crawl**  
   - Einstieg: Portal-Feed oder Listing.  
   - Pro Verfahren: Titel, Status, Kommune, URLs zu Dokumenten/Anlagen.  
   - Dokumente herunterladen, SHA256 bilden, Textlayer prüfen, ggf. OCR.  
   - Scoring anwenden (BESS/Grid) und `procedures`/`sources`/`documents` füllen.

3) **RIS-Discovery**  
   - Heuristik: Subdomains mit `sessionnet`, `allris`, `sdnet`, `somacos`.  
   - Sitemap/`rss.aspx` prüfen; oft `vo020.asp` für Vorlagen/Anlagen.  
   - Mindestens URLs und Dokumente hashen; Status/Datum übernehmen.

4) **Amtsblatt**  
   - Basis-URL aus Gemeinde-Homepage (Regex `/amtsblatt|bekanntmachung|satzung`).  
   - PDFs holen, Hash + OCR falls nötig.  
   - Titel/Datum erkennen (Regex auf Deckblatt), Scoring anwenden.

5) **XPlanung/WFS (optional erste Iteration)**  
   - Landesweite oder kommunale WFS prüfen (GetCapabilities).  
   - B-Plan/FNP-Layer paginieren; Attribute nach BESS/Grid-Mustern durchsuchen.  
   - Geometrie/BBOX direkt in `procedures.geometry/bbox` übernehmen.

6) **Exports**  
   - Excel-Export via `apps/export/to_excel.py` (Platzhalter vorhanden).  
   - Optional Parquet/GeoJSON.

## Checks & Coverage
- Quote OCR vs. Textlayer
- HTTP-Fehler pro Quelle
- Treffer-Count pro Kommune vs. Seed-Liste
- Dedup-Rate (Titel/AGS/Hash)

## Nächste Schritte
- DiPlanung-Spider implementieren (`apps/crawlers/diplanung/spider.py`).
- RIS-Connector (SessionNet) implementieren.
- Gazette-Pattern-Liste verfeinern und Whitelist pro Kommune pflegen.







