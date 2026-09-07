"""Landmark catalogue: hand-authored core list + researched landmarks.json -> LANDMARKS tuples.

Tuple format (shared with the Paris pipeline):
  (name, x, y, rot_deg_ccw_from_east, birth, death, builder, params)
builder is "glb:<model id>" (london/assets/models/<id>.glb, true-scale metres, long axis x,
front towards glTF +z = Blender -y) or a procedural builder name from landmarks.py.
"""
import json, math, os, struct

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "..", "assets", "models")
from terrain import ll

_bbox_cache = {}


def glb_bbox(model_id):
    """(w, d, h) of a GLB written by export_glb.mjs (POSITION accessor min/max), or None."""
    if model_id in _bbox_cache:
        return _bbox_cache[model_id]
    p = os.path.join(MODELS, model_id + ".glb")
    res = None
    if os.path.exists(p):
        try:
            with open(p, "rb") as fh:
                fh.read(12)
                ln, typ = struct.unpack("<II", fh.read(8))
                js = json.loads(fh.read(ln).decode("utf-8"))
            acc = js["accessors"][js["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
            mn, mx = acc["min"], acc["max"]
            res = (mx[0] - mn[0], mx[2] - mn[2], mx[1] - mn[1])
        except Exception as e:  # noqa
            print("[landmarks] bad glb", model_id, e)
    _bbox_cache[model_id] = res
    return res


def has_glb(model_id):
    return os.path.exists(os.path.join(MODELS, model_id + ".glb"))


def rot_from(front_bearing=None, axis_bearing=None):
    """ccw rotation (deg) from +x so that the model's front (-y) faces `front_bearing` (cw from north),
    or so that its long axis (x) lies along `axis_bearing`."""
    if front_bearing is not None:
        return (180.0 - front_bearing) % 360
    if axis_bearing is not None:
        return (90.0 - axis_bearing) % 360
    return 0.0


# ------------------------------------------------------------------ hand-authored core list
# (id, lon, lat, front_bearing (deg cw from N, None) | ("axis", bearing), birth, death, model, params)
# model: "glb:<id>" or procedural builder; when a glb is missing, the fallback builder in FALLBACK is used.
CORE = [
    # Roman
    ("roman_forum", -0.0855, 51.5128, 188, 100, 300, "glb:roman_forum_basilica", {"w": 167, "d": 167, "h": 25}),
    ("roman_forum_early", -0.0855, 51.5128, 188, 75, 100, "roman_forum", {"w": 100, "d": 60}),
    ("roman_amphitheatre", -0.0921, 51.5155, 188, 75, 350, "glb:roman_amphitheatre", {"a": 50, "b": 43}),
    ("roman_baths_huggin", -0.0955, 51.5115, 180, 80, 350, "roman_baths", {"w": 50, "d": 40}),
    ("roman_temple_mithras", -0.0905, 51.5125, 180, 240, 400, "roman_temple", {"w": 18, "d": 28, "h": 10}),
    ("governors_palace", -0.0905, 51.5100, 180, 90, 300, "roman_baths", {"w": 90, "d": 60}),
    ("ludgate", -0.1030, 51.5140, 270, 200, 1760, "glb:roman_gate", {"w": 40, "d": 14, "h": 9}),
    ("newgate", -0.1010, 51.5156, 285, 200, 1767, "glb:roman_gate", {"w": 40, "d": 14, "h": 9}),
    ("aldersgate", -0.0975, 51.5170, 330, 200, 1761, "glb:roman_gate", {"w": 40, "d": 14, "h": 9}),
    ("cripplegate", -0.0947, 51.5180, 0, 200, 1760, "glb:roman_gate", {"w": 40, "d": 14, "h": 9}),
    ("bishopsgate", -0.0815, 51.5176, 20, 200, 1760, "glb:roman_gate", {"w": 40, "d": 14, "h": 9}),
    ("aldgate", -0.0762, 51.5140, 70, 200, 1761, "glb:roman_gate", {"w": 40, "d": 14, "h": 9}),
    # Saxon / Norman / medieval
    ("westminster_abbey_saxon", -0.1273, 51.4993, 270, 1065, 1245, "glb:medieval_abbey", {"w": 100, "d": 60, "h": 25}),
    ("westminster_abbey_notowers", -0.1273, 51.4993, 270, 1269, 1745, "glb:westminster_abbey_notowers", {"w": 156, "d": 62, "h": 45}),
    ("westminster_abbey", -0.1273, 51.4993, 270, 1745, 9999, "glb:westminster_abbey", {"w": 156, "d": 62, "h": 69}),
    ("old_palace_of_westminster", -0.1246, 51.4995, 90, 1099, 1834, "glb:old_palace_of_westminster", {"w": 200, "d": 120, "h": 28}),
    ("old_st_pauls_spire", -0.0984, 51.5138, 270, 1240, 1561, "glb:old_st_pauls_spire", {"w": 178, "d": 90, "h": 149}),
    ("old_st_pauls_early", -0.0984, 51.5138, 270, 1087, 1240, "cathedral", {"w": 60, "d": 140, "h": 30, "towers": 0}),
    ("old_st_pauls_nospire", -0.0984, 51.5138, 270, 1561, 1666, "glb:old_st_pauls_nospire", {"w": 178, "d": 90, "h": 85}),
    ("tower_of_london", -0.0759, 51.5081, 180, 1100, 9999, "glb:tower_of_london", {"w": 200, "d": 180, "h": 36}),
    ("white_tower_early", -0.0759, 51.5081, 180, 1078, 1100, "castle", {"w": 36, "d": 32, "h": 20, "keep": 27}),
    ("southwark_cathedral", -0.0897, 51.5062, 0, 1220, 9999, "glb:southwark_cathedral", {"w": 80, "d": 30, "h": 50}),
    ("guildhall", -0.0917, 51.5156, 180, 1440, 9999, "glb:guildhall", {"w": 46, "d": 15, "h": 27}),
    ("temple_church", -0.1104, 51.5134, 180, 1185, 9999, "glb:temple_church", {"w": 42, "d": 18, "h": 20}),
    ("lambeth_palace", -0.1198, 51.4948, 270, 1495, 9999, "glb:lambeth_palace", {"w": 110, "d": 80, "h": 22}),
    ("lambeth_palace_early", -0.1198, 51.4948, 270, 1200, 1495, "abbey", {"w": 60, "d": 80, "h": 18}),
    ("baynards_castle", -0.1010, 51.5120, 180, 1428, 1666, "glb:baynards_castle", {"w": 100, "d": 60, "h": 20}),
    ("baynards_castle_norman", -0.1030, 51.5125, 180, 1066, 1213, "castle", {"w": 60, "d": 45, "h": 12, "keep": 20}),
    ("montfichet_tower", -0.1040, 51.5140, 180, 1070, 1276, "castle", {"w": 40, "d": 40, "h": 10, "keep": 18}),
    ("winchester_palace", -0.0910, 51.5068, 0, 1150, 1814, "glb:winchester_palace", {"w": 44, "d": 30, "h": 18}),
    ("st_bartholomew", -0.0999, 51.5188, 180, 1123, 9999, "glb:medieval_abbey", {"w": 75, "d": 40, "h": 25}),
    ("bermondsey_abbey", -0.0800, 51.4985, 0, 1090, 1541, "glb:medieval_abbey", {"w": 75, "d": 40, "h": 25}),
    ("holy_trinity_aldgate", -0.0770, 51.5142, 180, 1108, 1532, "glb:medieval_abbey", {"w": 75, "d": 40, "h": 25}),
    ("st_mary_spital", -0.0765, 51.5190, 180, 1197, 1539, "glb:medieval_abbey", {"w": 75, "d": 40, "h": 25}),
    ("clerkenwell_priory", -0.1030, 51.5225, 180, 1144, 1540, "glb:medieval_abbey", {"w": 75, "d": 40, "h": 25}),
    ("charterhouse", -0.0995, 51.5216, 180, 1371, 9999, "glb:medieval_abbey", {"w": 75, "d": 40, "h": 25}),
    ("greyfriars", -0.0985, 51.5165, 180, 1225, 1538, "glb:medieval_abbey", {"w": 75, "d": 40, "h": 25}),
    ("blackfriars", -0.1030, 51.5125, 180, 1278, 1538, "glb:medieval_abbey", {"w": 75, "d": 40, "h": 25}),
    ("austin_friars", -0.0865, 51.5160, 180, 1253, 1538, "glb:medieval_abbey", {"w": 75, "d": 40, "h": 25}),
    ("savoy_palace", -0.1195, 51.5105, 180, 1263, 1381, "glb:baynards_castle", {"w": 100, "d": 60, "h": 20}),
    ("eleanor_cross", -0.1276, 51.5077, 180, 1294, 1647, "glb:eleanor_cross_charing", {"w": 8, "d": 8, "h": 21}),
    ("crosby_hall", -0.0810, 51.5150, 180, 1466, 1908, "glb:crosby_hall", {"w": 21, "d": 12, "h": 16}),
    ("eltham_palace", 0.0500, 51.4463, 180, 1305, 9999, "palace_block", {"w": 60, "d": 30, "h": 14}),
    ("lundenwic_hall_a", -0.1225, 51.5120, 180, 640, 880, "glb:saxon_hall", {"w": 25, "d": 10, "h": 8}),
    ("lundenwic_hall_b", -0.1190, 51.5105, 200, 660, 880, "glb:saxon_hall", {"w": 25, "d": 10, "h": 8}),
    ("st_alban_wood_street", -0.0940, 51.5165, 180, 800, 1666, "glb:saxon_church", {"w": 25, "d": 9, "h": 18}),
    ("all_hallows_by_the_tower", -0.0797, 51.5094, 180, 675, 9999, "glb:saxon_church", {"w": 25, "d": 9, "h": 18}),
    ("st_pauls_saxon", -0.0984, 51.5138, 270, 604, 1087, "glb:saxon_church", {"w": 25, "d": 9, "h": 18}),
    # Tudor / Stuart
    ("whitehall_palace", -0.1258, 51.5052, 90, 1530, 1698, "glb:whitehall_palace", {"w": 400, "d": 150, "h": 20}),
    ("banqueting_house", -0.1259, 51.5044, 270, 1622, 9999, "glb:banqueting_house", {"w": 34, "d": 21, "h": 28}),
    ("st_james_palace", -0.1379, 51.5045, 180, 1536, 9999, "glb:st_james_palace", {"w": 130, "d": 110, "h": 25}),
    ("globe_theatre", -0.0955, 51.5075, 0, 1599, 1644, "glb:globe_theatre", {"w": 30, "d": 30, "h": 12}),
    ("globe_theatre_new", -0.0972, 51.5081, 0, 1997, 9999, "glb:globe_theatre", {"w": 30, "d": 30, "h": 12}),
    ("greenwich_palace", -0.0060, 51.4830, 0, 1500, 1662, "glb:greenwich_palace_placentia", {"w": 220, "d": 80, "h": 20}),
    ("greenwich_naval_college", -0.0060, 51.4830, 0, 1712, 9999, "glb:greenwich_royal_naval_college", {"w": 300, "d": 200, "h": 40}),
    ("bridewell_palace", -0.1055, 51.5125, 180, 1523, 1864, "palace_block", {"w": 80, "d": 60, "h": 16}),
    ("hampton_court", -0.3378, 51.4036, 180, 1515, 9999, "palace_block", {"w": 200, "d": 180, "h": 18}),
    ("somerset_house_old", -0.1173, 51.5109, 180, 1551, 1775, "palace_block", {"w": 120, "d": 80, "h": 16}),
    ("royal_exchange_1571", -0.0873, 51.5135, 180, 1571, 1666, "square_ring", {"w": 60, "d": 50, "h": 14}),
    ("royal_exchange_1669", -0.0873, 51.5135, 180, 1669, 1838, "square_ring", {"w": 65, "d": 55, "h": 16}),
    ("royal_exchange", -0.0873, 51.5135, 270, 1844, 9999, "glb:royal_exchange", {"w": 90, "d": 55, "h": 25}),
    # Wren / Georgian
    ("st_pauls_cathedral", -0.0984, 51.51385, 270, 1710, 9999, "glb:st_pauls_cathedral", {"w": 158, "d": 75, "h": 111}),
    ("monument", -0.0859, 51.5102, 180, 1677, 9999, "glb:monument", {"w": 8, "d": 8, "h": 62}),
    ("st_brides", -0.1056, 51.5138, 180, 1703, 9999, "glb:wren_church_bride", {"w": 35, "d": 18, "h": 69}),
    ("st_mary_le_bow", -0.0937, 51.5139, 180, 1680, 9999, "glb:wren_church_bow", {"w": 35, "d": 18, "h": 68}),
    ("st_magnus", -0.0865, 51.5093, 180, 1687, 9999, "glb:wren_church_generic", {"w": 35, "d": 18, "h": 45}),
    ("st_stephen_walbrook", -0.0899, 51.5127, 180, 1679, 9999, "glb:wren_church_generic", {"w": 35, "d": 18, "h": 45}),
    ("christ_church_greyfriars", -0.0985, 51.5165, 180, 1687, 1940, "glb:wren_church_generic", {"w": 35, "d": 18, "h": 45}),
    ("st_dunstan_east", -0.0790, 51.5098, 180, 1701, 1941, "glb:wren_church_generic", {"w": 35, "d": 18, "h": 45}),
    ("st_vedast", -0.0960, 51.5148, 180, 1712, 9999, "glb:wren_church_generic", {"w": 35, "d": 18, "h": 45}),
    ("st_james_garlickhythe", -0.0938, 51.5112, 180, 1717, 9999, "glb:wren_church_generic", {"w": 35, "d": 18, "h": 45}),
    ("st_lawrence_jewry", -0.0925, 51.5152, 180, 1677, 9999, "glb:wren_church_generic", {"w": 35, "d": 18, "h": 45}),
    ("st_michael_cornhill", -0.0855, 51.5133, 180, 1722, 9999, "glb:wren_church_generic", {"w": 35, "d": 18, "h": 45}),
    ("royal_hospital_chelsea", -0.1585, 51.4874, 180, 1692, 9999, "glb:royal_hospital_chelsea", {"w": 150, "d": 100, "h": 20}),
    ("kensington_palace", -0.1877, 51.5051, 90, 1695, 9999, "glb:kensington_palace", {"w": 120, "d": 100, "h": 18}),
    ("christ_church_spitalfields", -0.0746, 51.5189, 270, 1729, 9999, "glb:christ_church_spitalfields", {"w": 55, "d": 25, "h": 68}),
    ("st_martin_in_the_fields", -0.1267, 51.5089, 270, 1726, 9999, "glb:st_martin_in_the_fields", {"w": 50, "d": 25, "h": 59}),
    ("st_george_bloomsbury", -0.1246, 51.5170, 180, 1731, 9999, "glb:st_martin_in_the_fields", {"w": 40, "d": 25, "h": 50}),
    ("st_anne_limehouse", -0.0395, 51.5122, 180, 1730, 9999, "glb:christ_church_spitalfields", {"w": 50, "d": 25, "h": 60}),
    ("st_george_in_the_east", -0.0575, 51.5108, 180, 1729, 9999, "glb:christ_church_spitalfields", {"w": 50, "d": 25, "h": 50}),
    ("st_alfege_greenwich", -0.0095, 51.4805, 180, 1718, 9999, "glb:christ_church_spitalfields", {"w": 50, "d": 25, "h": 40}),
    ("buckingham_house", -0.1419, 51.5014, 90, 1705, 1826, "glb:buckingham_house", {"w": 60, "d": 30, "h": 15}),
    ("buckingham_palace", -0.1419, 51.5014, 90, 1850, 9999, "glb:buckingham_palace", {"w": 108, "d": 120, "h": 24}),
    ("mansion_house", -0.0893, 51.5132, 270, 1752, 9999, "glb:mansion_house", {"w": 60, "d": 40, "h": 25}),
    ("bank_of_england_early", -0.0885, 51.5142, 180, 1734, 1833, "palace_block", {"w": 40, "d": 30, "h": 14}),
    ("bank_of_england_soane", -0.0885, 51.5142, 180, 1833, 1925, "square_ring", {"w": 100, "d": 90, "h": 10}),
    ("bank_of_england", -0.0885, 51.5142, 180, 1939, 9999, "glb:bank_of_england", {"w": 100, "d": 90, "h": 30}),
    ("horse_guards", -0.1277, 51.5048, 90, 1759, 9999, "glb:horse_guards", {"w": 110, "d": 40, "h": 30}),
    ("somerset_house", -0.1173, 51.5109, 180, 1801, 9999, "glb:somerset_house", {"w": 150, "d": 100, "h": 22}),
    ("kew_pagoda", -0.2915, 51.4762, 180, 1762, 9999, "glb:kew_pagoda", {"w": 15, "d": 15, "h": 50}),
    ("newgate_prison", -0.1015, 51.5155, 90, 1782, 1902, "palace_block", {"w": 90, "d": 50, "h": 16}),
    ("millbank_penitentiary", -0.1275, 51.4911, 90, 1821, 1890, "castle", {"w": 200, "d": 200, "h": 12, "keep": 14}),
    ("carlton_house", -0.1315, 51.5065, 0, 1783, 1826, "palace_block", {"w": 60, "d": 40, "h": 16}),
    ("custom_house", -0.0800, 51.5088, 180, 1817, 9999, "palace_block", {"w": 150, "d": 40, "h": 18}),
    ("euston_arch", -0.1330, 51.5275, 180, 1837, 1961, "arch_cube", {"w": 22, "d": 8, "h": 22}),
    ("bethlem_hospital", -0.1088, 51.4960, 0, 1815, 9999, "domed_church", {"w": 70, "d": 40, "h": 18, "dome": 40}),
    # Victorian
    ("british_museum", -0.1270, 51.5194, 180, 1852, 9999, "glb:british_museum", {"w": 130, "d": 100, "h": 25}),
    ("national_gallery", -0.1283, 51.5089, 180, 1838, 9999, "glb:national_gallery", {"w": 140, "d": 50, "h": 20}),
    ("nelsons_column", -0.1281, 51.5077, 180, 1843, 9999, "glb:nelsons_column", {"w": 12, "d": 12, "h": 52}),
    ("marble_arch", -0.1589, 51.5131, 180, 1851, 9999, "glb:marble_arch", {"w": 14, "d": 6, "h": 14}),
    ("wellington_arch", -0.1508, 51.5025, 150, 1830, 9999, "glb:wellington_arch", {"w": 20, "d": 8, "h": 25}),
    ("palace_of_westminster", -0.1246, 51.4995, 90, 1860, 9999, "glb:palace_of_westminster", {"w": 265, "d": 120, "h": 98}),
    ("crystal_palace_sydenham", -0.0740, 51.4225, 90, 1854, 1936, "glb:crystal_palace_sydenham", {"w": 500, "d": 120, "h": 85}),
    ("crystal_palace_hyde_park", -0.1700, 51.5030, 180, 1851, 1852, "glb:crystal_palace_sydenham", {"w": 500, "d": 120, "h": 40}),
    ("st_pancras", -0.1257, 51.5308, 180, 1868, 9999, "glb:st_pancras", {"w": 213, "d": 150, "h": 82}),
    ("kings_cross", -0.1240, 51.5310, 180, 1852, 9999, "glb:kings_cross", {"w": 250, "d": 70, "h": 32}),
    ("paddington_station", -0.1774, 51.5166, 200, 1854, 9999, "glb:paddington_station", {"w": 210, "d": 100, "h": 30}),
    ("cannon_street_station", -0.0905, 51.5110, 180, 1866, 9999, "glb:cannon_street_station", {"w": 200, "d": 60, "h": 40}),
    ("charing_cross_station", -0.1246, 51.5076, 0, 1864, 9999, "glb:charing_cross_station", {"w": 150, "d": 60, "h": 30}),
    ("euston_station", -0.1330, 51.5281, 180, 1968, 9999, "box", {"w": 200, "d": 120, "h": 16}),
    ("euston_station_old", -0.1325, 51.5283, 180, 1838, 1963, "station", {"w": 120, "d": 200, "h": 20}),
    ("liverpool_street_station", -0.0817, 51.5179, 180, 1874, 9999, "station", {"w": 180, "d": 200, "h": 24}),
    ("victoria_station", -0.1440, 51.4952, 180, 1862, 9999, "station", {"w": 200, "d": 220, "h": 24}),
    ("waterloo_station", -0.1132, 51.5031, 180, 1848, 9999, "station", {"w": 220, "d": 240, "h": 24}),
    ("london_bridge_station", -0.0864, 51.5050, 0, 1836, 9999, "station", {"w": 180, "d": 180, "h": 20}),
    ("fenchurch_street_station", -0.0788, 51.5117, 180, 1841, 9999, "station", {"w": 90, "d": 120, "h": 18}),
    ("marylebone_station", -0.1631, 51.5225, 180, 1899, 9999, "station", {"w": 120, "d": 160, "h": 20}),
    ("royal_albert_hall", -0.1774, 51.5009, 180, 1871, 9999, "glb:royal_albert_hall", {"w": 83, "d": 72, "h": 41}),
    ("albert_memorial", -0.1776, 51.5024, 180, 1872, 9999, "glb:albert_memorial", {"w": 20, "d": 20, "h": 54}),
    ("natural_history_museum", -0.1763, 51.4967, 180, 1881, 9999, "glb:natural_history_museum", {"w": 200, "d": 90, "h": 60}),
    ("v_and_a", -0.1720, 51.4966, 180, 1909, 9999, "palace_block", {"w": 220, "d": 180, "h": 24}),
    ("imperial_institute", -0.1768, 51.4986, 180, 1893, 1962, "glb:imperial_institute", {"w": 210, "d": 60, "h": 85}),
    ("queens_tower", -0.1768, 51.4986, 180, 1962, 9999, "glb:queens_tower", {"w": 20, "d": 20, "h": 85}),
    ("royal_courts_of_justice", -0.1132, 51.5136, 180, 1882, 9999, "glb:royal_courts_of_justice", {"w": 140, "d": 100, "h": 60}),
    ("westminster_cathedral", -0.1395, 51.4958, 180, 1903, 9999, "glb:westminster_cathedral", {"w": 110, "d": 50, "h": 87}),
    ("alexandra_palace", -0.1305, 51.5942, 180, 1875, 9999, "glb:alexandra_palace", {"w": 300, "d": 130, "h": 40}),
    ("old_bailey", -0.1020, 51.5155, 270, 1907, 9999, "glb:old_bailey", {"w": 80, "d": 60, "h": 67}),
    ("smithfield_market", -0.1017, 51.5188, 180, 1868, 9999, "glb:smithfield_market", {"w": 190, "d": 75, "h": 20}),
    ("harrods", -0.1634, 51.4994, 0, 1905, 9999, "glb:harrods", {"w": 150, "d": 100, "h": 30}),
    ("tate_britain", -0.1275, 51.4911, 90, 1897, 9999, "glb:tate_britain", {"w": 120, "d": 90, "h": 20}),
    ("tower_bridge_lm", -0.0753, 51.5056, None, 1894, 9999, None, {}),   # placeholder: bridges are built from BRIDGES
    ("foreign_office", -0.1275, 51.5030, 90, 1868, 9999, "palace_block", {"w": 160, "d": 120, "h": 24}),
    ("admiralty_arch", -0.1281, 51.5069, 45, 1912, 9999, "arch_cube", {"w": 60, "d": 20, "h": 22}),
    ("selfridges", -0.1526, 51.5145, 180, 1909, 9999, "box", {"w": 150, "d": 80, "h": 28}),
    ("savoy_hotel", -0.1200, 51.5103, 180, 1889, 9999, "box", {"w": 100, "d": 70, "h": 35}),
    ("lords", -0.1727, 51.5294, 180, 1814, 9999, "stadium", {"a": 90, "b": 75, "h": 14}),
    ("the_oval", -0.1150, 51.4838, 180, 1845, 9999, "stadium", {"a": 95, "b": 80, "h": 14}),
    ("stamford_bridge", -0.1910, 51.4817, 180, 1905, 9999, "stadium", {"a": 110, "b": 90, "h": 22}),
    ("highbury", -0.1027, 51.5575, 180, 1913, 2006, "stadium", {"a": 100, "b": 75, "h": 18}),
    ("white_city_stadium", -0.2260, 51.5135, 180, 1908, 1985, "stadium", {"a": 180, "b": 110, "h": 16}),
    ("twickenham", -0.3415, 51.4560, 180, 1909, 9999, "stadium", {"a": 130, "b": 110, "h": 30}),
    ("tottenham_stadium", -0.0665, 51.6043, 180, 2019, 9999, "stadium", {"a": 130, "b": 110, "h": 35}),
    ("white_hart_lane", -0.0665, 51.6043, 180, 1899, 2017, "stadium", {"a": 100, "b": 80, "h": 18}),
    ("county_hall", -0.1195, 51.5015, 90, 1922, 9999, "glb:county_hall", {"w": 230, "d": 100, "h": 30}),
    ("bush_house", -0.1170, 51.5127, 0, 1935, 9999, "palace_block", {"w": 120, "d": 60, "h": 30}),
    ("broadcasting_house", -0.1436, 51.5183, 180, 1932, 9999, "box", {"w": 60, "d": 40, "h": 34}),
    ("senate_house", -0.1289, 51.5210, 180, 1937, 9999, "glb:senate_house", {"w": 120, "d": 40, "h": 64}),
    ("battersea_a", -0.1445, 51.4820, 0, 1935, 1955, "glb:battersea_a", {"w": 160, "d": 85, "h": 103}),
    ("battersea_b", -0.1445, 51.4820, 0, 1955, 9999, "glb:battersea_b", {"w": 160, "d": 170, "h": 103}),
    ("bankside_power_station", -0.0994, 51.5076, 0, 1953, 2000, "glb:tate_modern", {"w": 200, "d": 100, "h": 99}),
    ("tate_modern", -0.0994, 51.5076, 0, 2000, 9999, "glb:tate_modern", {"w": 200, "d": 100, "h": 99}),
    ("wembley_old", -0.2796, 51.5560, 180, 1923, 2002, "glb:wembley_old", {"w": 300, "d": 250, "h": 35}),
    ("wembley_stadium", -0.2796, 51.5560, 180, 2007, 9999, "glb:wembley_stadium", {"w": 315, "d": 275, "h": 133}),
    ("croydon_airport", -0.1160, 51.3565, 0, 1928, 1959, "airport", {"runways": [(1200, 0, 20)]}),
    ("heathrow_old", -0.4543, 51.4700, 0, 1955, 9999, "glb:heathrow_old", {"w": 400, "d": 200, "h": 20}),
    ("heathrow_terminal", -0.4880, 51.4723, 0, 2008, 9999, "glb:heathrow_terminal", {"w": 400, "d": 180, "h": 87}),
    ("heathrow", -0.4600, 51.4700, 0, 1946, 9999, "airport", {"runways": [(3900, 450, 0), (3660, -900, 0)]}),
    ("london_city_airport", 0.0553, 51.5048, 180, 1987, 9999, "airport", {"runways": [(1500, 0, 90)]}),
    # postwar / modern
    ("southbank_centre", -0.1160, 51.5060, 0, 1951, 9999, "glb:southbank_centre", {"w": 500, "d": 150, "h": 30}),
    ("shell_centre", -0.1163, 51.5028, 0, 1961, 9999, "glb:shell_centre", {"w": 60, "d": 40, "h": 107}),
    ("millbank_tower", -0.1258, 51.4924, 90, 1963, 9999, "glb:millbank_tower", {"w": 50, "d": 25, "h": 118}),
    ("bt_tower", -0.1389, 51.5215, 180, 1964, 9999, "glb:bt_tower", {"w": 20, "d": 20, "h": 189}),
    ("centre_point", -0.1300, 51.5163, 180, 1966, 9999, "glb:centre_point", {"w": 50, "d": 20, "h": 117}),
    ("barbican_estate", -0.0937, 51.5200, 180, 1976, 9999, "glb:barbican_estate", {"w": 500, "d": 350, "h": 123}),
    ("trellick_tower", -0.2058, 51.5240, 180, 1972, 9999, "glb:trellick_tower", {"w": 60, "d": 20, "h": 98}),
    ("balfron_tower", -0.0107, 51.5140, 180, 1967, 9999, "glb:trellick_tower", {"w": 60, "d": 20, "h": 84}),
    ("guys_tower", -0.0876, 51.5033, 180, 1974, 9999, "glb:guys_tower", {"w": 50, "d": 30, "h": 143}),
    ("tower_42", -0.0838, 51.5153, 180, 1980, 9999, "glb:tower_42", {"w": 55, "d": 55, "h": 183}),
    ("lloyds_building", -0.0824, 51.5131, 180, 1986, 9999, "glb:lloyds_building", {"w": 70, "d": 50, "h": 95}),
    ("thames_barrier", 0.0370, 51.4974, ("axis", 145), 1982, 9999, "glb:thames_barrier", {"w": 520, "d": 30, "h": 20}),
    ("one_canada_square", -0.0195, 51.5049, 180, 1991, 9999, "glb:one_canada_square", {"w": 55, "d": 55, "h": 235}),
    ("canary_wharf_pair", -0.0195, 51.5049, 180, 2002, 9999, "glb:canary_wharf_pair", {"w": 200, "d": 100, "h": 200}),
    ("newfoundland", -0.0248, 51.5035, 180, 2021, 9999, "glb:newfoundland", {"w": 40, "d": 30, "h": 220}),
    ("landmark_pinnacle", -0.0259, 51.5015, 180, 2020, 9999, "glb:landmark_pinnacle", {"w": 40, "d": 25, "h": 233}),
    ("one_park_drive", -0.0135, 51.5023, 180, 2019, 9999, "glb:one_park_drive", {"w": 40, "d": 40, "h": 205}),
    ("sis_building", -0.1240, 51.4874, 90, 1994, 9999, "glb:sis_building", {"w": 110, "d": 70, "h": 50}),
    ("millennium_dome", 0.0032, 51.5030, 180, 1999, 9999, "glb:millennium_dome", {"w": 365, "d": 365, "h": 100}),
    ("london_eye", -0.1196, 51.5033, 90, 2000, 9999, "glb:london_eye", {"w": 135, "d": 30, "h": 135}),
    ("excel_centre", 0.0295, 51.5083, 180, 2000, 9999, "glb:excel_centre", {"w": 500, "d": 150, "h": 25}),
    ("city_hall", -0.0785, 51.5045, 0, 2002, 9999, "glb:city_hall", {"w": 50, "d": 50, "h": 45}),
    ("gherkin", -0.0803, 51.5145, 180, 2004, 9999, "glb:gherkin", {"w": 56, "d": 56, "h": 180}),
    ("emirates_stadium", -0.1084, 51.5549, 180, 2006, 9999, "glb:emirates_stadium", {"w": 250, "d": 200, "h": 40}),
    ("broadgate_tower", -0.0793, 51.5205, 180, 2008, 9999, "glb:broadgate_tower", {"w": 60, "d": 30, "h": 165}),
    ("strata_se1", -0.0995, 51.4928, 180, 2010, 9999, "glb:strata_se1", {"w": 40, "d": 30, "h": 148}),
    ("heron_tower", -0.0813, 51.5163, 180, 2011, 9999, "glb:heron_tower", {"w": 50, "d": 40, "h": 230}),
    ("london_stadium", -0.0166, 51.5386, 180, 2011, 9999, "glb:london_stadium", {"w": 315, "d": 256, "h": 45}),
    ("orbit", -0.0133, 51.5385, 180, 2012, 9999, "glb:orbit", {"w": 40, "d": 40, "h": 115}),
    ("westfield_stratford", -0.0077, 51.5432, 180, 2011, 9999, "glb:westfield_stratford", {"w": 500, "d": 200, "h": 25}),
    ("shard", -0.0865, 51.5045, 180, 2012, 9999, "glb:shard", {"w": 60, "d": 55, "h": 310}),
    ("walkie_talkie", -0.0836, 51.5112, 180, 2014, 9999, "glb:walkie_talkie", {"w": 60, "d": 40, "h": 160}),
    ("cheesegrater", -0.0819, 51.5138, 180, 2014, 9999, "glb:cheesegrater", {"w": 60, "d": 50, "h": 225}),
    ("st_george_wharf_tower", -0.1268, 51.4858, 180, 2014, 9999, "glb:st_george_wharf_tower", {"w": 40, "d": 40, "h": 181}),
    ("scalpel", -0.0827, 51.5129, 180, 2018, 9999, "glb:scalpel", {"w": 50, "d": 40, "h": 190}),
    ("one_blackfriars", -0.1046, 51.5075, 0, 2018, 9999, "glb:one_blackfriars", {"w": 50, "d": 40, "h": 163}),
    ("twentytwo_bishopsgate", -0.0830, 51.5150, 180, 2020, 9999, "glb:twentytwo_bishopsgate", {"w": 70, "d": 60, "h": 278}),
    ("gasholder_kings_cross", -0.1265, 51.5365, 180, 1867, 1999, "glb:gasholder", {"w": 60, "d": 60, "h": 40}),
    ("gasholder_old_kent_road", -0.0640, 51.4880, 180, 1879, 9999, "glb:gasholder", {"w": 60, "d": 60, "h": 40}),
    ("gasholder_bromley_by_bow", -0.0055, 51.5230, 180, 1872, 9999, "glb:gasholder", {"w": 60, "d": 60, "h": 40}),
    ("gasholder_beckton", 0.0650, 51.5170, 180, 1870, 1985, "glb:gasholder", {"w": 60, "d": 60, "h": 40}),
    ("gasholder_fulham", -0.1980, 51.4790, 180, 1830, 9999, "glb:gasholder", {"w": 60, "d": 60, "h": 40}),
]

# procedural fallbacks when a glb is not (yet) available, keyed by glb id
FALLBACK = {
    "roman_forum_basilica": ("roman_forum", {"w": 167, "d": 167}), "roman_amphitheatre": ("roman_amphitheatre", {"a": 50, "b": 43}),
    "roman_gate": ("castle", {"w": 30, "d": 12, "h": 6, "keep": 9}), "medieval_abbey": ("abbey", {"w": 75, "d": 40, "h": 22}),
    "saxon_church": ("basilica", {"w": 9, "d": 25, "h": 10}), "saxon_hall": ("box", {"w": 25, "d": 10, "h": 6}),
    "westminster_abbey_notowers": ("cathedral", {"w": 62, "d": 156, "h": 30, "towers": 0}),
    "westminster_abbey": ("cathedral", {"w": 62, "d": 156, "h": 30, "towers": 2}),
    "old_palace_of_westminster": ("palace_block", {"w": 200, "d": 120, "h": 16}),
    "old_st_pauls_spire": ("cathedral", {"w": 90, "d": 178, "h": 40, "towers": 2}),
    "old_st_pauls_nospire": ("cathedral", {"w": 90, "d": 178, "h": 40, "towers": 2}),
    "tower_of_london": ("castle", {"w": 200, "d": 180, "h": 12, "keep": 30}),
    "southwark_cathedral": ("cathedral", {"w": 30, "d": 80, "h": 22, "towers": 1}), "guildhall": ("basilica", {"w": 15, "d": 46, "h": 18}),
    "temple_church": ("domed_church", {"w": 18, "d": 42, "h": 12, "dome": 20}), "lambeth_palace": ("palace_block", {"w": 110, "d": 80, "h": 16}),
    "baynards_castle": ("castle", {"w": 100, "d": 60, "h": 12, "keep": 20}), "winchester_palace": ("palace_block", {"w": 44, "d": 30, "h": 12}),
    "eleanor_cross_charing": ("box", {"w": 6, "d": 6, "h": 21}), "crosby_hall": ("basilica", {"w": 12, "d": 21, "h": 10}),
    "whitehall_palace": ("palace_block", {"w": 400, "d": 150, "h": 14}), "banqueting_house": ("box", {"w": 34, "d": 21, "h": 28}),
    "st_james_palace": ("palace_block", {"w": 130, "d": 110, "h": 16}), "globe_theatre": ("stadium", {"a": 15, "b": 15, "h": 11}),
    "greenwich_palace_placentia": ("palace_block", {"w": 220, "d": 80, "h": 16}), "greenwich_royal_naval_college": ("invalides", {"w": 300, "d": 200, "h": 20, "dome": 40}),
    "royal_exchange": ("palace_block", {"w": 90, "d": 55, "h": 20}), "st_pauls_cathedral": ("domed_church", {"w": 90, "d": 158, "h": 33, "dome": 111}),
    "monument": ("box", {"w": 8, "d": 8, "h": 62}), "wren_church_bride": ("basilica", {"w": 18, "d": 35, "h": 14}),
    "wren_church_bow": ("basilica", {"w": 18, "d": 35, "h": 14}), "wren_church_generic": ("basilica", {"w": 18, "d": 35, "h": 12}),
    "royal_hospital_chelsea": ("palace_block", {"w": 150, "d": 100, "h": 14}), "kensington_palace": ("palace_block", {"w": 120, "d": 100, "h": 14}),
    "christ_church_spitalfields": ("basilica", {"w": 25, "d": 55, "h": 18}), "st_martin_in_the_fields": ("basilica", {"w": 25, "d": 50, "h": 16}),
    "buckingham_house": ("palace_block", {"w": 60, "d": 30, "h": 12}), "buckingham_palace": ("palace_block", {"w": 108, "d": 120, "h": 24}),
    "mansion_house": ("palace_block", {"w": 60, "d": 40, "h": 20}), "bank_of_england": ("palace_block", {"w": 100, "d": 90, "h": 24}),
    "horse_guards": ("palace_block", {"w": 110, "d": 40, "h": 18}), "somerset_house": ("palace_block", {"w": 150, "d": 100, "h": 22}),
    "kew_pagoda": ("tower", {"w": 15, "d": 15, "h": 50}), "british_museum": ("palace_block", {"w": 130, "d": 100, "h": 22}),
    "national_gallery": ("palace_block", {"w": 140, "d": 50, "h": 18}), "nelsons_column": ("box", {"w": 6, "d": 6, "h": 52}),
    "marble_arch": ("arch_cube", {"w": 14, "d": 6, "h": 14}), "wellington_arch": ("arch_cube", {"w": 20, "d": 8, "h": 25}),
    "palace_of_westminster": ("palace_block", {"w": 265, "d": 120, "h": 24}), "crystal_palace_sydenham": ("station", {"w": 500, "d": 120, "h": 30}),
    "st_pancras": ("station", {"w": 213, "d": 150, "h": 30, "tower": 82}), "kings_cross": ("station", {"w": 250, "d": 70, "h": 28}),
    "paddington_station": ("station", {"w": 210, "d": 100, "h": 28}), "cannon_street_station": ("station", {"w": 200, "d": 60, "h": 28, "tower": 40}),
    "charing_cross_station": ("station", {"w": 150, "d": 60, "h": 28}), "royal_albert_hall": ("stadium", {"a": 42, "b": 36, "h": 30}),
    "albert_memorial": ("box", {"w": 20, "d": 20, "h": 54}), "natural_history_museum": ("palace_block", {"w": 200, "d": 90, "h": 24}),
    "imperial_institute": ("palace_block", {"w": 210, "d": 60, "h": 22}), "queens_tower": ("tower", {"w": 20, "d": 20, "h": 85}),
    "royal_courts_of_justice": ("palace_block", {"w": 140, "d": 100, "h": 24}), "westminster_cathedral": ("domed_church", {"w": 50, "d": 110, "h": 25, "dome": 40}),
    "alexandra_palace": ("palace_block", {"w": 300, "d": 130, "h": 24}), "old_bailey": ("domed_church", {"w": 60, "d": 80, "h": 25, "dome": 45}),
    "smithfield_market": ("station", {"w": 190, "d": 75, "h": 16}), "harrods": ("box", {"w": 150, "d": 100, "h": 30}),
    "tate_britain": ("palace_block", {"w": 120, "d": 90, "h": 18}), "county_hall": ("palace_block", {"w": 230, "d": 100, "h": 28}),
    "senate_house": ("tower", {"w": 40, "d": 30, "h": 64}), "battersea_a": ("box", {"w": 160, "d": 85, "h": 50}), "battersea_b": ("box", {"w": 160, "d": 170, "h": 50}),
    "tate_modern": ("box", {"w": 200, "d": 100, "h": 35}), "wembley_old": ("stadium", {"a": 150, "b": 125, "h": 25}), "wembley_stadium": ("stadium", {"a": 157, "b": 137, "h": 52}),
    "heathrow_old": ("box", {"w": 400, "d": 200, "h": 20}), "heathrow_terminal": ("box", {"w": 400, "d": 180, "h": 40}),
    "southbank_centre": ("box", {"w": 500, "d": 150, "h": 25}), "shell_centre": ("tower", {"w": 60, "d": 40, "h": 107}),
    "millbank_tower": ("tower", {"w": 50, "d": 25, "h": 118}), "bt_tower": ("tower", {"w": 16, "d": 16, "h": 177}), "centre_point": ("tower", {"w": 50, "d": 20, "h": 117}),
    "barbican_estate": ("bnf", {"w": 400, "d": 300, "h": 123}), "trellick_tower": ("tower", {"w": 60, "d": 20, "h": 98}), "guys_tower": ("tower", {"w": 50, "d": 30, "h": 143}),
    "tower_42": ("tower", {"w": 55, "d": 55, "h": 183}), "lloyds_building": ("tower", {"w": 70, "d": 50, "h": 95}), "thames_barrier": ("box", {"w": 520, "d": 30, "h": 20}),
    "one_canada_square": ("tower", {"w": 55, "d": 55, "h": 235}), "canary_wharf_pair": ("bnf", {"w": 200, "d": 100, "h": 200}),
    "newfoundland": ("tower", {"w": 40, "d": 30, "h": 220}), "landmark_pinnacle": ("tower", {"w": 40, "d": 25, "h": 233}), "one_park_drive": ("tower", {"w": 40, "d": 40, "h": 205}),
    "sis_building": ("box", {"w": 110, "d": 70, "h": 50}), "millennium_dome": ("stadium", {"a": 182, "b": 182, "h": 50}), "london_eye": ("tower", {"w": 30, "d": 10, "h": 135}),
    "excel_centre": ("box", {"w": 500, "d": 150, "h": 25}), "city_hall": ("box", {"w": 50, "d": 50, "h": 45}), "gherkin": ("tower", {"w": 56, "d": 56, "h": 180}),
    "emirates_stadium": ("stadium", {"a": 125, "b": 100, "h": 40}), "broadgate_tower": ("tower", {"w": 60, "d": 30, "h": 165}),
    "strata_se1": ("tower", {"w": 40, "d": 30, "h": 148}), "heron_tower": ("tower", {"w": 50, "d": 40, "h": 230}), "london_stadium": ("stadium", {"a": 157, "b": 128, "h": 45}),
    "orbit": ("tower", {"w": 30, "d": 30, "h": 115}), "westfield_stratford": ("box", {"w": 500, "d": 200, "h": 25}), "shard": ("tower", {"w": 60, "d": 55, "h": 310}),
    "walkie_talkie": ("tower", {"w": 60, "d": 40, "h": 160}), "cheesegrater": ("tower", {"w": 60, "d": 50, "h": 225}), "st_george_wharf_tower": ("tower", {"w": 40, "d": 40, "h": 181}),
    "scalpel": ("tower", {"w": 50, "d": 40, "h": 190}), "one_blackfriars": ("tower", {"w": 50, "d": 40, "h": 163}), "twentytwo_bishopsgate": ("tower", {"w": 70, "d": 60, "h": 278}),
    "gasholder": ("tower", {"w": 60, "d": 60, "h": 40}),
}

# builder for researched landmark types without a specific model
TYPE_BUILDER = {
    "church": ("basilica", 1), "cathedral": ("cathedral", 1), "abbey": ("abbey", 1), "palace": ("palace_block", 1), "castle": ("castle", 1),
    "fort": ("castle", 1), "hall": ("palace_block", 1), "tower": ("tower", 1), "skyscraper": ("tower", 1), "station": ("station", 1),
    "museum": ("palace_block", 1), "monument": ("box", 1), "column": ("box", 1), "arch": ("arch_cube", 1), "stadium": ("stadium", 1),
    "dome": ("domed_church", 1), "power_station": ("box", 1), "market": ("station", 1), "exchange": ("palace_block", 1),
    "theatre": ("box", 1), "hospital": ("palace_block", 1), "prison": ("castle", 1), "industrial": ("box", 1), "arena": ("stadium", 1),
    "other": ("box", 1),
}


def _entry(name, lon, lat, front, birth, death, model, prm):
    x, y = ll(lon, lat)
    if isinstance(front, tuple):
        rot = rot_from(axis_bearing=front[1])
    else:
        rot = rot_from(front_bearing=front if front is not None else 180)
    if model is None:
        return None
    if model.startswith("glb:"):
        mid = model[4:]
        if has_glb(mid):
            w, d, h = glb_bbox(mid) or (prm.get("w", 50), prm.get("d", 50), prm.get("h", 20))
            p = dict(prm); p.update({"w": w, "d": d, "h": h})
            return (name, x, y, rot, birth, death, model, p)
        fb = FALLBACK.get(mid)
        if fb is None:
            return None
        return (name, x, y, rot, birth, death, fb[0], dict(fb[1]))
    return (name, x, y, rot, birth, death, model, dict(prm))


def build_landmark_list(research):
    out, taken = [], []
    for (name, lon, lat, front, birth, death, model, prm) in CORE:
        e = _entry(name, lon, lat, front, birth, death, model, prm)
        if e:
            out.append(e); taken.append((e[1], e[2], birth, death))
    if research:
        items = research.get("landmarks", research) if isinstance(research, dict) else research
        core_ids = {c[0] for c in CORE}
        AREA_WORDS = ("park", "square", "gardens", "terrace", "estate", "docks", "dock", "common", "fields", "cemetery", "heath", "market_area", "reservoir")
        n_add = 0
        for r in items:
            try:
                if r.get("importance", 3) > 2 or r.get("type") in ("bridge", "wall_gate", "roman", "wheel", "airport"):
                    continue
                if r["id"] in core_ids:
                    continue                      # hand-authored entry (with its model) wins
                fw_ = float(r.get("footprint_w_m") or 0); fd_ = float(r.get("footprint_d_m") or 0)
                if float(r.get("height_m") or 0) <= 0.5:
                    continue                      # open spaces, docks, sites
                if fw_ * fd_ > 60000 and r.get("type") in ("other", "industrial", "hall"):
                    continue                      # parks / squares / dock basins described as landmarks
                if any(w in r["id"] for w in AREA_WORDS) and r.get("type") in ("other", "industrial"):
                    continue
                x, y = ll(r["lon"], r["lat"])
                if abs(x) > 26000 or abs(y) > 20000:
                    continue
                birth = int(r["birth"]); death = int(r["death"]) if r.get("death") else 9999
                # skip if a core entry already covers this spot in this period
                if any(math.hypot(x - tx, y - ty) < 90 and birth < td and death > tb for tx, ty, tb, td in taken):
                    continue
                typ = r.get("type", "other")
                if typ not in TYPE_BUILDER:
                    continue
                b, _ = TYPE_BUILDER[typ]
                w = float(r.get("footprint_w_m") or 40); d = float(r.get("footprint_d_m") or 25); h = float(r.get("height_m") or 15)
                top = float(r.get("spire_or_tower_h_m") or 0)
                prm = {"w": w, "d": d, "h": h}
                if b == "cathedral":
                    prm["towers"] = 2 if top > h * 1.5 else 1
                if b == "stadium":
                    prm = {"a": w / 2, "b": d / 2, "h": h}
                if b == "tower" and top > h:
                    prm["h"] = top
                if b == "domed_church":
                    prm["dome"] = top or h * 1.5
                if b == "castle":
                    prm["keep"] = top or h * 1.4
                front = r.get("front_bearing_deg")
                axis = r.get("orientation_deg")
                rot = rot_from(front_bearing=front) if front is not None else rot_from(axis_bearing=axis if axis is not None else 90)
                out.append((r["id"], x, y, rot, birth, death, b, prm)); taken.append((x, y, birth, death)); n_add += 1
            except Exception as ex:  # noqa
                print("[landmarks] bad research entry", r.get("id"), ex)
        print(f"[landmarks] core {len(CORE)} + researched {n_add}")
    return out


if __name__ == "__main__":
    import sys
    sys.path.insert(0, HERE)
    L = build_landmark_list(None)
    glb = sum(1 for e in L if e[6].startswith("glb:"))
    print(len(L), "landmarks,", glb, "with GLB models")
