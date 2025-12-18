# Legal Compliance & AGB-Prüfung

## Gecrawlte Websites

### 1. DiPlanung (Brandenburg)
- **URL**: `https://bb.beteiligung.diplanung.de/`
- **Typ**: Öffentliches Beteiligungsportal
- **Status**: ✅ Öffentlich zugänglich, keine Login-Pflicht
- **Robots.txt**: Zu prüfen
- **AGB**: Zu prüfen

### 2. XPlanung/WFS (Brandenburg)
- **URL**: `https://geoportal.brandenburg.de/geodienste/xplanung`
- **URL**: `https://www.geobasis-bb.de/geodaten/wfs/xplanung`
- **Typ**: Geodaten-Services (WFS = Web Feature Service)
- **Status**: ✅ Öffentliche Geodaten, OGC-Standard
- **Robots.txt**: Zu prüfen
- **Lizenz**: Vermutlich Datenlizenz Deutschland (dl-de/by-2-0)

### 3. RIS/SessionNet
- **URL**: Verschiedene Kommunen (z.B. `ris.angermünde.de`, `angermünde.sessionnet.de`)
- **Typ**: Ratsinformationssysteme
- **Status**: ✅ Öffentliche Sitzungsunterlagen
- **Robots.txt**: Je Kommune unterschiedlich
- **AGB**: Je Kommune unterschiedlich

### 4. Amtsblätter/Bekanntmachungen
- **URL**: Verschiedene Kommunen (z.B. `dahme.de/bekanntmachungen`)
- **Typ**: Öffentliche Bekanntmachungen
- **Status**: ✅ Öffentlich zugänglich
- **Robots.txt**: Je Kommune unterschiedlich
- **AGB**: Je Kommune unterschiedlich

## Rechtliche Einschätzung

### ✅ Positiv
1. **Öffentliche Daten**: Alle gecrawlten Daten sind öffentlich zugänglich
2. **Verwaltungsdaten**: Bebauungspläne, Bekanntmachungen sind öffentliche Informationen
3. **Transparenz**: Forensische Nachvollziehbarkeit (source_url, doc_hash)
4. **Keine geschützten Daten**: Keine personenbezogenen Daten (außer Firmennamen in öffentlichen Dokumenten)

### ⚠️ Potenzielle Risiken
1. **Keine robots.txt-Prüfung**: Aktuell nicht implementiert
2. **Kein User-Agent**: Kein identifizierbarer User-Agent gesetzt
3. **Kein Rate-Limiting**: Keine Delays zwischen Requests
4. **Kommerzielle Nutzung**: Daten werden für kommerzielle Zwecke verwendet (M&A, BD)

## Empfohlene Maßnahmen

### 1. Robots.txt respektieren
```python
from urllib.robotparser import RobotFileParser

def can_fetch(url: str) -> bool:
    rp = RobotFileParser()
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    rp.set_url(f"{base_url}/robots.txt")
    try:
        rp.read()
        return rp.can_fetch('*', url)
    except:
        return True  # Wenn robots.txt nicht erreichbar, erlauben
```

### 2. User-Agent setzen
```python
headers = {
    'User-Agent': 'BESS-Forensic-Crawler/1.0 (Research/Transparency; +https://github.com/your-repo)'
}
```

### 3. Rate-Limiting
```python
import time
time.sleep(1)  # Mindestens 1 Sekunde zwischen Requests
```

### 4. Kontaktaufnahme (optional)
- Kontakt mit Portal-Betreibern aufnehmen
- Erlaubnis für Crawling einholen (wenn möglich)

## Rechtliche Beratung

**WICHTIG**: Diese Einschätzung ist keine Rechtsberatung. Bei Unsicherheiten sollte ein Rechtsanwalt konsultiert werden.

## Nächste Schritte

1. ✅ Robots.txt-Prüfung implementieren
2. ✅ User-Agent hinzufügen
3. ✅ Rate-Limiting einbauen
4. ⚠️ AGBs der einzelnen Portale prüfen
5. ⚠️ Bei Unsicherheit: Rechtsberatung einholen






