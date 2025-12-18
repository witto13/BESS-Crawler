# Gemeindeseeds (Amtlich) – Empfehlung

## Option A: Destatis Gemeindeverzeichnis (empfohlen)
- Quelle: Amtlicher Gemeindeverzeichnis-Auszug (Destatis).
- Felder: Name, Amtlicher Schlüssel (AGS/ARS), Bundesland/Kreis.
- Vorgehen:
  1. Download CSV/XLSX von Destatis.
  2. Ingest in temporäre Tabelle `gv_raw`.
  3. Filter auf Brandenburg (`state = 'BB'` oder `AGS` Prefix `12`).
  4. Insert in `municipality_seed`:
     ```sql
     INSERT INTO municipality_seed (municipality_key, name, county, state, source)
     SELECT ags, name, kreis, 'BB', 'destatis'
     FROM gv_raw
     WHERE LEFT(ags, 2) = '12';
     ```

## Option B: BKG VG250
- Quelle: Verwaltungsgebiete 1:250 000 (VG250), Stand 31.12., BKG.
- Nutzt Geo-Daten + amtliche Schlüssel, ideal für Geo-Dedup.
- Import via `ogr2ogr` oder `shp2pgsql`:
  ```bash
  shp2pgsql -s 25832 -I VG250_GEM.shp public.vg250_gem | psql "$POSTGRES_DSN"
  INSERT INTO municipality_seed (municipality_key, name, county, state, source, metadata)
  SELECT ags, gen, kreis, 'BB', 'vg250', jsonb_build_object('geom', ST_AsText(geom))
  FROM vg250_gem WHERE LEFT(ags, 2) = '12';
  ```

## Hinweise
- AGS/ARS sind stabiler Schlüssel für Dedup.
- Für Audit: Quelle + Timestamp mit abspeichern.
- Ergänze Portal-URLs pro Gemeinde in `seed_sources` (noch anzulegen), z. B. DiPlanung, RIS, Amtsblatt.







