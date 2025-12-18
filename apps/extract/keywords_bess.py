"""
Comprehensive keyword dictionaries for BESS detection.
Based on improved rule system for Brandenburg planning/permitting.
"""

# 2.1 Planning-procedure signals (B-Plan / Bauleitplanung)
PLANNING_TERMS_STRONG = [
    "bebauungsplan",
    "b-plan",
    "bauleitplanung",
    "baugb",  # Only when near §§ below
    "flaechennutzungsplan",
    "flächennutzungsplan",
    "fnp",
    "vorhabenbezogener bebauungsplan",
    "vbp",  # Only when near "bebauungsplan"
]

PLANNING_STEP_TERMS = [
    # Aufstellung
    "aufstellungsbeschluss",
    "beschluss zur aufstellung",
    "beschlussfassung zur aufstellung",
    "gemäß § 2 abs. 1 baugb",
    "gemaess § 2 abs. 1 baugb",
    "§ 2 abs. 1 baugb",
    # Frühzeitige Beteiligung
    "fruehzeitige beteiligung",
    "frühzeitige beteiligung",
    "§ 3 abs. 1 baugb",
    "§ 4 abs. 1 baugb",
    # Öffentliche Auslegung
    "oeffentliche auslegung",
    "öffentliche auslegung",
    "auslegung der unterlagen",
    "§ 3 abs. 2 baugb",
    "§ 4 abs. 2 baugb",
    # Satzung / Inkrafttreten
    "satzungsbeschluss",
    "als satzung beschlossen",
    "bekanntmachung des satzungsbeschlusses",
    "inkrafttreten",
    "tritt in kraft",
    "§ 10 baugb",
]

PLANNING_SUPPORT_TERMS = [
    "geltungsbereich",
    "planzeichnung",
    "begruendung",
    "begründung",
    "umweltbericht",
    "umweltpruefung",
    "umweltprüfung",
    "abgrenzung",
    "plangebiet",
    "staedtebaulicher vertrag",
    "städtebaulicher vertrag",
]

# 2.2 Permit / privileged-project signals (§35/§34/§36 + permits)
PERMIT_TERMS_STRONG = [
    "bauvorbescheid",
    "antrag auf bauvorbescheid",
    "vorbescheid",
    "baugenehmigung",
    "bauantrag",
    "genehmigung nach",
    "gemeindliches einvernehmen",
    "einvernehmen gemaess § 36 baugb",
    "§ 36 baugb",
    "stellungnahme der gemeinde",
    "einvernehmen erteilen",
    "einvernehmen versagen",
    # Expanded privileged project language
    "bauvoranfrage",
    "bauvorantrag",
    "kenntnisnahme",
    "antrag auf errichtung",
    "standortgemeinde",
]

LEGAL_BASIS_TERMS = [
    "§ 35 baugb",
    "aussenbereich",
    "außenbereich",
    "privilegiertes vorhaben",
    "§ 34 baugb",
    "innenbereich",
    "§ 36 baugb",
]

PERMIT_DOC_CONTEXT_TERMS = [
    "beschlussvorlage",
    "sitzungsvorlage",
    "niederschrift",
    "protokoll",
    "tagesordnung",
    "bauausschuss",
    "hauptausschuss",
    "gemeindevertretung",
    "stadtverordnetenversammlung",
    "ortsbeirat",
]

# 2.3 BESS / storage terms
BESS_TERMS_EXPLICIT = [
    "batteriespeicher",
    "batterie-speicher",
    "energiespeicher",
    "stromspeicher",
    "grossspeicher",
    "großspeicher",
    "bess",
    "speicheranlage",  # Often BESS but can be heat/water — treat as medium
    "speicherpark",  # Medium
    "speicherkraftwerk",  # Rare/ambiguous; medium
]

BESS_TERMS_CONTAINER_GRID = [
    "containeranlage",
    "speichercontainer",
    "wechselrichter",
    "trafostation",
    "trafostationen",
    "transformator",
    "umspannwerk",
    "netzanschluss",
    "mittelspannung",
    "hochspannung",
    "anschluss an das stromnetz",
    "netzverknuepfungspunkt",
    "netzverknüpfungspunkt",
    # Expanded: containeranlage paired with grid context
    "anlage zur energiespeicherung",
]

ENERGY_CONTEXT_TERMS = [
    "photovoltaik",
    "pv",
    "solarpark",
    "windenergie",
    "energieerzeugung",
    "energieversorgung",
    "strom",
    "netzdienlich",
    "netzdienlichkeit",
    "regelenergie",
    "spitzenlast",
    "erneuerbare energien",
]

# 2.4 Zoning/land-use terms
ZONING_TERMS = [
    "sondergebiet",
    "so ",
    "so energie",
    "sondergebiet energie",
    "industriegebiet",
    "gi",
    "gewerbegebiet",
    "ge",
    "flaeche fuer versorgungsanlagen",
    "fläche für versorgungsanlagen",
    "technische anlagen",
    "anlagen zur energieversorgung",
    "versorgung",
]

# 2.5 Location parcel terms
PARCEL_TERMS = [
    "gemarkung",
    "flur",
    "flurstueck",
    "flurstück",
    "flurstuecke",
    "flurstücke",
    "lageplan",
    "adresse",
    "strasse",
    "straße",
    "koordinaten",
]

# 3) Negative keywords (false-positive suppression)
NEGATIVE_STORAGE_TERMS = [
    "regenrueckhaltebecken",
    "regenrückhaltebecken",
    "wasserbehaelter",
    "wasserbehälter",
    "loeschwasser",
    "löschwasser",
    "waermespeicher",
    "wärmespeicher",
    "kaeltespeicher",
    "kältespeicher",
    "gaslager",
    "gasspeicher",
    "muell",
    "abfall",
    "lagerhalle",
    "lagerung",
    "speisekammer",
]

NEGATIVE_UNRELATED_TERMS = [
    "datenspeicher",
    "speicherstadt",
    "speicherkarte",
    "cloud",
]

