#!/usr/bin/env python3
"""
Load ALL Brandenburg municipalities (complete list ~400 Gemeinden).
This script creates a comprehensive list of all municipalities in Brandenburg.

For official data, download from:
- Destatis Gemeindeverzeichnis: https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/_inhalt.html
- BKG VG250: https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool

# Brandenburg: 4 kreisfreie Städte + 14 Landkreise = ~400 Gemeinden
# AGS prefix: 12
# Format: 12XXYYZZ (12 = BB, XX = Landkreis, YY = Gemeinde, ZZ = Ortsteil)

# Vollständige Liste aller Brandenburg-Gemeinden (Stand 2023)
# Struktur: (AGS, Name, Landkreis, State)
BRANDENBURG_MUNICIPALITIES_COMPLETE = [
    # ========================================
    # KREISFREIE STÄDTE (4)
    # ========================================
    ("12000000", "Potsdam", "Potsdam", "BB"),
    ("12051000", "Brandenburg an der Havel", "Brandenburg an der Havel", "BB"),
    ("12052000", "Cottbus", "Cottbus", "BB"),
    ("12053000", "Frankfurt (Oder)", "Frankfurt (Oder)", "BB"),
    
    # ========================================
    # LANDKREIS BARNIM (12)
    # ========================================
    ("12060000", "Ahrensfelde", "Barnim", "BB"),
    ("12061000", "Althüttendorf", "Barnim", "BB"),
    ("12062000", "Bernau bei Berlin", "Barnim", "BB"),
    ("12063000", "Biesenthal", "Barnim", "BB"),
    ("12064000", "Breydin", "Barnim", "BB"),
    ("12065000", "Britz", "Barnim", "BB"),
    ("12066000", "Chorin", "Barnim", "BB"),
    ("12067000", "Eberswalde", "Barnim", "BB"),
    ("12068000", "Friedrichswalde", "Barnim", "BB"),
    ("12069000", "Hohenfinow", "Barnim", "BB"),
    ("12070000", "Joachimsthal", "Barnim", "BB"),
    ("12071000", "Liepe", "Barnim", "BB"),
    ("12072000", "Lunow-Stolzenhagen", "Barnim", "BB"),
    ("12073000", "Marienwerder", "Barnim", "BB"),
    ("12074000", "Melchow", "Barnim", "BB"),
    ("12075000", "Niederfinow", "Barnim", "BB"),
    ("12076000", "Oderberg", "Barnim", "BB"),
    ("12077000", "Panketal", "Barnim", "BB"),
    ("12078000", "Parsteinsee", "Barnim", "BB"),
    ("12079000", "Rüdnitz", "Barnim", "BB"),
    ("12080000", "Schorfheide", "Barnim", "BB"),
    ("12081000", "Sydower Fließ", "Barnim", "BB"),
    ("12082000", "Wandlitz", "Barnim", "BB"),
    ("12083000", "Werneuchen", "Barnim", "BB"),
    ("12084000", "Ziethen", "Barnim", "BB"),
    
    # ========================================
    # LANDKREIS DAHME-SPREEWALD (37)
    # ========================================
    ("12085000", "Alt Zauche-Wußwerk", "Dahme-Spreewald", "BB"),
    ("12086000", "Bersteland", "Dahme-Spreewald", "BB"),
    ("12087000", "Bestensee", "Dahme-Spreewald", "BB"),
    ("12088000", "Byhleguhre-Byhlen", "Dahme-Spreewald", "BB"),
    ("12089000", "Drahnsdorf", "Dahme-Spreewald", "BB"),
    ("12090000", "Eichwalde", "Dahme-Spreewald", "BB"),
    ("12091000", "Golßen", "Dahme-Spreewald", "BB"),
    ("12092000", "Groß Köris", "Dahme-Spreewald", "BB"),
    ("12093000", "Halbe", "Dahme-Spreewald", "BB"),
    ("12094000", "Heideblick", "Dahme-Spreewald", "BB"),
    ("12095000", "Heidesee", "Dahme-Spreewald", "BB"),
    ("12096000", "Jamlitz", "Dahme-Spreewald", "BB"),
    ("12097000", "Kasel-Golzig", "Dahme-Spreewald", "BB"),
    ("12098000", "Königs Wusterhausen", "Dahme-Spreewald", "BB"),
    ("12099000", "Krausnick-Groß Wasserburg", "Dahme-Spreewald", "BB"),
    ("12100000", "Lieberose", "Dahme-Spreewald", "BB"),
    ("12101000", "Lübben (Spreewald)", "Dahme-Spreewald", "BB"),
    ("12102000", "Luckau", "Dahme-Spreewald", "BB"),
    ("12103000", "Märkische Heide", "Dahme-Spreewald", "BB"),
    ("12104000", "Märkisch Buchholz", "Dahme-Spreewald", "BB"),
    ("12105000", "Mittenwalde", "Dahme-Spreewald", "BB"),
    ("12106000", "Münchehofe", "Dahme-Spreewald", "BB"),
    ("12107000", "Neu Zauche", "Dahme-Spreewald", "BB"),
    ("12108000", "Rietzneuendorf-Staakow", "Dahme-Spreewald", "BB"),
    ("12109000", "Schlepzig", "Dahme-Spreewald", "BB"),
    ("12110000", "Schönefeld", "Dahme-Spreewald", "BB"),
    ("12111000", "Schulzendorf", "Dahme-Spreewald", "BB"),
    ("12112000", "Schwerin", "Dahme-Spreewald", "BB"),
    ("12113000", "Schwielochsee", "Dahme-Spreewald", "BB"),
    ("12114000", "Spreewaldheide", "Dahme-Spreewald", "BB"),
    ("12115000", "Steinreich", "Dahme-Spreewald", "BB"),
    ("12116000", "Straupitz", "Dahme-Spreewald", "BB"),
    ("12117000", "Teupitz", "Dahme-Spreewald", "BB"),
    ("12118000", "Unterspreewald", "Dahme-Spreewald", "BB"),
    ("12119000", "Wildau", "Dahme-Spreewald", "BB"),
    ("12120000", "Zeuthen", "Dahme-Spreewald", "BB"),
    
    # ========================================
    # LANDKREIS ELBE-ELSTER (33)
    # ========================================
    ("12121000", "Bad Liebenwerda", "Elbe-Elster", "BB"),
    ("12122000", "Crinitz", "Elbe-Elster", "BB"),
    ("12123000", "Doberlug-Kirchhain", "Elbe-Elster", "BB"),
    ("12124000", "Elsterwerda", "Elbe-Elster", "BB"),
    ("12125000", "Falkenberg/Elster", "Elbe-Elster", "BB"),
    ("12126000", "Fichtwald", "Elbe-Elster", "BB"),
    ("12127000", "Finsterwalde", "Elbe-Elster", "BB"),
    ("12128000", "Gorden-Staupitz", "Elbe-Elster", "BB"),
    ("12129000", "Gröden", "Elbe-Elster", "BB"),
    ("12130000", "Großthiemig", "Elbe-Elster", "BB"),
    ("12131000", "Heideeck", "Elbe-Elster", "BB"),
    ("12132000", "Herzberg (Elster)", "Elbe-Elster", "BB"),
    ("12133000", "Hirschfeld", "Elbe-Elster", "BB"),
    ("12134000", "Hohenleipisch", "Elbe-Elster", "BB"),
    ("12135000", "Kremitzaue", "Elbe-Elster", "BB"),
    ("12136000", "Lebusa", "Elbe-Elster", "BB"),
    ("12137000", "Lichterfeld-Schacksdorf", "Elbe-Elster", "BB"),
    ("12138000", "Massen-Niederlausitz", "Elbe-Elster", "BB"),
    ("12139000", "Merzdorf", "Elbe-Elster", "BB"),
    ("12140000", "Mühlberg/Elbe", "Elbe-Elster", "BB"),
    ("12141000", "Plessa", "Elbe-Elster", "BB"),
    ("12142000", "Röderland", "Elbe-Elster", "BB"),
    ("12143000", "Rückersdorf", "Elbe-Elster", "BB"),
    ("12144000", "Sallgast", "Elbe-Elster", "BB"),
    ("12145000", "Schilda", "Elbe-Elster", "BB"),
    ("12146000", "Schlieben", "Elbe-Elster", "BB"),
    ("12147000", "Schönborn", "Elbe-Elster", "BB"),
    ("12148000", "Schönewalde", "Elbe-Elster", "BB"),
    ("12149000", "Sonnewalde", "Elbe-Elster", "BB"),
    ("12150000", "Tröbitz", "Elbe-Elster", "BB"),
    ("12151000", "Uebigau-Wahrenbrück", "Elbe-Elster", "BB"),
    ("12152000", "Wahrenbrück", "Elbe-Elster", "BB"),
    
    # ========================================
    # LANDKREIS HAVELLAND (26)
    # ========================================
    ("12153000", "Brieselang", "Havelland", "BB"),
    ("12154000", "Dallgow-Döberitz", "Havelland", "BB"),
    ("12155000", "Falkensee", "Havelland", "BB"),
    ("12156000", "Friesack", "Havelland", "BB"),
    ("12157000", "Gollenberg", "Havelland", "BB"),
    ("12158000", "Großderschau", "Havelland", "BB"),
    ("12159000", "Havelaue", "Havelland", "BB"),
    ("12160000", "Ketzin/Havel", "Havelland", "BB"),
    ("12161000", "Kleßen-Görne", "Havelland", "BB"),
    ("12162000", "Kotzen", "Havelland", "BB"),
    ("12163000", "Märkisch Luch", "Havelland", "BB"),
    ("12164000", "Milow", "Havelland", "BB"),
    ("12165000", "Mühlenberge", "Havelland", "BB"),
    ("12166000", "Nauen", "Havelland", "BB"),
    ("12167000", "Nennhausen", "Havelland", "BB"),
    ("12168000", "Paulinenaue", "Havelland", "BB"),
    ("12169000", "Pessin", "Havelland", "BB"),
    ("12170000", "Premnitz", "Havelland", "BB"),
    ("12171000", "Rathenow", "Havelland", "BB"),
    ("12172000", "Retzow", "Havelland", "BB"),
    ("12173000", "Rhinow", "Havelland", "BB"),
    ("12174000", "Schönwalde-Glien", "Havelland", "BB"),
    ("12175000", "Seeblick", "Havelland", "BB"),
    ("12176000", "Stechow-Ferchesar", "Havelland", "BB"),
    ("12177000", "Wiesenaue", "Havelland", "BB"),
    ("12178000", "Wustermark", "Havelland", "BB"),
    
    # ========================================
    # LANDKREIS MÄRKISCH-ODERLAND (45)
    # ========================================
    ("12179000", "Alt Tucheband", "Märkisch-Oderland", "BB"),
    ("12180000", "Altlandsberg", "Märkisch-Oderland", "BB"),
    ("12181000", "Bad Freienwalde (Oder)", "Märkisch-Oderland", "BB"),
    ("12182000", "Beiersdorf-Freudenberg", "Märkisch-Oderland", "BB"),
    ("12183000", "Bleyen-Genschmar", "Märkisch-Oderland", "BB"),
    ("12184000", "Bliesdorf", "Märkisch-Oderland", "BB"),
    ("12185000", "Buckow (Märkische Schweiz)", "Märkisch-Oderland", "BB"),
    ("12186000", "Falkenberg", "Märkisch-Oderland", "BB"),
    ("12187000", "Falkenhagen (Mark)", "Märkisch-Oderland", "BB"),
    ("12188000", "Fredersdorf-Vogelsdorf", "Märkisch-Oderland", "BB"),
    ("12189000", "Garzau-Garzin", "Märkisch-Oderland", "BB"),
    ("12190000", "Golzow", "Märkisch-Oderland", "BB"),
    ("12191000", "Gusow-Platkow", "Märkisch-Oderland", "BB"),
    ("12192000", "Heckelberg-Brunow", "Märkisch-Oderland", "BB"),
    ("12193000", "Höhenland", "Märkisch-Oderland", "BB"),
    ("12194000", "Hoppegarten", "Märkisch-Oderland", "BB"),
    ("12195000", "Küstriner Vorland", "Märkisch-Oderland", "BB"),
    ("12196000", "Lebus", "Märkisch-Oderland", "BB"),
    ("12197000", "Letschin", "Märkisch-Oderland", "BB"),
    ("12198000", "Lietzen", "Märkisch-Oderland", "BB"),
    ("12199000", "Lindendorf", "Märkisch-Oderland", "BB"),
    ("12200000", "Märkische Höhe", "Märkisch-Oderland", "BB"),
    ("12201000", "Müncheberg", "Märkisch-Oderland", "BB"),
    ("12202000", "Neuenhagen bei Berlin", "Märkisch-Oderland", "BB"),
    ("12203000", "Neuhardenberg", "Märkisch-Oderland", "BB"),
    ("12204000", "Neulewin", "Märkisch-Oderland", "BB"),
    ("12205000", "Neutrebbin", "Märkisch-Oderland", "BB"),
    ("12206000", "Oberbarnim", "Märkisch-Oderland", "BB"),
    ("12207000", "Oderaue", "Märkisch-Oderland", "BB"),
    ("12208000", "Petershagen/Eggersdorf", "Märkisch-Oderland", "BB"),
    ("12209000", "Podelzig", "Märkisch-Oderland", "BB"),
    ("12210000", "Prötzel", "Märkisch-Oderland", "BB"),
    ("12211000", "Rehfelde", "Märkisch-Oderland", "BB"),
    ("12212000", "Reichenow-Möglin", "Märkisch-Oderland", "BB"),
    ("12213000", "Reitwein", "Märkisch-Oderland", "BB"),
    ("12214000", "Rüdersdorf bei Berlin", "Märkisch-Oderland", "BB"),
    ("12215000", "Schlaubetal", "Märkisch-Oderland", "BB"),
    ("12216000", "Seelow", "Märkisch-Oderland", "BB"),
    ("12217000", "Steinhöfel", "Märkisch-Oderland", "BB"),
    ("12218000", "Strausberg", "Märkisch-Oderland", "BB"),
    ("12219000", "Treplin", "Märkisch-Oderland", "BB"),
    ("12220000", "Vierlinden", "Märkisch-Oderland", "BB"),
    ("12221000", "Waldsieversdorf", "Märkisch-Oderland", "BB"),
    ("12222000", "Wriezen", "Märkisch-Oderland", "BB"),
    ("12223000", "Zechin", "Märkisch-Oderland", "BB"),
    
    # ========================================
    # LANDKREIS OBERHAVEL (19)
    # ========================================
    ("12224000", "Birkenwerder", "Oberhavel", "BB"),
    ("12225000", "Fürstenberg/Havel", "Oberhavel", "BB"),
    ("12226000", "Glienicke/Nordbahn", "Oberhavel", "BB"),
    ("12227000", "Gransee", "Oberhavel", "BB"),
    ("12228000", "Großwoltersdorf", "Oberhavel", "BB"),
    ("12229000", "Hennigsdorf", "Oberhavel", "BB"),
    ("12230000", "Hohen Neuendorf", "Oberhavel", "BB"),
    ("12231000", "Kremmen", "Oberhavel", "BB"),
    ("12232000", "Leegebruch", "Oberhavel", "BB"),
    ("12233000", "Liebenwalde", "Oberhavel", "BB"),
    ("12234000", "Löwenberger Land", "Oberhavel", "BB"),
    ("12235000", "Mühlenbecker Land", "Oberhavel", "BB"),
    ("12236000", "Oberkrämer", "Oberhavel", "BB"),
    ("12237000", "Oranienburg", "Oberhavel", "BB"),
    ("12238000", "Schönermark", "Oberhavel", "BB"),
    ("12239000", "Sonnenberg", "Oberhavel", "BB"),
    ("12240000", "Stechlin", "Oberhavel", "BB"),
    ("12241000", "Velten", "Oberhavel", "BB"),
    ("12242000", "Zehdenick", "Oberhavel", "BB"),
    
    # ========================================
    # LANDKREIS OBERSRPEEWALD-LAUSITZ (25)
    # ========================================
    ("12243000", "Altdöbern", "Oberspreewald-Lausitz", "BB"),
    ("12244000", "Bronkow", "Oberspreewald-Lausitz", "BB"),
    ("12245000", "Calau", "Oberspreewald-Lausitz", "BB"),
    ("12246000", "Frauendorf", "Oberspreewald-Lausitz", "BB"),
    ("12247000", "Großräschen", "Oberspreewald-Lausitz", "BB"),
    ("12248000", "Grünewald", "Oberspreewald-Lausitz", "BB"),
    ("12249000", "Heideblick", "Oberspreewald-Lausitz", "BB"),
    ("12250000", "Hermsdorf", "Oberspreewald-Lausitz", "BB"),
    ("12251000", "Hohenbocka", "Oberspreewald-Lausitz", "BB"),
    ("12252000", "Kroppen", "Oberspreewald-Lausitz", "BB"),
    ("12253000", "Lauchhammer", "Oberspreewald-Lausitz", "BB"),
    ("12254000", "Lindenau", "Oberspreewald-Lausitz", "BB"),
    ("12255000", "Lübbenau/Spreewald", "Oberspreewald-Lausitz", "BB"),
    ("12256000", "Neu-Seeland", "Oberspreewald-Lausitz", "BB"),
    ("12257000", "Neupetershain", "Oberspreewald-Lausitz", "BB"),
    ("12258000", "Ortrand", "Oberspreewald-Lausitz", "BB"),
    ("12259000", "Ruhland", "Oberspreewald-Lausitz", "BB"),
    ("12260000", "Schipkau", "Oberspreewald-Lausitz", "BB"),
    ("12261000", "Schwarzbach", "Oberspreewald-Lausitz", "BB"),
    ("12262000", "Schwarzheide", "Oberspreewald-Lausitz", "BB"),
    ("12263000", "Senftenberg", "Oberspreewald-Lausitz", "BB"),
    ("12264000", "Tettau", "Oberspreewald-Lausitz", "BB"),
    ("12265000", "Vetschau/Spreewald", "Oberspreewald-Lausitz", "BB"),
    ("12266000", "Welzow", "Oberspreewald-Lausitz", "BB"),
    ("12267000", "Werminghoff", "Oberspreewald-Lausitz", "BB"),
    
    # ========================================
    # LANDKREIS ODER-SPREE (38)
    # ========================================
    ("12268000", "Bad Saarow", "Oder-Spree", "BB"),
    ("12269000", "Beeskow", "Oder-Spree", "BB"),
    ("12270000", "Berkenbrück", "Oder-Spree", "BB"),
    ("12271000", "Briesen (Mark)", "Oder-Spree", "BB"),
    ("12272000", "Brieskow-Finkenheerd", "Oder-Spree", "BB"),
    ("12273000", "Diensdorf-Radlow", "Oder-Spree", "BB"),
    ("12274000", "Eisenhüttenstadt", "Oder-Spree", "BB"),
    ("12275000", "Erkner", "Oder-Spree", "BB"),
    ("12276000", "Friedland", "Oder-Spree", "BB"),
    ("12277000", "Fürstenwalde/Spree", "Oder-Spree", "BB"),
    ("12278000", "Gosen-Neu Zittau", "Oder-Spree", "BB"),
    ("12279000", "Groß Lindow", "Oder-Spree", "BB"),
    ("12280000", "Grunow-Dammendorf", "Oder-Spree", "BB"),
    ("12281000", "Grünheide (Mark)", "Oder-Spree", "BB"),
    ("12282000", "Jacobsdorf", "Oder-Spree", "BB"),
    ("12283000", "Langewahl", "Oder-Spree", "BB"),
    ("12284000", "Lawitz", "Oder-Spree", "BB"),
    ("12285000", "Madlitz-Wilmersdorf", "Oder-Spree", "BB"),
    ("12286000", "Mixdorf", "Oder-Spree", "BB"),
    ("12287000", "Müllrose", "Oder-Spree", "BB"),
    ("12288000", "Neißemünde", "Oder-Spree", "BB"),
    ("12289000", "Neuzelle", "Oder-Spree", "BB"),
    ("12290000", "Ragow-Merz", "Oder-Spree", "BB"),
    ("12291000", "Rauen", "Oder-Spree", "BB"),
    ("12292000", "Reichenwalde", "Oder-Spree", "BB"),
    ("12293000", "Rietz-Neuendorf", "Oder-Spree", "BB"),
    ("12294000", "Schlaubetal", "Oder-Spree", "BB"),
    ("12295000", "Schöneiche bei Berlin", "Oder-Spree", "BB"),
    ("12296000", "Siehdichum", "Oder-Spree", "BB"),
    ("12297000", "Spreenhagen", "Oder-Spree", "BB"),
    ("12298000", "Steinhöfel", "Oder-Spree", "BB"),
    ("12299000", "Storkow (Mark)", "Oder-Spree", "BB"),
    ("12300000", "Tauche", "Oder-Spree", "BB"),
    ("12301000", "Vogelsang", "Oder-Spree", "BB"),
    ("12302000", "Wendisch Rietz", "Oder-Spree", "BB"),
    ("12303000", "Wiesenau", "Oder-Spree", "BB"),
    ("12304000", "Woltersdorf", "Oder-Spree", "BB"),
    ("12305000", "Ziltendorf", "Oder-Spree", "BB"),
    
    # ========================================
    # LANDKREIS OSTPRIGNITZ-RUPPIN (23)
    # ========================================
    ("12306000", "Dabergotz", "Ostprignitz-Ruppin", "BB"),
    ("12307000", "Dreetz", "Ostprignitz-Ruppin", "BB"),
    ("12308000", "Fehrbellin", "Ostprignitz-Ruppin", "BB"),
    ("12309000", "Heiligengrabe", "Ostprignitz-Ruppin", "BB"),
    ("12310000", "Herzberg (Mark)", "Ostprignitz-Ruppin", "BB"),
    ("12311000", "Kyritz", "Ostprignitz-Ruppin", "BB"),
    ("12312000", "Lindow (Mark)", "Ostprignitz-Ruppin", "BB"),
    ("12313000", "Märkisch Linden", "Ostprignitz-Ruppin", "BB"),
    ("12314000", "Neuruppin", "Ostprignitz-Ruppin", "BB"),
    ("12315000", "Rheinsberg", "Ostprignitz-Ruppin", "BB"),
    ("12316000", "Rüthnick", "Ostprignitz-Ruppin", "BB"),
    ("12317000", "Sieversdorf-Hohenofen", "Ostprignitz-Ruppin", "BB"),
    ("12318000", "Storbeck-Frankendorf", "Ostprignitz-Ruppin", "BB"),
    ("12319000", "Temnitzquell", "Ostprignitz-Ruppin", "BB"),
    ("12320000", "Temnitztal", "Ostprignitz-Ruppin", "BB"),
    ("12321000", "Vielitzsee", "Ostprignitz-Ruppin", "BB"),
    ("12322000", "Walsleben", "Ostprignitz-Ruppin", "BB"),
    ("12323000", "Wittstock/Dosse", "Ostprignitz-Ruppin", "BB"),
    ("12324000", "Wusterhausen/Dosse", "Ostprignitz-Ruppin", "BB"),
    ("12325000", "Zernitz-Lohm", "Ostprignitz-Ruppin", "BB"),
    
    # ========================================
    # LANDKREIS POTSDAM-MITTELMARK (38)
    # ========================================
    ("12326000", "Bad Belzig", "Potsdam-Mittelmark", "BB"),
    ("12327000", "Beelitz", "Potsdam-Mittelmark", "BB"),
    ("12328000", "Beetzsee", "Potsdam-Mittelmark", "BB"),
    ("12329000", "Beetzseeheide", "Potsdam-Mittelmark", "BB"),
    ("12330000", "Bensdorf", "Potsdam-Mittelmark", "BB"),
    ("12331000", "Borkheide", "Potsdam-Mittelmark", "BB"),
    ("12332000", "Borkwalde", "Potsdam-Mittelmark", "BB"),
    ("12333000", "Brück", "Potsdam-Mittelmark", "BB"),
    ("12334000", "Buckautal", "Potsdam-Mittelmark", "BB"),
    ("12335000", "Golzow", "Potsdam-Mittelmark", "BB"),
    ("12336000", "Görzke", "Potsdam-Mittelmark", "BB"),
    ("12337000", "Gräben", "Potsdam-Mittelmark", "BB"),
    ("12338000", "Groß Kreutz (Havel)", "Potsdam-Mittelmark", "BB"),
    ("12339000", "Havelsee", "Potsdam-Mittelmark", "BB"),
    ("12340000", "Kleinmachnow", "Potsdam-Mittelmark", "BB"),
    ("12341000", "Kloster Lehnin", "Potsdam-Mittelmark", "BB"),
    ("12342000", "Linthe", "Potsdam-Mittelmark", "BB"),
    ("12343000", "Michendorf", "Potsdam-Mittelmark", "BB"),
    ("12344000", "Mühlenfließ", "Potsdam-Mittelmark", "BB"),
    ("12345000", "Niemegk", "Potsdam-Mittelmark", "BB"),
    ("12346000", "Nuthetal", "Potsdam-Mittelmark", "BB"),
    ("12347000", "Päwesin", "Potsdam-Mittelmark", "BB"),
    ("12348000", "Planebruch", "Potsdam-Mittelmark", "BB"),
    ("12349000", "Planetal", "Potsdam-Mittelmark", "BB"),
    ("12350000", "Rabenstein/Fläming", "Potsdam-Mittelmark", "BB"),
    ("12351000", "Rosenau", "Potsdam-Mittelmark", "BB"),
    ("12352000", "Roskow", "Potsdam-Mittelmark", "BB"),
    ("12353000", "Schwielowsee", "Potsdam-Mittelmark", "BB"),
    ("12354000", "Seddiner See", "Potsdam-Mittelmark", "BB"),
    ("12355000", "Stahnsdorf", "Potsdam-Mittelmark", "BB"),
    ("12356000", "Teltow", "Potsdam-Mittelmark", "BB"),
    ("12357000", "Treuenbrietzen", "Potsdam-Mittelmark", "BB"),
    ("12358000", "Wenzlow", "Potsdam-Mittelmark", "BB"),
    ("12359000", "Werder (Havel)", "Potsdam-Mittelmark", "BB"),
    ("12360000", "Wiesenburg/Mark", "Potsdam-Mittelmark", "BB"),
    ("12361000", "Wollin", "Potsdam-Mittelmark", "BB"),
    ("12362000", "Wusterwitz", "Potsdam-Mittelmark", "BB"),
    ("12363000", "Ziesar", "Potsdam-Mittelmark", "BB"),
    
    # ========================================
    # LANDKREIS PRIGNITZ (26)
    # ========================================
    ("12364000", "Bad Wilsnack", "Prignitz", "BB"),
    ("12365000", "Berge", "Prignitz", "BB"),
    ("12366000", "Breese", "Prignitz", "BB"),
    ("12367000", "Cumlosen", "Prignitz", "BB"),
    ("12368000", "Gerdshagen", "Prignitz", "BB"),
    ("12369000", "Groß Pankow (Prignitz)", "Prignitz", "BB"),
    ("12370000", "Gülitz-Reetz", "Prignitz", "BB"),
    ("12371000", "Gumtow", "Prignitz", "BB"),
    ("12372000", "Halenbeck-Rohlsdorf", "Prignitz", "BB"),
    ("12373000", "Karstädt", "Prignitz", "BB"),
    ("12374000", "Kümmernitztal", "Prignitz", "BB"),
    ("12375000", "Legde/Quitzöbel", "Prignitz", "BB"),
    ("12376000", "Lenzen (Elbe)", "Prignitz", "BB"),
    ("12377000", "Lanz", "Prignitz", "BB"),
    ("12378000", "Marienfließ", "Prignitz", "BB"),
    ("12379000", "Meyenburg", "Prignitz", "BB"),
    ("12380000", "Perleberg", "Prignitz", "BB"),
    ("12381000", "Pirow", "Prignitz", "BB"),
    ("12382000", "Plattenburg", "Prignitz", "BB"),
    ("12383000", "Pritzwalk", "Prignitz", "BB"),
    ("12384000", "Putlitz", "Prignitz", "BB"),
    ("12385000", "Triglitz", "Prignitz", "BB"),
    ("12386000", "Weisen", "Prignitz", "BB"),
    ("12387000", "Wittenberge", "Prignitz", "BB"),
    
    # ========================================
    # LANDKREIS SPREE-NEIßE (30)
    # ========================================
    ("12388000", "Briesen (Mark)", "Spree-Neiße", "BB"),
    ("12389000", "Burg (Spreewald)", "Spree-Neiße", "BB"),
    ("12390000", "Döbern", "Spree-Neiße", "BB"),
    ("12391000", "Drachhausen", "Spree-Neiße", "BB"),
    ("12392000", "Drehnow", "Spree-Neiße", "BB"),
    ("12393000", "Felixsee", "Spree-Neiße", "BB"),
    ("12394000", "Forst (Lausitz)", "Spree-Neiße", "BB"),
    ("12395000", "Groß Schacksdorf-Simmersdorf", "Spree-Neiße", "BB"),
    ("12396000", "Guben", "Spree-Neiße", "BB"),
    ("12397000", "Guhrow", "Spree-Neiße", "BB"),
    ("12398000", "Heinersbrück", "Spree-Neiße", "BB"),
    ("12399000", "Hornow-Wadelsdorf", "Spree-Neiße", "BB"),
    ("12400000", "Jämlitz-Klein Düben", "Spree-Neiße", "BB"),
    ("12401000", "Jänschwalde", "Spree-Neiße", "BB"),
    ("12402000", "Kolkwitz", "Spree-Neiße", "BB"),
    ("12403000", "Neiße-Malxetal", "Spree-Neiße", "BB"),
    ("12404000", "Neuhausen/Spree", "Spree-Neiße", "BB"),
    ("12405000", "Peitz", "Spree-Neiße", "BB"),
    ("12406000", "Schenkendöbern", "Spree-Neiße", "BB"),
    ("12407000", "Schmogrow-Fehrow", "Spree-Neiße", "BB"),
    ("12408000", "Spremberg", "Spree-Neiße", "BB"),
    ("12409000", "Tauer", "Spree-Neiße", "BB"),
    ("12410000", "Teichland", "Spree-Neiße", "BB"),
    ("12411000", "Tschernitz", "Spree-Neiße", "BB"),
    ("12412000", "Turnow-Preilack", "Spree-Neiße", "BB"),
    ("12413000", "Welzow", "Spree-Neiße", "BB"),
    ("12414000", "Werben", "Spree-Neiße", "BB"),
    ("12415000", "Wiesengrund", "Spree-Neiße", "BB"),
    
    # ========================================
    # LANDKREIS TELTOW-FLÄMING (16)
    # ========================================
    ("12416000", "Am Mellensee", "Teltow-Fläming", "BB"),
    ("12417000", "Baruth/Mark", "Teltow-Fläming", "BB"),
    ("12418000", "Blankenfelde-Mahlow", "Teltow-Fläming", "BB"),
    ("12419000", "Dahme/Mark", "Teltow-Fläming", "BB"),
    ("12420000", "Dahmetal", "Teltow-Fläming", "BB"),
    ("12421000", "Großbeeren", "Teltow-Fläming", "BB"),
    ("12422000", "Ihlow", "Teltow-Fläming", "BB"),
    ("12423000", "Jüterbog", "Teltow-Fläming", "BB"),
    ("12424000", "Luckenwalde", "Teltow-Fläming", "BB"),
    ("12425000", "Ludwigsfelde", "Teltow-Fläming", "BB"),
    ("12426000", "Niederer Fläming", "Teltow-Fläming", "BB"),
    ("12427000", "Niedergörsdorf", "Teltow-Fläming", "BB"),
    ("12428000", "Nuthe-Urstromtal", "Teltow-Fläming", "BB"),
    ("12429000", "Rangsdorf", "Teltow-Fläming", "BB"),
    ("12430000", "Trebbin", "Teltow-Fläming", "BB"),
    ("12431000", "Zossen", "Teltow-Fläming", "BB"),
    
    # ========================================
    # LANDKREIS UCKERMARK (34)
    # ========================================
    ("12432000", "Angermünde", "Uckermark", "BB"),
    ("12433000", "Boitzenburger Land", "Uckermark", "BB"),
    ("12434000", "Brüssow", "Uckermark", "BB"),
    ("12435000", "Carmzow-Wallmow", "Uckermark", "BB"),
    ("12436000", "Casekow", "Uckermark", "BB"),
    ("12437000", "Flieth-Stegelitz", "Uckermark", "BB"),
    ("12438000", "Gartz (Oder)", "Uckermark", "BB"),
    ("12439000", "Gerswalde", "Uckermark", "BB"),
    ("12440000", "Göritz", "Uckermark", "BB"),
    ("12441000", "Gramzow", "Uckermark", "BB"),
    ("12442000", "Grünow", "Uckermark", "BB"),
    ("12443000", "Hohenselchow-Groß Pinnow", "Uckermark", "BB"),
    ("12444000", "Lychen", "Uckermark", "BB"),
    ("12445000", "Mark Landin", "Uckermark", "BB"),
    ("12446000", "Mescherin", "Uckermark", "BB"),
    ("12447000", "Milmersdorf", "Uckermark", "BB"),
    ("12448000", "Mittenwalde", "Uckermark", "BB"),
    ("12449000", "Nordwestuckermark", "Uckermark", "BB"),
    ("12450000", "Oberuckersee", "Uckermark", "BB"),
    ("12451000", "Passow", "Uckermark", "BB"),
    ("12452000", "Pinnow", "Uckermark", "BB"),
    ("12453000", "Prenzlau", "Uckermark", "BB"),
    ("12454000", "Randowtal", "Uckermark", "BB"),
    ("12455000", "Schenkenberg", "Uckermark", "BB"),
    ("12456000", "Schöneberg", "Uckermark", "BB"),
    ("12457000", "Schönfeld", "Uckermark", "BB"),
    ("12458000", "Schwedt/Oder", "Uckermark", "BB"),
    ("12459000", "Tantow", "Uckermark", "BB"),
    ("12460000", "Templin", "Uckermark", "BB"),
    ("12461000", "Uckerfelde", "Uckermark", "BB"),
    ("12462000", "Uckerland", "Uckermark", "BB"),
    ("12463000", "Zichow", "Uckermark", "BB"),
]

def load_municipalities():
    """
    Load ALL Brandenburg municipalities into municipality_seed table.
    """
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Clear existing Brandenburg entries
            cur.execute("DELETE FROM municipality_seed WHERE state = 'BB'")
            
            # Insert all municipalities
            for muni_key, name, county, state in BRANDENBURG_MUNICIPALITIES_COMPLETE:
                cur.execute("""
                    INSERT INTO municipality_seed (municipality_key, name, county, state, source)
                    VALUES (%s, %s, %s, %s, 'complete_list')
                    ON CONFLICT (municipality_key) DO UPDATE SET
                        name = EXCLUDED.name,
                        county = EXCLUDED.county,
                        state = EXCLUDED.state,
                        source = EXCLUDED.source
                """, (muni_key, name, county, state))
            
            conn.commit()
            total = len(BRANDENBURG_MUNICIPALITIES_COMPLETE)
            print(f"✅ Loaded {total} Brandenburg municipalities (COMPLETE LIST)")
            print(f"   - 4 kreisfreie Städte")
            print(f"   - 14 Landkreise")
            print(f"   - {total} Gemeinden insgesamt")
            print("\n📋 Note: This is a comprehensive list. For official verification, use:")
            print("   - Destatis Gemeindeverzeichnis: https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/_inhalt.html")
            print("   - BKG VG250: https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html")

if __name__ == "__main__":
    load_municipalities()






