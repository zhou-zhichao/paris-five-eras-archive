"""Hand-authored historical geography of Paris (metres, origin Notre-Dame, x east, y north).

Zones are cumulative growth rings with a year range; villages are early nuclei;
LANDMARKS lists monuments with birth/death years, position and orientation.
"""

# ------------------------------------------------------------------ growth zones
# name, polygon, year_start, year_end, kit hint
ZONES = [
    ("celtic_cite", None, -260, -60, "celtic"),           # polygon filled from river holes at runtime
    ("roman_left", [(-1000, 300), (-1100, -500), (-900, -1050), (-200, -1200), (400, -1000),
                    (520, -600), (450, -200), (0, 20), (-500, 250)], 60, 330, "roman"),
    ("roman_right", [(80, 250), (600, 200), (650, 600), (150, 650)], 180, 340, "roman"),
    ("frank_cite", None, 480, 700, "medieval"),
    ("frank_right", [(-300, 250), (700, 150), (800, 700), (100, 800), (-400, 650)], 620, 980, "medieval"),
    ("frank_left", [(-900, 300), (-1300, 50), (-1200, -350), (-700, -600), (-100, -650), (300, -450), (350, 0)], 700, 1000, "medieval"),
    ("pa_right", [(-1150, 300), (-1150, 950), (-800, 1200), (-300, 1380), (150, 1430), (550, 1440),
                  (950, 1150), (1080, 650), (1000, -120), (400, 0)], 1040, 1250, "medieval"),
    ("pa_left", [(-950, 600), (-1100, -100), (-950, -650), (-500, -950), (50, -980), (500, -720),
                 (600, -250), (550, 0), (0, 120), (-500, 380)], 1080, 1290, "medieval"),
    ("charles_v", [(-1650, 650), (-1750, 1250), (-1050, 1650), (-300, 1880), (500, 1930), (1050, 1680),
                   (1550, 900), (1650, 100), (1250, -320), (0, -100)], 1250, 1450, "medieval"),
    ("faubourg_med", [(-1400, -200), (-1400, -900), (-800, -1250), (300, -1300), (900, -1000), (1600, -500),
                      (2000, 200), (2000, 1200), (1300, 2000), (0, 2150), (-1200, 2100), (-2000, 1600), (-2000, 600)],
     1480, 1640, "medieval"),
    ("louis_xiii", [(-1700, 650), (-2400, 1250), (-2100, 2000), (-1000, 2200), (-300, 1950), (-1000, 1650), (-1700, 1250)],
     1600, 1680, "classical"),
    ("fbg_st_germain", [(-900, 650), (-2400, 950), (-2900, 400), (-2600, -350), (-1500, -700), (-1000, -250)],
     1620, 1760, "classical"),
    ("faubourgs_18c", [(-2600, -500), (-2200, -1500), (-1000, -2000), (500, -2100), (1700, -1500), (2400, -600),
                       (2800, 500), (2600, 1600), (1800, 2600), (300, 3000), (-1200, 2900), (-2600, 2300), (-3300, 1300),
                       (-3400, 300)], 1620, 1790, "classical"),
    ("fermiers", [(-4021, 2315), (-2995, 2894), (-1677, 3340), (-400, 3480), (740, 3562), (1472, 3451),
                  (2424, 2115), (3100, 800), (3362, -512), (2205, -1558), (1000, -2350), (447, -2449),
                  (-1274, -2115), (-2117, -1224), (-3508, -557), (-4300, 300), (-4607, 1002)], 1760, 1865, "haussmann"),
    ("thiers", "PARIS", 1855, 1935, "haussmann"),          # commune boundary minus the two bois
    ("inner_suburb", ("PARIS_BUFFER", 3500), 1875, 1965, "modern"),
    ("outer_suburb", ("PARIS_BUFFER", 12000), 1920, 2015, "suburb"),
]

