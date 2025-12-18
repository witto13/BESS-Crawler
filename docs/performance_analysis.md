# Performance-Analyse: Warum dauert der Crawl so lange?

## 🔍 Hauptursachen

### 1. **Rate-Limiting (Compliance)**
- **Problem**: 1 Sekunde Delay zwischen **jedem Request**
- **Auswirkung**: 
  - Bei 4.317 Procedures × 1s = **~72 Minuten nur für Delays**
  - Plus Dokument-Downloads (jede Procedure hat mehrere Dokumente)
- **Warum**: Compliance mit robots.txt und AGBs

### 2. **Dokument-Downloads**
- **Problem**: Jede Procedure lädt alle Dokumente herunter
- **Auswirkung**:
  - DiPlanung: ~3-5 Dokumente pro Procedure
  - 4.317 Procedures × 3 Dokumente × 1s Delay = **~3,6 Stunden nur für Dokumente**
- **Warum**: Für Extraktionen (MW, Hektar, Datum, Firmen) benötigt

### 3. **Geobasis-BB: 10 Sekunden Delay**
- **Problem**: robots.txt erfordert `crawl-delay: 10`
- **Auswirkung**: XPlanung-WFS Requests sind **10x langsamer**
- **Warum**: Compliance mit robots.txt

### 4. **Sequenzielle Verarbeitung**
- **Problem**: Procedures werden nacheinander verarbeitet
- **Auswirkung**: Keine Parallelisierung
- **Warum**: Einfacheres Error-Handling, aber langsamer

### 5. **Viele kleine Jobs**
- **Problem**: 422 Jobs in Queue (RIS/Gazette)
- **Auswirkung**: Jeder Job macht nur wenige Requests, aber mit Delays
- **Warum**: Pro Gemeinde ein Job

## 📊 Aktuelle Zahlen

```
Total Procedures: 4.317
Queue: 422 Jobs
Rate: ~1 Procedure/Sekunde (mit Delays)
Geschätzte Zeit: ~1-2 Stunden für verbleibende Jobs
```

## ⚡ Beschleunigungs-Optionen

### Option 1: Rate-Limiting reduzieren (⚠️ Risiko)
- **Aktuell**: 1 Sekunde
- **Vorschlag**: 0.5 Sekunden (nur für nicht-kritische Domains)
- **Risiko**: Könnte gegen robots.txt verstoßen
- **Gewinn**: ~50% schneller

### Option 2: Parallelisierung
- **Aktuell**: 1 Worker, sequenziell
- **Vorschlag**: Mehrere Worker parallel
- **Risiko**: Höhere Server-Last
- **Gewinn**: 2-4x schneller (je nach Worker-Anzahl)

### Option 3: Dokument-Downloads optional
- **Aktuell**: Alle Dokumente werden heruntergeladen
- **Vorschlag**: Nur bei High-Confidence oder auf Anfrage
- **Risiko**: Weniger Extraktionen
- **Gewinn**: ~70% schneller

### Option 4: Batch-Processing
- **Aktuell**: Ein Request pro Procedure
- **Vorschlag**: Mehrere Procedures pro Request (wenn API unterstützt)
- **Risiko**: Nicht alle APIs unterstützen das
- **Gewinn**: 2-5x schneller

## 🎯 Empfohlene Lösung

### Kurzfristig (Schnell)
1. **Mehrere Worker**: 2-3 Worker parallel
2. **Dokument-Downloads optimieren**: Nur bei High-Score

### Langfristig (Optimal)
1. **Intelligentes Rate-Limiting**: Domain-spezifisch
2. **Parallelisierung**: Mehrere Worker + Threading
3. **Caching**: Dokumente nicht doppelt herunterladen

## ⏱️ Geschätzte Zeit

### Aktuell (mit Compliance)
- **DiPlanung**: ~1-2 Stunden (mit Dokumenten)
- **RIS/Gazette**: ~30-60 Minuten (422 Jobs × ~5s pro Job)
- **XPlanung**: ~10-20 Minuten (mit 10s Delay)
- **Gesamt**: ~2-4 Stunden

### Mit Optimierungen
- **Mit 3 Workern**: ~40-80 Minuten
- **Ohne Dokument-Downloads**: ~20-40 Minuten
- **Kombiniert**: ~15-30 Minuten

## 💡 Empfehlung

**Für jetzt**: Crawl laufen lassen (ist fast fertig - 422 Jobs = ~30-60 Minuten)

**Für zukünftige Crawls**: 
1. Mehrere Worker aktivieren
2. Dokument-Downloads optimieren (nur bei High-Score)
3. Intelligentes Rate-Limiting






