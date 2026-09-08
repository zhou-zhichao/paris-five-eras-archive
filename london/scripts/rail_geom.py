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


def build_tracks(pieces, zg0, zg1):
    """pieces (N,8): x0,y0,x1,y1,year,elev,kind,tracks ; zg0/zg1 ground heights at the ends."""
    out = []
    p0 = pieces[:, 0:2]; p1 = pieces[:, 2:4]
    birth = pieces[:, 4]; elev = pieces[:, 5]; kind = pieces[:, 6]; ntr = np.clip(pieces[:, 7], 1, 4).astype(int)
    # rail-top height per piece
    top0 = zg0.copy(); top1 = zg1.copy()
    bridge = elev == 1; emb = elev == 2
    gb = (zg0 + zg1) / 2
    top0[bridge] = gb[bridge] + 7.0; top1[bridge] = gb[bridge] + 7.0     # viaducts / bridges: deck 7 m above ground
    top0[emb] += 3.5; top1[emb] += 3.5                           # embankments
    # embankment body (trapezoid approximated by a wide low box + narrower upper box)
    if emb.any():
        w_extra = 4.0 + 4.4 * (ntr[emb] - 1)
        out.append(_box_along(p0[emb], p1[emb], 14.0 + w_extra, zg0[emb] - 0.2, zg0[emb] + 1.8, MAT_EMBANK, birth[emb]))
        out.append(_box_along(p0[emb], p1[emb], 9.0 + w_extra, zg0[emb] + 1.7, top0[emb] - 0.3, MAT_EMBANK, birth[emb]))
    # viaduct: deck slab + brick piers every 12 m (the gaps read as arches)
    if bridge.any():
        bp0, bp1, bb, gbb = p0[bridge], p1[bridge], birth[bridge], gb[bridge]
        wdeck = 8.5 + 4.4 * (ntr[bridge] - 1)
        out.append(_box_along(bp0, bp1, wdeck, gbb + 5.4, gbb + 7.0, MAT_BRICK, bb))
        for sy in (-1, 1):                                        # parapets
            q0, q1 = _offset(bp0, bp1, sy * (wdeck / 2 - 0.35))
            out.append(_box_along(q0, q1, 0.6, gbb + 7.0, gbb + 8.0, MAT_BRICK, bb))
        # piers
        d = bp1 - bp0; L = np.linalg.norm(d, axis=1)
        pier_p0, pier_p1, pier_b, pier_g = [], [], [], []
        for i in range(len(bp0)):
            npier = max(1, int(L[i] // 12.0))
            for k in range(npier):
                s = (k + 0.5) / npier
                c = bp0[i] + d[i] * s
                t = d[i] / (L[i] + 1e-6)
                pier_p0.append(c - t * 1.5); pier_p1.append(c + t * 1.5); pier_b.append(bb[i]); pier_g.append(gbb[i])
        if pier_p0:
            pier_p0 = np.array(pier_p0, dtype=np.float32); pier_p1 = np.array(pier_p1, dtype=np.float32)
            pier_b = np.array(pier_b, dtype=np.float32); pier_g = np.array(pier_g, dtype=np.float32)
            out.append(_box_along(pier_p0, pier_p1, np.float32(8.5), pier_g - 1.0, pier_g + 5.5, MAT_BRICK, pier_b))
    # ballast + rails for every track of the way
    for k in range(1, 5):
        sel = ntr >= k
        if not sel.any():
            continue
        offs = (k - 1 - (ntr[sel] - 1) / 2.0) * TRACK_SPACING
        q0, q1 = _offset(p0[sel], p1[sel], offs[:, None])
        zb0 = top0[sel] + 0.35; zb1 = top1[sel] + 0.35
        wb = np.where(kind[sel] == 2, BALLAST_W * 0.8, BALLAST_W)
        out.append(_strip(q0, q1, wb[:, None], zb0, zb1, MAT_BALLAST, birth[sel], ext=1.0))
        for sy in (-1, 1):
            r0, r1 = _offset(q0, q1, sy * RAIL_GAUGE / 2)
            out.append(_strip(r0, r1, RAIL_W, zb0 + 0.25, zb1 + 0.25, MAT_RAIL, birth[sel], ext=1.0))
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