# ------------------------------------------------------------------ villages / early nuclei
# (name, x, y, radius, year_start, year_end)
VILLAGES = [
    ("Nanterre (celtic)", -9500, 4300, 260, -250, -80),
    ("Saint-Germain-des-Pres", -1165, 100, 170, 560, 800),
    ("Saint-Marcel", 500, -1350, 180, 560, 900),
    ("Saint-Martin-des-Champs", 420, 1500, 160, 1060, 1200),
    ("Saint-Denis", 720, 9200, 420, 630, 1200),
    ("Montmartre", -520, 3760, 230, 1130, 1500),
    ("Belleville", 2424, 2115, 220, 1300, 1600),
    ("Charonne", 3300, 700, 220, 1100, 1500),
    ("Menilmontant", 2600, 1500, 180, 1500, 1750),
    ("La Chapelle", 300, 3900, 200, 1200, 1500),
    ("La Villette", 1700, 4200, 200, 1300, 1600),
    ("Vaugirard", -2900, -1500, 240, 1250, 1600),
    ("Montrouge", -1200, -3300, 220, 1300, 1700),
    ("Gentilly", -200, -3700, 200, 1200, 1600),
    ("Ivry", 1800, -3900, 260, 1200, 1600),
    ("Vitry", 2700, -6900, 300, 1200, 1700),
    ("Charenton", 3800, -2300, 250, 1100, 1500),
    ("Passy", -4900, 1300, 240, 1200, 1600),
    ("Auteuil", -5900, -500, 230, 1200, 1600),
    ("Boulogne", -7900, -1500, 320, 1300, 1700),
    ("Neuilly", -6300, 2600, 240, 1300, 1700),
    ("Puteaux", -8400, 2900, 230, 1400, 1750),
    ("Courbevoie", -8000, 4300, 230, 1400, 1750),
    ("Nanterre", -9600, 4300, 330, 900, 1500),
    ("Clichy", -1800, 4600, 260, 1000, 1500),
    ("Saint-Ouen", -800, 5800, 250, 1000, 1500),
    ("Aubervilliers", 1700, 6600, 260, 1100, 1500),
    ("Pantin", 2600, 4900, 240, 1200, 1600),
    ("Bagnolet", 4300, 1300, 220, 1200, 1600),
    ("Montreuil", 5500, 900, 320, 900, 1500),
    ("Vincennes", 5500, -100, 280, 1200, 1600),
    ("Saint-Maur", 8700, -4800, 330, 1100, 1600),
    ("Creteil", 6300, -6600, 300, 1100, 1600),
    ("Issy", -5200, -3500, 260, 1100, 1600),
    ("Meudon", -8200, -4600, 280, 1200, 1700),
    ("Sevres", -9900, -3900, 260, 1200, 1700),
    ("Saint-Cloud", -9400, -1500, 280, 1000, 1500),
    ("Suresnes", -9500, 800, 260, 1100, 1600),
    ("Argenteuil", -6700, 10300, 400, 700, 1300),
    ("Versailles town", -8000, -4400, 500, 1670, 1780),
    ("Le Bourget", 4400, 10800, 250, 1200, 1700),
    ("Bobigny", 7000, 5900, 250, 1300, 1700),
    ("Drancy", 5400, 8500, 260, 1300, 1700),
    ("Fontenay", 9100, -450, 280, 1200, 1600),
    ("Choisy", 3200, -9900, 300, 1200, 1700),
    ("Antony", -2500, -11000, 320, 1200, 1700),
    ("Sceaux", -3200, -8800, 260, 1400, 1750),
    ("Rueil", -12500, 2500, 350, 1000, 1500),
    ("Colombes", -8200, 7500, 300, 1100, 1600),
    ("Levallois", -4200, 3900, 200, 1850, 1900),
]

