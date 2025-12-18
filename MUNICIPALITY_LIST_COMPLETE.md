# ✅ Vollständige Brandenburg-Gemeinde-Liste geladen

## Status

**Vollständige Liste aller Brandenburg-Gemeinden wurde in die Datenbank geladen!**

### Statistiken

- **Gesamt:** ~400 Gemeinden
- **Kreisfreie Städte:** 4
- **Landkreise:** 14
- **Gemeinden:** Alle Gemeinden in Brandenburg

### Landkreise

1. **Barnim** - 25 Gemeinden
2. **Dahme-Spreewald** - 37 Gemeinden
3. **Elbe-Elster** - 33 Gemeinden
4. **Havelland** - 26 Gemeinden
5. **Märkisch-Oderland** - 45 Gemeinden
6. **Oberhavel** - 19 Gemeinden
7. **Oberspreewald-Lausitz** - 25 Gemeinden
8. **Oder-Spree** - 38 Gemeinden
9. **Ostprignitz-Ruppin** - 23 Gemeinden
10. **Potsdam-Mittelmark** - 38 Gemeinden
11. **Prignitz** - 26 Gemeinden
12. **Spree-Neiße** - 30 Gemeinden
13. **Teltow-Fläming** - 16 Gemeinden
14. **Uckermark** - 34 Gemeinden

### Kreisfreie Städte

1. **Potsdam**
2. **Brandenburg an der Havel**
3. **Cottbus**
4. **Frankfurt (Oder)**

## Verwendung

Die vollständige Liste ist jetzt in der `municipality_seed` Tabelle gespeichert.

### Scripts

- **Vollständige Liste laden:**
  ```bash
  docker compose exec worker python3 /workspace/scripts/load_brandenburg_municipalities_complete.py
  ```

- **Sample-Liste (alte):**
  ```bash
  docker compose exec worker python3 /workspace/scripts/load_brandenburg_municipalities.py
  ```

### Nächste Schritte

1. ✅ Vollständige Gemeinde-Liste geladen
2. ⏭️ Jobs für alle Gemeinden enqueuen (RIS, Amtsblatt, Municipal Websites)
3. ⏭️ Crawling starten

### Offizielle Quellen (für Verifikation)

- **Destatis Gemeindeverzeichnis:** https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/_inhalt.html
- **BKG VG250:** https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html

---

**Status: ✅ VOLLSTÄNDIG GELADEN**

Alle ~400 Brandenburg-Gemeinden sind jetzt in der Datenbank und können für das Crawling verwendet werden.






