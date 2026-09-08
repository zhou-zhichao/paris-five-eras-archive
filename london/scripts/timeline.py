"""Time <-> year mapping, era labels and population for the London film.

180 s at 30 fps like the reference format.  The year curve is authored as a few
key points (time, year) and sampled every 2 s for the Blender keyframes; the
pacing gives the eras with the most visible change the most screen time.
"""
import bisect

FPS = 30
DURATION = 180.0
TOTAL_FRAMES = int(DURATION * FPS)

# (t seconds, year) key points
KEYS = [
    (0, -60), (6, 20), (9, 43),                 # pre-Roman landscape, then Londinium is founded
    (14, 70), (18, 130), (24, 300), (28, 420),  # Roman rise, wall, decline and abandonment
    (34, 700), (38, 886),                       # Saxon Lundenwic, Alfred re-occupies the walls
    (44, 1066), (50, 1200), (56, 1300),         # Norman / medieval growth to the 1300 peak
    (60, 1400), (64, 1500), (70, 1600),         # plague, Tudor London
    (76, 1660), (80, 1666), (83, 1680), (86, 1700),   # the City rebuilt in brick after 1666, house by house
    (94, 1760), (102, 1800),                    # Georgian West End and East End
    (112, 1840), (120, 1860), (128, 1880), (136, 1900),  # Victorian explosion
    (142, 1914), (146, 1930), (150, 1945),      # Edwardian, interwar suburbia, Blitz
    (156, 1965), (160, 1985), (164, 2005), (166, 2025), (170, 2025),
]

SAMPLES = []
for _t in range(0, 172, 2):
    i = bisect.bisect_right([k[0] for k in KEYS], _t) - 1
    i = min(max(i, 0), len(KEYS) - 2)
    (t0, y0), (t1, y1) = KEYS[i], KEYS[i + 1]
    SAMPLES.append((_t, round(y0 + (y1 - y0) * (_t - t0) / (t1 - t0), 2)))

# era label, first year it is shown
ERAS = [
    (-9999, "PRE-ROMAN ERA"),
    (43, "ROMAN ERA"),
    (450, "SAXON ERA"),
    (1066, "NORMAN ERA"),
    (1200, "MEDIEVAL ERA"),
    (1485, "TUDOR ERA"),
    (1603, "STUART ERA"),
    (1714, "GEORGIAN ERA"),
    (1837, "VICTORIAN ERA"),
    (1901, "EDWARDIAN ERA"),
    (1919, "INTERWAR ERA"),
    (1945, "POSTWAR ERA"),
    (1986, "GLOBAL CITY ERA"),
]

# population (year, people) - Greater London area equivalents; sources: Museum of London,
# Wrigley, Finlay & Shearer, ONS census (see research/population.json)
POPULATION = [
    (-60, 2000), (43, 3000), (60, 10000), (100, 30000), (140, 45000), (200, 45000), (300, 25000),
    (400, 10000), (450, 2000), (600, 3000), (700, 8000), (800, 10000), (886, 8000), (1000, 12000),
    (1086, 18000), (1200, 30000), (1300, 80000), (1348, 80000), (1350, 45000), (1377, 45000),
    (1450, 50000), (1500, 55000), (1550, 90000), (1600, 200000), (1650, 400000), (1700, 575000),
    (1750, 700000), (1801, 1096784), (1811, 1303564), (1821, 1573210), (1831, 1878229), (1841, 2207653),
    (1851, 2651939), (1861, 3188485), (1871, 3840595), (1881, 4713441), (1891, 5572012), (1901, 6506889),
    (1911, 7160441), (1921, 7386755), (1931, 8110358), (1939, 8615245), (1951, 8196807), (1961, 7992443),
    (1971, 7452346), (1981, 6608598), (1991, 6887280), (2001, 7172091), (2011, 8173941), (2021, 8799728),
    (2025, 9000000),
]

_TS = [s[0] for s in SAMPLES]
_YS = [s[1] for s in SAMPLES]
_PY = [p[0] for p in POPULATION]
_PP = [p[1] for p in POPULATION]

# outro: the city dissolves into a wireframe grid and fades out
OUTRO_START = 168.5   # seconds: year counter frozen at 2025, grid wipe begins
FADE_OUT_START = 175.0
FADE_IN_END = 2.5


def year_at(t):
    """Continuous year for time t (seconds)."""
    if t <= _TS[0]:
        return float(_YS[0])
    if t >= _TS[-1]:
        return float(_YS[-1])
    i = bisect.bisect_right(_TS, t) - 1
    t0, t1 = _TS[i], _TS[i + 1]
    y0, y1 = _YS[i], _YS[i + 1]
    return y0 + (y1 - y0) * (t - t0) / (t1 - t0)


def year_at_frame(frame):
    return year_at(frame / FPS)


def t_of_year(year):
    """Inverse of year_at (seconds), clamped to the animated range."""
    if year <= _YS[0]:
        return float(_TS[0])
    if year >= _YS[-1]:
        return 166.0
    i = bisect.bisect_right(_YS, year) - 1
    while i < len(_YS) - 1 and _YS[i + 1] == _YS[i]:
        i += 1
    y0, y1 = _YS[i], _YS[i + 1]
    t0, t1 = _TS[i], _TS[i + 1]
    return t0 + (t1 - t0) * (year - y0) / (y1 - y0)


def sprout_years(year, seconds=1.4):
    """How many years a `seconds`-long sprout animation spans at this point in the film."""
    t = t_of_year(year)
    return max(1.0, year_at(t + seconds) - year_at(t))


def era_at(year):
    label = ERAS[0][1]
    for start, name in ERAS:
        if year >= start:
            label = name
    return label


def population_at(year):
    """Log-linear interpolation of the population series."""
    import math
    if year <= _PY[0]:
        return _PP[0]
    if year >= _PY[-1]:
        return _PP[-1]
    i = bisect.bisect_right(_PY, year) - 1
    y0, y1 = _PY[i], _PY[i + 1]
    p0, p1 = _PP[i], _PP[i + 1]
    f = (year - y0) / (y1 - y0)
    return int(round(math.exp(math.log(p0) + (math.log(p1) - math.log(p0)) * f)))


def population_label(year):
    p = population_at(year)
    if p >= 1_000_000:
        return f"POP. {p/1e6:.1f} M"
    if p >= 10000:
        return f"POP. {int(round(p, -3)):,}"
    return f"POP. {int(round(p, -2)):,}"


def years_per_second(t):
    """Local rate, used to size the sprout animation in years."""
    return (year_at(t + 0.5) - year_at(t - 0.5))


if __name__ == "__main__":
    for t in range(0, 181, 10):
        y = year_at(t)
        print(t, round(y), era_at(y), population_label(y))
