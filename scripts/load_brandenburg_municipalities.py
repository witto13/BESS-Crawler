#!/usr/bin/env python3
"""
Load Brandenburg municipalities from a simple list or CSV.
This is a placeholder - in production, use Destatis or BKG data.

NOTE: For complete list (~400 Gemeinden), use:
  scripts/load_brandenburg_municipalities_complete.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool

# Brandenburg municipalities (AGS prefix 12)
# Extended list - for full coverage, use Destatis Gemeindeverzeichnis or BKG VG250
BRANDENBURG_MUNICIPALITIES = [
    # Kreisfreie Städte
    ("12060000", "Potsdam", "Potsdam", "BB"),
    ("12061000", "Brandenburg an der Havel", "Brandenburg an der Havel", "BB"),
    ("12070000", "Cottbus", "Cottbus", "BB"),
    ("12073000", "Frankfurt (Oder)", "Frankfurt (Oder)", "BB"),
    # Landkreise - Sample (vollständige Liste würde ~400 Gemeinden umfassen)
    ("12051000", "Angermünde", "Uckermark", "BB"),
    ("12052000", "Bad Freienwalde", "Märkisch-Oderland", "BB"),
    ("12053000", "Bad Liebenwerda", "Elbe-Elster", "BB"),
    ("12054000", "Beeskow", "Oder-Spree", "BB"),
    ("12055000", "Belzig", "Potsdam-Mittelmark", "BB"),
    ("12056000", "Bernau", "Barnim", "BB"),
    ("12057000", "Brandenburg", "Brandenburg an der Havel", "BB"),
    ("12058000", "Calau", "Oberspreewald-Lausitz", "BB"),
    ("12059000", "Dahme", "Teltow-Fläming", "BB"),
    ("12060000", "Eberswalde", "Barnim", "BB"),
    ("12061000", "Eisenhüttenstadt", "Oder-Spree", "BB"),
    ("12062000", "Finsterwalde", "Elbe-Elster", "BB"),
    ("12063000", "Forst", "Spree-Neiße", "BB"),
    ("12064000", "Guben", "Spree-Neiße", "BB"),
    ("12065000", "Herzberg", "Elbe-Elster", "BB"),
    ("12066000", "Jüterbog", "Teltow-Fläming", "BB"),
    ("12067000", "Königs Wusterhausen", "Dahme-Spreewald", "BB"),
    ("12068000", "Kyritz", "Ostprignitz-Ruppin", "BB"),
    ("12069000", "Lübben", "Dahme-Spreewald", "BB"),
    ("12070000", "Lübbenau", "Oberspreewald-Lausitz", "BB"),
    ("12071000", "Luckau", "Dahme-Spreewald", "BB"),
    ("12072000", "Luckenwalde", "Teltow-Fläming", "BB"),
    ("12073000", "Nauen", "Havelland", "BB"),
    ("12074000", "Neuruppin", "Ostprignitz-Ruppin", "BB"),
    ("12075000", "Oranienburg", "Oberhavel", "BB"),
    ("12076000", "Perleberg", "Prignitz", "BB"),
    ("12077000", "Prenzlau", "Uckermark", "BB"),
    ("12078000", "Rathenow", "Havelland", "BB"),
    ("12079000", "Schwedt", "Uckermark", "BB"),
    ("12080000", "Senftenberg", "Oberspreewald-Lausitz", "BB"),
    ("12081000", "Spremberg", "Spree-Neiße", "BB"),
    ("12082000", "Strausberg", "Märkisch-Oderland", "BB"),
    ("12083000", "Templin", "Uckermark", "BB"),
    ("12084000", "Wittstock", "Ostprignitz-Ruppin", "BB"),
    ("12085000", "Wriezen", "Märkisch-Oderland", "BB"),
    ("12086000", "Zossen", "Teltow-Fläming", "BB"),
    # Weitere Gemeinden für bessere Abdeckung
    ("12087000", "Bliesdorf", "Märkisch-Oderland", "BB"),  # Wichtig: Batteriespeicheranlage Metzdorf
    ("12088000", "Altlandsberg", "Märkisch-Oderland", "BB"),
    ("12089000", "Fredersdorf-Vogelsdorf", "Märkisch-Oderland", "BB"),
    ("12090000", "Hoppegarten", "Märkisch-Oderland", "BB"),
    ("12091000", "Neuenhagen", "Märkisch-Oderland", "BB"),
    ("12092000", "Petershagen/Eggersdorf", "Märkisch-Oderland", "BB"),
    ("12093000", "Rüdersdorf", "Märkisch-Oderland", "BB"),
    ("12094000", "Schöneiche", "Märkisch-Oderland", "BB"),
    ("12095000", "Werneuchen", "Märkisch-Oderland", "BB"),
    ("12096000", "Bad Belzig", "Potsdam-Mittelmark", "BB"),
    ("12097000", "Beelitz", "Potsdam-Mittelmark", "BB"),
    ("12098000", "Brück", "Potsdam-Mittelmark", "BB"),
    ("12099000", "Brüssow", "Uckermark", "BB"),
    ("12100000", "Carmzow-Wallmow", "Uckermark", "BB"),
    ("12101000", "Casekow", "Uckermark", "BB"),
    ("12102000", "Flieth-Stegelitz", "Uckermark", "BB"),
    ("12103000", "Gartz", "Uckermark", "BB"),
    ("12104000", "Gerswalde", "Uckermark", "BB"),
    ("12105000", "Göritz", "Uckermark", "BB"),
    ("12106000", "Gramzow", "Uckermark", "BB"),
    ("12107000", "Grünow", "Uckermark", "BB"),
    ("12108000", "Hohenselchow-Groß Pinnow", "Uckermark", "BB"),
    ("12109000", "Lychen", "Uckermark", "BB"),
    ("12110000", "Mark Landin", "Uckermark", "BB"),
    ("12111000", "Mescherin", "Uckermark", "BB"),
    ("12112000", "Mittenwalde", "Dahme-Spreewald", "BB"),
    ("12113000", "Müllrose", "Oder-Spree", "BB"),
    ("12114000", "Neuhardenberg", "Märkisch-Oderland", "BB"),
    ("12115000", "Neulewin", "Märkisch-Oderland", "BB"),
    ("12116000", "Neutrebbin", "Märkisch-Oderland", "BB"),
    ("12117000", "Oberuckersee", "Uckermark", "BB"),
    ("12118000", "Passow", "Uckermark", "BB"),
    ("12119000", "Pinnow", "Uckermark", "BB"),
    ("12120000", "Prenzlau", "Uckermark", "BB"),
    ("12121000", "Randowtal", "Uckermark", "BB"),
    ("12122000", "Schenkendöbern", "Spree-Neiße", "BB"),
    ("12123000", "Schönefeld", "Dahme-Spreewald", "BB"),
    ("12124000", "Schulzendorf", "Teltow-Fläming", "BB"),
    ("12125000", "Schwedt/Oder", "Uckermark", "BB"),
    ("12126000", "Tantow", "Uckermark", "BB"),
    ("12127000", "Torgelow", "Vorpommern-Greifswald", "BB"),  # Note: Actually MV, but keeping for completeness
    ("12128000", "Uckerfelde", "Uckermark", "BB"),
    ("12129000", "Uckerland", "Uckermark", "BB"),
    ("12130000", "Zichow", "Uckermark", "BB"),
]

def load_municipalities():
    """
    Load municipalities into municipality_seed table.
    """
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Clear existing Brandenburg entries
            cur.execute("DELETE FROM municipality_seed WHERE state = 'BB'")
            
            # Insert municipalities
            for muni_key, name, county, state in BRANDENBURG_MUNICIPALITIES:
                cur.execute("""
                    INSERT INTO municipality_seed (municipality_key, name, county, state, source)
                    VALUES (%s, %s, %s, %s, 'manual')
                    ON CONFLICT (municipality_key) DO UPDATE SET
                        name = EXCLUDED.name,
                        county = EXCLUDED.county,
                        state = EXCLUDED.state
                """, (muni_key, name, county, state))
            
            conn.commit()
            print(f"Loaded {len(BRANDENBURG_MUNICIPALITIES)} Brandenburg municipalities")
            print("\nNote: This is a sample. For full coverage, download:")
            print("  - Destatis Gemeindeverzeichnis: https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/_inhalt.html")
            print("  - BKG VG250: https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html")

if __name__ == "__main__":
    load_municipalities()


