# Improved BESS Classifier - Dokumentation

## Übersicht

Das verbesserte Klassifizierungssystem implementiert ein umfassendes Regelwerk für die Erkennung von BESS-relevanten Verfahren in Brandenburg. Es basiert auf deterministischen Regeln mit optionalem LLM-Fallback.

## Implementierte Komponenten

### 1. Text-Normalisierung (`apps/extract/normalize.py`)
- Lowercase-Konvertierung
- Umlaut-Normalisierung (ä->ae, ö->oe, ü->ue, ß->ss)
- Whitespace-Kollabierung
- Beibehaltung des Originaltexts für Evidence-Snippets

### 2. Keyword-Dictionaries (`apps/extract/keywords_bess.py`)
- **PLANNING_TERMS_STRONG**: B-Plan/Bauleitplanung Signale
- **PLANNING_STEP_TERMS**: Verfahrensschritte (Aufstellung, Auslegung, Satzung)
- **PERMIT_TERMS_STRONG**: Genehmigungsverfahren (Bauvorbescheid, Baugenehmigung)
- **BESS_TERMS_EXPLICIT**: Explizite BESS-Keywords
- **BESS_TERMS_CONTAINER_GRID**: Container/Grid-Infrastruktur
- **ENERGY_CONTEXT_TERMS**: Energie-Kontext (PV, Wind, etc.)
- **ZONING_TERMS**: Zonierung/Nutzung
- **NEGATIVE_STORAGE_TERMS**: False-Positive-Suppression

### 3. Klassifizierer (`apps/extract/classifier_bess.py`)
- **is_candidate()**: Schneller Prefilter
- **classify_relevance()**: Hauptklassifizierung
- **tag_procedure_type()**: Verfahrenstyp-Tagging
- **tag_legal_basis()**: Rechtsgrundlage-Tagging
- **tag_project_components()**: Projektkomponenten-Tagging
- **calculate_confidence()**: Confidence-Scoring (0-1)

### 4. Integration (`apps/extract/rules_bess.py`)
- Verbesserter `score()` mit `use_improved=True` Flag
- Fallback auf altes System wenn `use_improved=False`
- Integration in Worker (`apps/worker/main.py`)

## Klassifizierungsregeln

### Rule R1: Explizites BESS + Verfahren
- BESS_TERMS_EXPLICIT UND Verfahrens-Terme → RELEVANT

### Rule R2: Explizites BESS im Titel (ab 2023)
- Titel enthält "Batteriespeicher" oder "Energiespeicher" → RELEVANT

### Rule R3: Ambiguöses "Speicher" mit starkem Grid-Kontext
- "Speicher" + 2+ Grid-Terme + Verfahrens-Terme + keine Negativ-Terme → RELEVANT

## Confidence-Scoring

Additive Punkte:
- **BESS-Explizitheit**: +0.55 (batteriespeicher/energiespeicher/stromspeicher)
- **Verfahrens-Stärke**: +0.25 (spezifische Schritte)
- **Grid-Infrastruktur**: +0.10 (Umspannwerk, Netzanschluss, etc.)

Penalties:
- **False-Positive**: -0.60 (Negativ-Terme ohne explizites BESS)
- **Ambiguös**: -0.25 (nur "Speicher" ohne Grid-Terme)
- **Datum fehlt**: -0.15

## Verfahrenstypen

### B-Plan
- `BPLAN_AUFSTELLUNG`: Aufstellungsbeschluss
- `BPLAN_FRUEHZEITIG_3_1`: Frühzeitige Beteiligung
- `BPLAN_AUSLEGUNG_3_2`: Öffentliche Auslegung
- `BPLAN_SATZUNG`: Satzungsbeschluss
- `BPLAN_OTHER`: Sonstige B-Plan-Verfahren

### Genehmigungen
- `PERMIT_BAUVORBESCHEID`: Bauvorbescheid
- `PERMIT_BAUGENEHMIGUNG`: Baugenehmigung
- `PERMIT_36_EINVERNEHMEN`: Gemeindliches Einvernehmen §36
- `PERMIT_OTHER`: Sonstige Genehmigungen

## Projektkomponenten

- `PV+BESS`: Photovoltaik + Batteriespeicher
- `WIND+BESS`: Windenergie + Batteriespeicher
- `BESS_ONLY`: Nur Batteriespeicher
- `OTHER/UNCLEAR`: Unklar/Sonstiges

## Output-Schema

Jedes Ergebnis enthält:
- `is_relevant`: Boolean
- `procedure_type`: Verfahrenstyp
- `legal_basis`: Rechtsgrundlage (§35/§34/§36)
- `project_components`: Projektkomponenten
- `confidence_score`: 0-1
- `ambiguity_flag`: Boolean
- `review_recommended`: Boolean
- `evidence_snippets`: Array von Text-Snippets

## Datenbank-Schema

Neue Felder in `procedures` Tabelle:
- `procedure_type VARCHAR(50)`
- `legal_basis VARCHAR(20)`
- `project_components VARCHAR(50)`
- `ambiguity_flag BOOLEAN`
- `review_recommended BOOLEAN`
- `site_location_raw TEXT`
- `evidence_snippets JSONB`

## Tests

Unit-Tests in `tests/test_classifier_bess.py`:
- ✅ B-Plan Aufstellungsbeschluss
- ✅ Bauvorbescheid
- ✅ PV+BESS kombiniert
- ✅ False-Positive (Wasserspeicher)
- ✅ Ambiguöses "Speicher" mit Grid-Kontext
- ✅ §36 Einvernehmen

## Verwendung

```python
from apps.extract.classifier_bess import classify_relevance
from datetime import datetime

text = "Aufstellungsbeschluss für Batteriespeicheranlage..."
title = "Bebauungsplan Batteriespeicher"
result = classify_relevance(text, title, date=datetime(2024, 1, 1))

if result["is_relevant"]:
    print(f"Verfahrenstyp: {result['procedure_type']}")
    print(f"Confidence: {result['confidence_score']}")
```

## Migration

Schema-Migration ausführen:
```bash
docker compose exec worker python3 /workspace/scripts/migrate_add_classifier_fields.py
```

## Nächste Schritte

1. ✅ Klassifizierer implementiert
2. ✅ Tests erstellt
3. ⚠️ Schema-Migration ausführen
4. ⚠️ Worker-Integration testen
5. ⚠️ Optional: LLM-Fallback für `review_recommended=True`






