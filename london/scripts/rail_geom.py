"""Railway geometry for Blender (build_scene side): ballast + rails, viaduct arches, embankments, platforms.

All functions return (verts (N,3), faces (M,4), material index (M,), birth (M,)) numpy arrays so the caller
can concatenate them into one mesh with a FaceLife modifier.
"""
import numpy as np

MAT_BALLAST, MAT_RAIL, MAT_BRICK, MAT_EMBANK, MAT_PLATFORM, MAT_DECK = 0, 1, 2, 3, 4, 5

RAIL_GAUGE = 2.6      # exaggerated (buildings are drawn 2x): the two rails read as a double line
RAIL_W = 0.55
BALLAST_W = 5.6
TRACK_SPACING = 4.4   # multi-track ways: extra tracks side by side


def _col(w, n):
    w = np.asarray(w, dtype=np.float32)
    return w.reshape(-1, 1) if w.ndim == 1 and len(w) == n else w


def _strip(p0, p1, w, z0, z1, mat, birth, ext=0.0):
    w = _col(w, len(p0))
    d = p1 - p0
    L = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    t = d / L
    nrm = np.stack([-t[:, 1], t[:, 0]], axis=1)
    e = t * ext
    a = p0 - e - nrm * w / 2; b = p1 + e - nrm * w / 2; c = p1 + e + nrm * w / 2; dd = p0 - e + nrm * w / 2
    n = len(p0)
    verts = np.concatenate([np.column_stack([a, z0]), np.column_stack([b, z1]), np.column_stack([c, z1]), np.column_stack([dd, z0])])
    faces = np.stack([np.arange(n), np.arange(n) + n, np.arange(n) + 2 * n, np.arange(n) + 3 * n], axis=1)
    return verts, faces, np.full(n, mat, dtype=np.int32), birth


def _box_along(p0, p1, w, zb, zt, mat, birth):
    """closed box between p0->p1 (N pieces): 4 sides + top + bottom."""
    w = _col(w, len(p0))
    n = len(p0)
    zb = np.broadcast_to(np.asarray(zb, dtype=np.float32), (n,)); zt = np.broadcast_to(np.asarray(zt, dtype=np.float32), (n,))
    d = p1 - p0
    L = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    t = d / L; nrm = np.stack([-t[:, 1], t[:, 0]], axis=1)
    p0 = p0 - t * 0.9; p1 = p1 + t * 0.9          # pieces overlap a little so the joints on curves do not show
    a = p0 - nrm * w / 2; b = p1 - nrm * w / 2; c = p1 + nrm * w / 2; dd = p0 + nrm * w / 2
    lo = [np.column_stack([q, zb]) for q in (a, b, c, dd)]
    hi = [np.column_stack([q, zt]) for q in (a, b, c, dd)]
    verts = np.concatenate(lo + hi)
    i = np.arange(n)
    A, B, C, D = i, i + n, i + 2 * n, i + 3 * n
    A2, B2, C2, D2 = A + 4 * n, B + 4 * n, C + 4 * n, D + 4 * n
    faces = np.concatenate([
        np.stack([A2, B2, C2, D2], axis=1),        # top
        np.stack([D, C, B, A], axis=1),            # bottom
        np.stack([A, B, B2, A2], axis=1), np.stack([B, C, C2, B2], axis=1),
        np.stack([C, D, D2, C2], axis=1), np.stack([D, A, A2, D2], axis=1)])
    return verts, faces, np.full(len(faces), mat, dtype=np.int32), np.tile(birth, 6)


def _offset(p0, p1, off):
    off = _col(off, len(p0))
    d = p1 - p0
    L = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    t = d / L; nrm = np.stack([-t[:, 1], t[:, 0]], axis=1)
    return p0 + nrm * off, p1 + nrm * off