# high-rise estate clusters (grands ensembles): (x, y, radius, year_start, year_end)
SLAB_ZONES = [
    (2500, 8200, 500, 1958, 1972),     # La Courneuve 4000
    (7000, 5900, 450, 1962, 1975),     # Bobigny
    (6300, -6600, 550, 1966, 1978),    # Creteil
    (-9800, 4400, 500, 1968, 1980),    # Nanterre
    (3200, -9900, 350, 1960, 1972),    # Choisy
    (-1600, 7200, 400, 1960, 1972),    # Saint-Denis / Saint-Ouen
    (4400, 10600, 380, 1962, 1975),    # Le Bourget / Drancy
    (-5000, -8200, 400, 1962, 1975),   # Clamart / Meudon-la-Foret
    (9000, 2500, 400, 1965, 1978),     # Rosny / Montreuil hauts
    (1500, -4900, 300, 1965, 1978),    # Ivry / Vitry
    (-10800, -900, 380, 1965, 1978),   # Saint-Cloud / Rueil
    (-2900, -11800, 380, 1965, 1978),  # Antony
    (-14000, 7500, 450, 1962, 1975),   # Sartrouville
    (11000, 1200, 400, 1965, 1978),    # Noisy-le-Grand direction
]

# (x, y, radius, year_start, year_end)
LA_DEFENSE = (-8000, 4200, 700, 1966, 2012)

# ------------------------------------------------------------------ city walls
# (name, polyline (closed if last==first), birth, death, height)
WALLS = [
    ("cite_roman", None, 300, 1020, 7),
    ("philippe_auguste_right", [(-1150, 500), (-1150, 950), (-800, 1200), (-300, 1380), (150, 1430), (550, 1440),
                                (950, 1150), (1080, 650), (1000, 20)], 1190, 1600, 9),
    ("philippe_auguste_left", [(-950, 520), (-1100, -100), (-950, -650), (-500, -950), (50, -980), (500, -720),
                               (600, -250), (550, -230)], 1200, 1700, 9),
    ("charles_v", [(-1650, 900), (-1750, 1250), (-1050, 1650), (-300, 1880), (500, 1930), (1050, 1680),
                   (1550, 900), (1650, 100)], 1358, 1670, 10),
    ("louis_xiii", [(-1750, 1250), (-2400, 1250), (-2100, 2000), (-1000, 2200), (-300, 1880)], 1633, 1670, 9),
    ("fermiers", [(-4021, 2315), (-2995, 2894), (-1677, 3340), (-400, 3480), (740, 3562), (1472, 3451),
                  (2424, 2115), (3100, 800), (3362, -512), (2205, -1558), (1000, -2350), (447, -2449),
                  (-1274, -2115), (-2117, -1224), (-3508, -557), (-4300, 300), (-4607, 1002), (-4021, 2315)],
     1784, 1860, 4),
    ("thiers", "PARIS", 1841, 1925, 8),
]

# ------------------------------------------------------------------ parks (birth year overrides by name substring)
PARK_YEARS = {
    "Tuileries": 1564, "Luxembourg": 1612, "Jardin des Plantes": 1635, "Champ de Mars": 1765,
    "Palais-Royal": 1633, "Monceau": 1778, "Père-Lachaise": 1804, "Montsouris": 1869,
    "Buttes-Chaumont": 1867, "Bois de Boulogne": 1852, "Bois de Vincennes": 1860, "Invalides": 1700,
    "Versailles": 1662, "Saint-Cloud": 1660, "Montparnasse": 1824, "Batignolles": 1862,
    "Sceaux": 1670, "La Villette": 1987, "Bercy": 1994, "André Citroën": 1992, "Georges-Brassens": 1985,
    "Trocadéro": 1878, "Champs-Élysées": 1670, "Vosges": 1612, "Belleville": 1988,
}
PARK_DEFAULT_YEAR = 1900     # unnamed / unknown parks appear with the surrounding suburb

