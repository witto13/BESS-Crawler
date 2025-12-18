# Änderungen - PV & BESS Scanning

## ✅ Implementiert (12.12.2024)

### 1. **Scoring erweitert: PV + BESS**
- **Vorher**: Nur BESS mit hoher Priorität, Solarparks nur mit Speicher
- **Jetzt**: 
  - BESS: 10 Punkte (wie vorher)
  - **PV/Solarparks: 5 Punkte** (auch ohne Speicher relevant für MS/HS)
  - Photovoltaik, PV-Anlagen, Solarparks werden jetzt erkannt
  - Kombinationen (Solar + Speicher) bekommen Bonus +6

### 2. **Extraktionen aus Titeln**
- **Vorher**: Extraktionen nur aus heruntergeladenen Dokumenten
- **Jetzt**: Extraktionen auch aus **Titeln** (MW/MWh, Hektar, Datum, Firmen)
- → Mehr Procedures haben jetzt Extraktionen, auch ohne Dokumente

### 3. **Gemeinde-Liste erweitert**
- **Vorher**: 40 Gemeinden
- **Jetzt**: **80 Gemeinden** (inkl. Bliesdorf - Batteriespeicheranlage Metzdorf)
- Alle Gemeinden haben jetzt RIS/Gazette-Jobs

### 4. **Aktiver Crawl**
- **1102 Procedures** werden gerade von DiPlanung verarbeitet
- **487 Jobs** in der Queue (RIS/Gazette/XPlanung)
- Worker läuft und verarbeitet kontinuierlich

## 📊 Erwartete Ergebnisse

Nach dem Crawl sollten mehr Procedures haben:
- ✅ **PV/Solarparks** erkannt (nicht nur BESS)
- ✅ **Extraktionen aus Titeln** (auch ohne Dokumente)
- ✅ **Bliesdorf/Metzdorf** gescannt
- ✅ **Mehr Gemeinden** abgedeckt

## 🔄 Nächste Schritte

1. **Warten auf Crawl-Abschluss** (~1102 Procedures werden verarbeitet)
2. **Export prüfen**: `python3 scripts/export_to_excel.py`
3. **Optional**: Vollständige Gemeinde-Liste von Destatis/BKG laden

## 📝 Wichtige Dateien

- `apps/extract/rules_bess.py` - Scoring für PV + BESS
- `apps/worker/main.py` - Extraktionen aus Titeln
- `scripts/load_brandenburg_municipalities.py` - 80 Gemeinden (inkl. Bliesdorf)






