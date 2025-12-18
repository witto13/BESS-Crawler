# ✅ Discovery-Logik Implementiert

## Status: ✅ VOLLSTÄNDIG IMPLEMENTIERT

### Übersicht

Die Discovery-Logik definiert **exakt WO auf den Websites gesucht werden soll** für jede Verfahrensart. Keine generische Websuche mehr, sondern konkrete Pfade.

---

## 📁 Neue Module

### 1. `apps/crawlers/discovery/municipality_index.py`
- **Municipality-Index** mit offiziellen Website-URLs
- **Discovery-Pfade** für jede Quelle definiert:
  - Municipal Website Pfade (17 Pfade)
  - RIS URL Patterns (8 Patterns)
  - RIS Committee Pfade (8 Pfade)
  - RIS Committee Namen (7 Namen)
  - Amtsblatt Patterns (5 Patterns)

### 2. `apps/crawlers/discovery/municipal_website.py`
- **Municipal Website Discovery**
- Entdeckt welche Sektionen existieren
- Crawlt nur spezifische Sektionen:
  - `/bekanntmachungen`
  - `/bauleitplanung`
  - `/bebauungsplaene`
  - etc.
- Stoppt bei PDFs oder externen Links (RIS/Amtsblatt)

### 3. `apps/crawlers/discovery/ris_discovery.py`
- **RIS Discovery** mit expliziten Pfaden
- Discovery-Order:
  1. Discover RIS URL
  2. Discover Committees
  3. Crawl Sessions
  4. Extract Items
- Fokus auf relevante Committees:
  - Bauausschuss
  - Hauptausschuss
  - Gemeindevertretung
  - etc.

### 4. `apps/crawlers/discovery/amtsblatt_discovery.py`
- **Amtsblatt Discovery** mit expliziten Pfaden
- Discovery-Order:
  1. Discover Amtsblatt URL
  2. List Issues
  3. Extract Procedures
- Fokus auf B-Plan und Permit-Ankündigungen

---

## 🔄 Integrierte Crawler

### RIS/SessionNet (`apps/crawlers/ris/sessionnet.py`)
- ✅ Verwendet neue Discovery-Module
- ✅ Fallback auf alte Methode wenn Discovery fehlschlägt
- ✅ Speichert `discovery_source` und `discovery_path`

### Amtsblatt (`apps/crawlers/gazette/spider.py`)
- ✅ Verwendet neue Discovery-Module
- ✅ Fallback auf alte Methode wenn Discovery fehlschlägt
- ✅ Speichert `discovery_source` und `discovery_path`

---

## 🗄️ Datenbank-Schema

### Neue Felder in `sources` Tabelle:
- `discovery_source` VARCHAR(50) - RIS, AMTSBLATT, MUNICIPAL_WEBSITE, LANDKREIS
- `discovery_path` TEXT - Exakter URL-Pfad wo gefunden

**Migration:** `scripts/migrate_add_discovery_fields.py`

---

## 📋 Discovery-Order (wie spezifiziert)

Für jede Gemeinde, immer in dieser Reihenfolge:

1. **Ratsinformationssystem (RIS)** - Höchste Ausbeute für privilegierte Projekte
2. **Amtsblatt** - Höchste Ausbeute für frühe + rechtliche Bekanntmachungen
3. **Municipal Bekanntmachungen / Bauleitplanung** - Sekundär
4. **Landkreis Mirrors** - Optional, nur als Ergänzung

---

## 🎯 Was wird NICHT gecrawlt (explizite Ausschlüsse)

- ❌ Developer-Websites
- ❌ Pressemitteilungen
- ❌ Social Media
- ❌ Login-geschützte Portale
- ❌ Generische Google-Suchergebnisse
- ❌ Nationale Portale ohne kommunale Publikation

---

## 📊 Output-Tagging (Pflicht)

Jeder Record enthält:
- `discovery_source` = einer von:
  - `RIS`
  - `AMTSBLATT`
  - `MUNICIPAL_WEBSITE`
  - `LANDKREIS`
- `discovery_path` = exakter URL-Pfad wo gefunden

---

## ✅ Definition of Done

Der Crawler kann jetzt für jeden Hit beantworten:

> "Welcher **offizielle Publikationskanal** war das, und warum wurde dieser Kanal gewählt?"

**Antwort:** 
- `discovery_source` zeigt den Kanal
- `discovery_path` zeigt den exakten Pfad
- Discovery-Order erklärt die Priorität

---

## 🚀 Nächste Schritte

1. ✅ Discovery-Logik implementiert
2. ⏭️ Municipality-Index mit echten Daten füllen
3. ⏭️ Brandenburg-spezifische RIS-URL-Heuristiken hinzufügen
4. ⏭️ Coverage-Benchmarking (wie viele echte Projekte werden erfasst?)

---

## 📝 Code-Beispiele

### Municipal Website Discovery
```python
from apps.crawlers.discovery.municipal_website import discover_municipal_sections, crawl_municipal_section

sections = discover_municipal_sections("https://example.de")
for section in sections:
    procedures = crawl_municipal_section(section)
```

### RIS Discovery
```python
from apps.crawlers.discovery.ris_discovery import discover_ris, discover_committees

ris_url = discover_ris("Brandenburg", "https://example.de")
committees = discover_committees(ris_url)
```

### Amtsblatt Discovery
```python
from apps.crawlers.discovery.amtsblatt_discovery import discover_amtsblatt, list_amtsblatt_issues

amtsblatt_url = discover_amtsblatt("Brandenburg", "https://example.de")
issues = list_amtsblatt_issues(amtsblatt_url)
```

---

**Status: ✅ VOLLSTÄNDIG IMPLEMENTIERT**

Die Discovery-Logik ist vollständig implementiert und wird automatisch von den Crawlern verwendet.