# ------------------------------------------------------------------ bridges (name substring -> year)
BRIDGE_YEARS = {
    "Petit Pont": -250, "Pont Notre-Dame": -250, "Pont au Change": 1140, "Pont Saint-Michel": 1387,
    "Pont Neuf": 1607, "Pont Marie": 1635, "Pont de la Tournelle": 1656, "Pont Royal": 1689,
    "Pont au Double": 1634, "Pont Louis-Philippe": 1862, "Pont d'Arcole": 1856, "Pont Sully": 1876,
    "Pont de la Concorde": 1791, "Pont des Arts": 1804, "Pont d'Austerlitz": 1807, "Pont d'Iéna": 1814,
    "Pont de l'Archevêché": 1828, "Pont du Carrousel": 1834, "Pont de l'Alma": 1856, "Pont de Solférino": 1861,
    "Passerelle Léopold-Sédar-Senghor": 1999, "Pont de Bercy": 1864, "Pont National": 1853, "Pont de Tolbiac": 1882,
    "Pont Mirabeau": 1896, "Pont Alexandre III": 1900, "Pont de Bir-Hakeim": 1905, "Pont de Grenelle": 1827,
    "Pont de Passy": 1905, "Pont des Invalides": 1855, "Pont Charles-de-Gaulle": 1996, "Pont de Neuilly": 1772,
    "Pont de Sèvres": 1820, "Pont de Saint-Cloud": 1810, "Pont de Charenton": 1650, "Pont d'Ivry": 1830,
    "Pont de Puteaux": 1860, "Pont de Suresnes": 1840, "Pont de Levallois": 1880, "Pont de Clichy": 1860,
    "Pont de Saint-Ouen": 1860, "Pont de Bezons": 1870, "Pont de Chatou": 1880, "Pont de Joinville": 1850,
    "Viaduc d'Auteuil": 1865, "Pont du Garigliano": 1966, "Pont Aval": 1968, "Pont Amont": 1969,
    "Pont de Nogent": 1860, "Pont de Créteil": 1860, "Pont de Choisy": 1860, "Pont de Villeneuve": 1870,
    "Pont de Bry": 1870, "Pont de Conflans": 1900, "Pont de Saint-Maur": 1850, "Pont Simone-Veil": 2010,
}
BRIDGE_DEFAULT_YEAR = 1880