def _chains(pieces, zg0, zg1):
    """Join consecutive pieces of one way (shared end points, same attributes) into polylines:
    list of (pts (N,2), z_ground (N,), birth, elev, kind, ntr)."""
    out = []
    n = len(pieces)
    i = 0
    while i < n:
        j = i
        while (j + 1 < n and abs(pieces[j + 1, 0] - pieces[j, 2]) < 0.05 and abs(pieces[j + 1, 1] - pieces[j, 3]) < 0.05
               and np.all(pieces[j + 1, 4:8] == pieces[j, 4:8])):
            j += 1
        pts = np.concatenate([pieces[i:j + 1, 0:2], pieces[j:j + 1, 2:4]]).astype(np.float64)
        zg = np.concatenate([zg0[i:j + 1], zg1[j:j + 1]]).astype(np.float64)
        out.append((pts, zg, float(pieces[i, 4]), int(pieces[i, 5]), int(pieces[i, 6]), int(np.clip(pieces[i, 7], 1, 4))))
        i = j + 1
    return out


def _frames(pts):
    """unit tangent and mitre normal (scaled by 1/cos(theta/2), clamped) at every polyline node"""
    d = np.diff(pts, axis=0)
    L = np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    t = d / L
    tn = np.empty_like(pts)
    tn[0] = t[0]; tn[-1] = t[-1]
    if len(pts) > 2:
        m = t[:-1] + t[1:]
        mn = np.linalg.norm(m, axis=1, keepdims=True)
        tn[1:-1] = np.where(mn > 1e-6, m / np.maximum(mn, 1e-9), t[:-1])
    nrm = np.stack([-tn[:, 1], tn[:, 0]], axis=1)
    # mitre length: 1/cos(half angle) between the node normal and the segment normal, clamped to 2
    seg_n = np.stack([-t[:, 1], t[:, 0]], axis=1)
    cosh = np.ones(len(pts))
    cosh[:-1] = np.abs(np.sum(nrm[:-1] * seg_n, axis=1))
    cosh[-1] = np.abs(np.sum(nrm[-1] * seg_n[-1]))
    scale = np.clip(1.0 / np.maximum(cosh, 1e-3), 1.0, 2.0)
    return tn, nrm * scale[:, None], np.concatenate([[0.0], np.cumsum(L[:, 0])])


def _ribbon(pts, nrm, z, w, off, mat, birth, zlo=None):
    """continuous strip along the polyline: width w, centred at lateral offset `off`, top at z (per node).
    With zlo it becomes a closed box (top, bottom, two sides, two end caps) between zlo and z."""
    c = pts + nrm * off
    a = c - nrm * (w / 2); b = c + nrm * (w / 2)
    n = len(pts)
    top = np.concatenate([np.column_stack([a, z]), np.column_stack([b, z])])
    i = np.arange(n - 1)
    faces = [np.stack([i, i + 1, i + 1 + n, i + n], axis=1)]
    verts = [top]
    if zlo is not None:
        bot = np.concatenate([np.column_stack([a, zlo]), np.column_stack([b, zlo])])
        verts.append(bot)
        o = 2 * n
        faces.append(np.stack([i + n + o, i + 1 + n + o, i + 1 + o, i + o], axis=1))       # bottom
        faces.append(np.stack([i + o, i + 1 + o, i + 1, i], axis=1))                        # side a
        faces.append(np.stack([i + n, i + 1 + n, i + 1 + n + o, i + n + o], axis=1))        # side b
        faces.append(np.array([[0, n, n + o, o], [n - 1 + n + o, n - 1 + n, n - 1, n - 1 + o]]))   # end caps
    v = np.concatenate(verts).astype(np.float32); f = np.concatenate(faces).astype(np.int32)
    return v, f, np.full(len(f), mat, dtype=np.int32), np.full(len(f), birth, dtype=np.float32)


def _samples(pts, tn, s, step, first=0.5):
    """positions / tangents along the polyline every `step` m (arc-length parameter s per node)"""
    total = s[-1]
    if total < step * 0.6:
        return np.zeros((0, 2)), np.zeros((0, 2))
    ss = np.arange(step * first, total, step)
    P = np.column_stack([np.interp(ss, s, pts[:, 0]), np.interp(ss, s, pts[:, 1])])
    T = np.column_stack([np.interp(ss, s, tn[:, 0]), np.interp(ss, s, tn[:, 1])])
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    return P, T


