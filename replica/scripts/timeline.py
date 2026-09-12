"""Time <-> year mapping and era labels, sampled from the reference video.

The reference is 180 s at 30 fps.  (t seconds, displayed year) pairs were read
off the video every 2 s; in between we interpolate linearly.
"""
import bisect

FPS = 30
DURATION = 180.0
TOTAL_FRAMES = int(DURATION * FPS)

# (t_seconds, year)
SAMPLES = [
    (0, -270), (2, -209), (4, -147), (6, -85), (8, -24), (10, 38), (12, 101),
    (14, 163), (16, 225), (18, 286), (20, 344), (22, 399), (24, 454), (26, 510),
    (28, 565), (30, 622), (32, 683), (34, 746), (36, 810), (38, 874), (40, 938),
    (42, 1001), (44, 1064), (46, 1127), (48, 1188), (50, 1247), (52, 1294),
    (54, 1337), (56, 1379), (58, 1421), (60, 1459), (62, 1492), (64, 1524),
    (66, 1555), (68, 1584), (70, 1607), (72, 1624), (74, 1639), (76, 1653),
    (78, 1667), (80, 1680), (82, 1694), (84, 1706), (86, 1718), (88, 1729),
    (90, 1740), (92, 1751), (94, 1761), (96, 1771), (98, 1777), (100, 1783),
    (102, 1789), (104, 1795), (106, 1800), (108, 1806), (110, 1811), (112, 1817),
    (114, 1822), (116, 1828), (118, 1834), (120, 1839), (122, 1845), (124, 1851),
    (126, 1857), (128, 1863), (130, 1869), (132, 1875), (134, 1881), (136, 1887),
    (138, 1895), (140, 1905), (142, 1917), (144, 1930), (146, 1942), (148, 1954),
    (150, 1966), (152, 1977), (154, 1988), (156, 1998), (158, 2006), (160, 2014),
    (162, 2020), (164, 2024), (166, 2025), (170, 2025),
]

# era label, first year it is shown
ERAS = [
    (-9999, "CELTIC ERA"),
    (52, "ROMAN ERA"),
    (508, "FRANKISH ERA"),
    (987, "MEDIEVAL ERA"),
    (1515, "MODERN ERA"),
    (1793, "NAPOLEONIC ERA"),
    (1841, "HAUSMANN ERA"),
    (1885, "INDUSTRIAL ERA"),
    (1950, "GLOBALIZATION ERA"),
]

_TS = [s[0] for s in SAMPLES]
_YS = [s[1] for s in SAMPLES]

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


def years_per_second(t):
    """Local rate, used to size the sprout animation in years."""
    return (year_at(t + 0.5) - year_at(t - 0.5))


if __name__ == "__main__":
    for t in range(0, 181, 10):
        print(t, round(year_at(t)), era_at(year_at(t)))