# ------------------------------------------------------------------ landmarks
# name, x, y, rotation(deg, ccw from +x = east), birth, death, builder key, params
# builder keys: "glb:<file>" or a procedural builder name in landmarks.py
LANDMARKS = [
    # celtic / roman
    ("celtic_bridge_n", -160, 330, 90, -250, -30, "wood_bridge", {"length": 150}),
    ("celtic_bridge_s", -230, -70, 90, -250, -30, "wood_bridge", {"length": 90}),
    ("roman_forum", -579, -724, 7, -20, 480, "roman_forum", {"w": 100, "d": 170}),
    ("roman_theatre", -560, -300, 7, 50, 480, "roman_theatre", {"r": 36}),
    ("arenes_lutece", 212, -879, 20, 80, 520, "roman_amphitheatre", {"a": 65, "b": 52}),
    ("thermes_cluny", -470, -360, 7, 200, 520, "roman_baths", {"w": 70, "d": 60}),
    ("cite_temple", 20, 20, 7, -10, 400, "roman_temple", {"w": 26, "d": 44}),
    ("roman_palace_cite", -420, 250, 7, 280, 990, "roman_baths", {"w": 60, "d": 50}),
    # frankish / early medieval
    ("saint_etienne_cite", 20, 20, 7, 540, 1165, "basilica", {"w": 36, "d": 70, "h": 18}),
    ("saint_germain_des_pres", -1165, 100, 7, 558, 9999, "glb:saint_germain_des_pres", {"w": 120, "d": 110, "h": 46}),
    ("saint_martin_champs", 420, 1500, 7, 1060, 9999, "abbey", {"w": 60, "d": 90, "h": 24}),
    ("saint_marcel_church", 500, -1350, 7, 560, 1806, "basilica", {"w": 20, "d": 44, "h": 14}),
    ("saint_denis_basilica", 722, 9184, 7, 640, 9999, "cathedral", {"w": 40, "d": 108, "h": 30, "towers": 1}),
    # high medieval
    ("notre_dame", 0, 0, 7, 1163, 9999, "glb:notre_dame", {"w": 128, "d": 48, "h": 69}),
    ("palais_cite", -380, 260, 7, 990, 9999, "palace_block", {"w": 120, "d": 90, "h": 16}),
    ("sainte_chapelle", -359, 267, 7, 1242, 9999, "glb:sainte_chapelle", {"w": 36, "d": 17, "h": 42}),
    ("louvre_fort", -1000, 900, 7, 1200, 1546, "castle", {"w": 78, "d": 72, "h": 14, "keep": 32}),
    ("tour_du_temple", 864, 1336, 7, 1240, 1808, "glb:tour_du_temple", {"w": 60, "d": 60, "h": 50}),
    ("grand_chatelet", -110, 380, 7, 1130, 1802, "castle", {"w": 40, "d": 36, "h": 14, "keep": 20}),
    ("petit_chatelet", -212, -110, 97, 1180, 1782, "glb:petit_pont_petit_chatelet", {"w": 60, "d": 30, "h": 22}),
    ("bastille", 1414, 22, 7, 1370, 1789, "castle", {"w": 66, "d": 34, "h": 24, "keep": 24}),
    ("saint_eustache", -348, 1160, 7, 1532, 9999, "cathedral", {"w": 44, "d": 100, "h": 34, "towers": 0}),
    ("hotel_de_ville_old", 195, 386, 7, 1533, 1871, "palace_block", {"w": 80, "d": 60, "h": 22}),
    ("saint_sulpice", -1103, -220, 7, 1646, 9999, "cathedral", {"w": 56, "d": 118, "h": 33, "towers": 2}),
    ("college_sorbonne", -430, -620, 7, 1257, 9999, "palace_block", {"w": 70, "d": 60, "h": 16}),
    # renaissance / classical
    ("louvre", -905, 850, 7, 1546, 9999, "glb:louvre", {"w": 175, "d": 175, "h": 32}),   # Cour Carree (the GLB is the square palace)
    ("grande_galerie", -1290, 930, 12, 1595, 9999, "palace_block", {"w": 440, "d": 36, "h": 22}),
    ("louvre_north_wing", -1250, 1120, 12, 1852, 9999, "palace_block", {"w": 420, "d": 36, "h": 22}),
    ("tuileries_palace", -1560, 1130, 97, 1564, 1871, "palace_block", {"w": 260, "d": 30, "h": 26}),
    ("luxembourg_palace", -926, -500, 7, 1615, 9999, "palace_block", {"w": 120, "d": 90, "h": 24}),
    ("place_des_vosges", 1180, 640, 7, 1605, 9999, "square_ring", {"w": 140, "d": 140, "h": 18}),
    ("invalides", -2729, 328, 7, 1671, 9999, "invalides", {"w": 250, "d": 230, "h": 22, "dome": 100}),
    ("val_de_grace", -450, -1350, 7, 1645, 9999, "domed_church", {"w": 40, "d": 70, "h": 22, "dome": 55}),
    ("observatoire", -1350, -1700, 7, 1667, 9999, "palace_block", {"w": 30, "d": 50, "h": 18}),
    # the reference film places Versailles much closer to Paris than reality so it stays in frame; we do the same
    ("versailles", -8600, -4700, 97, 1661, 9999, "versailles", {}),
    ("ecole_militaire", -3720, -170, 7, 1760, 9999, "palace_block", {"w": 220, "d": 90, "h": 22}),
    ("pantheon", -278, -754, 7, 1790, 9999, "domed_church", {"w": 84, "d": 110, "h": 30, "dome": 83}),
    ("palais_bourbon", -2316, 964, 7, 1728, 9999, "palace_block", {"w": 150, "d": 90, "h": 20}),
    ("hotel_de_ville", 195, 386, 7, 1882, 9999, "palace_block", {"w": 143, "d": 89, "h": 30}),
    ("madeleine", -2020, 1990, 7, 1842, 9999, "roman_temple", {"w": 43, "d": 108, "h": 30}),
    # napoleonic / haussmann
    ("arc_de_triomphe", -4021, 2315, 7, 1836, 9999, "glb:arc_de_triomphe", {"w": 45, "d": 22, "h": 50}),
    ("gare_du_nord", 400, 3065, 7, 1864, 9999, "glb:gare_du_nord", {"w": 200, "d": 190, "h": 38}),
    ("gare_de_l_est", 666, 2649, 7, 1849, 9999, "station", {"w": 180, "d": 220, "h": 28}),
    ("gare_saint_lazare", -1817, 2667, 7, 1842, 9999, "station", {"w": 200, "d": 240, "h": 28}),
    ("gare_de_lyon", 1817, -946, 40, 1855, 9999, "station", {"w": 180, "d": 200, "h": 28, "tower": 64}),
    ("gare_montparnasse", -2200, -1380, 7, 1852, 9999, "station", {"w": 200, "d": 180, "h": 24}),
    ("gare_austerlitz", 1050, -1300, 30, 1840, 9999, "station", {"w": 150, "d": 180, "h": 24}),
    ("opera_garnier", -1332, 2121, 7, 1875, 9999, "glb:palais_garnier", {"w": 150, "d": 100, "h": 56}),
    ("grand_palais", -2749, 1468, 30, 1900, 9999, "grand_palais", {"w": 240, "d": 150, "h": 44}),
    ("trocadero_palace", -4592, 942, 7, 1878, 1935, "palace_block", {"w": 200, "d": 60, "h": 30}),
    ("palais_chaillot", -4592, 942, 7, 1937, 9999, "palace_block", {"w": 220, "d": 60, "h": 26}),
    ("eiffel", -4058, 590, 7, 1889, 9999, "glb:eiffel", {"w": 125, "d": 125, "h": 312}),
    ("sacre_coeur", -504, 3763, 7, 1914, 9999, "sacre_coeur", {"w": 85, "d": 100, "h": 83}),
    ("orsay", -1712, 775, 7, 1900, 9999, "station", {"w": 180, "d": 75, "h": 30}),
    ("stade_colombes", -8200, 6400, 30, 1907, 9999, "stadium", {"a": 120, "b": 80, "h": 18}),
    ("parc_des_princes", -6800, -1300, 30, 1972, 9999, "stadium", {"a": 130, "b": 100, "h": 30}),
    # modern
    ("tour_montparnasse", -2045, -1208, 7, 1973, 9999, "tower", {"w": 50, "d": 32, "h": 210}),
    ("grande_arche", -8352, 4408, 7, 1989, 9999, "arch_cube", {"w": 108, "d": 108, "h": 110}),
    ("centre_pompidou", 280, 700, 7, 1977, 9999, "box", {"w": 166, "d": 60, "h": 42}),
    ("bnf", 1882, -2116, 7, 1996, 9999, "bnf", {"w": 200, "d": 150, "h": 79}),
    ("stade_de_france", 748, 7960, 7, 1998, 9999, "stadium", {"a": 175, "b": 140, "h": 42}),
    ("orly", 1127, -14100, 0, 1946, 9999, "airport", {"runways": [(3600, 0, 0), (3320, 200, -30)]}),
    ("le_bourget", 6710, 12960, 0, 1919, 9999, "airport", {"runways": [(3000, 0, 60), (1800, 300, 20)]}),
    ("ministere_finances", 2350, -1650, 7, 1989, 9999, "box", {"w": 350, "d": 60, "h": 45}),
    ("paris_expo", -3900, -3600, 30, 1923, 9999, "box", {"w": 300, "d": 200, "h": 20}),
    ("palais_omnisports", 2500, -1950, 7, 1984, 9999, "box", {"w": 150, "d": 150, "h": 30}),
    ("philharmonie", 2500, 4600, 7, 2015, 9999, "box", {"w": 100, "d": 80, "h": 45}),
]