def build_tracks(pieces, zg0, zg1):
    """pieces (N,8): x0,y0,x1,y1,year,elev,kind,tracks ; zg0/zg1 ground heights at the ends.
    Every way is swept as ONE continuous ribbon with mitred joints (ballast, rails, deck, parapets,
    embankment); viaduct piers are sampled along the arc length.  No more piecewise boxes."""
    out = []
    for pts, zg, birth, elev, kind, ntr in _chains(pieces, zg0, zg1):
        if len(pts) < 2:
            continue
        tn, nrm, s = _frames(pts)
        top = zg.copy()
        if elev == 1:
            gb = float(zg.mean())
            top[:] = gb + 7.0                                          # viaducts / bridges: deck 7 m above ground
        elif elev == 2:
            top += 3.5                                                 # embankments
        w_extra = 4.4 * (ntr - 1)
        if elev == 2:
            out.append(_ribbon(pts, nrm, zg + 1.8, 14.0 + w_extra, 0.0, MAT_EMBANK, birth, zlo=zg - 0.2))
            out.append(_ribbon(pts, nrm, top - 0.3, 9.0 + w_extra, 0.0, MAT_EMBANK, birth, zlo=zg + 1.7))
        if elev == 1:
            wdeck = 8.5 + w_extra
            out.append(_ribbon(pts, nrm, top, wdeck, 0.0, MAT_BRICK, birth, zlo=top - 1.6))
            for sy in (-1, 1):                                         # parapets
                out.append(_ribbon(pts, nrm, top + 1.0, 0.6, sy * (wdeck / 2 - 0.35), MAT_BRICK, birth, zlo=top))
            P, T = _samples(pts, tn, s, 24.0)                          # piers every 24 m of arc length
            for k in range(len(P)):
                p0 = P[k] - T[k] * 1.5; p1 = P[k] + T[k] * 1.5
                zgk = float(np.interp(s[-1] * (k + 0.5) / max(len(P), 1), s, zg))
                v, f, m, b = _box_along(p0[None, :], p1[None, :], np.float32(wdeck), np.array([zgk - 1.0], dtype=np.float32),
                                        np.array([zgk + 5.4], dtype=np.float32), MAT_BRICK, np.array([birth], dtype=np.float32))
                out.append((v, f, m, b))
        # ballast + rails for every track of the way
        wb = BALLAST_W * (0.8 if kind == 2 else 1.0)
        for k in range(ntr):
            off = (k - (ntr - 1) / 2.0) * TRACK_SPACING
            out.append(_ribbon(pts, nrm, top + 0.35, wb, off, MAT_BALLAST, birth))
            for sy in (-1, 1):
                out.append(_ribbon(pts, nrm, top + 0.60, RAIL_W, off + sy * RAIL_GAUGE / 2, MAT_RAIL, birth))
    return _merge(out)


def build_platforms(platforms, zg0, zg1):
    if len(platforms) == 0:
        return None
    p0 = platforms[:, 0:2]; p1 = platforms[:, 2:4]; birth = platforms[:, 4]; w = platforms[:, 5]
    parts = [_box_along(p0, p1, w[:, None] if False else 4.0, zg0 + 0.2, zg0 + 1.3, MAT_PLATFORM, birth)]
    return _merge(parts)


def _merge(parts):
    verts, faces, mats, births = [], [], [], []
    off = 0
    for v, f, m, b in parts:
        verts.append(v); faces.append(f + off); mats.append(m); births.append(np.asarray(b, dtype=np.float32).reshape(-1))
        off += len(v)
    if not verts:
        return None
    return np.concatenate(verts), np.concatenate(faces), np.concatenate(mats), np.concatenate(births)
