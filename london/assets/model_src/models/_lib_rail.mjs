// Shared helpers for the LONDON RAILWAY STATION set.
// Conventions for this set: metres, ground y=0, footprint centred on the origin,
// the LONG axis (tracks / platforms) runs along X, the tracks leave towards -X,
// the station front / concourse faces +Z.
import {
  THREE, mat, box, cyl, cone, dome, gableRoof, hipRoof, prism, lathe, group, exportGLB,
} from '../export_glb.mjs';
import {
  openWall, arcade, column, colonnade, pediment, pedimentX, balustrade, parapet,
  cornice, windowsZ, windowsX, spire, pinnacle, finialBallCross, steps,
} from './_lib_wren_edwardian.mjs';

export {
  THREE, mat, box, cyl, cone, dome, gableRoof, hipRoof, prism, lathe, group, exportGLB,
  openWall, arcade, column, colonnade, pediment, pedimentX, balustrade, parapet,
  cornice, windowsZ, windowsX, spire, pinnacle, finialBallCross, steps,
};

export const OUT = 'C:/Users/sam/Documents/ChatGPT/3D map project/.claude/worktrees/london/london/assets/models/';

export const P = {
  stock: 0xb9a98a,      // London stock brick
  red: 0x9e5a45,        // Victorian red brick
  reddark: 0x88483a,
  terracotta: 0xa8624a,
  stone: 0xd9d2c0,      // Portland stone
  pale: 0xe3dccb,
  dstone: 0xb8ad94,
  slate: 0x4d5057,
  glassroof: 0x8fb0c4,
  glass: 0x5b7c96,
  darkglass: 0x34474f,
  iron: 0x3d3f42,
  steelwhite: 0xe6e6e6,
  concrete: 0xb5b2ab,
  dconcrete: 0x8d8a84,
  platform: 0x9a9690,
  ballast: 0x7d7468,
  rail: 0x3a3a3a,
  lead: 0x7b8087,
  dark: 0x33302b,
  gold: 0xd0a23c,
  alu: 0xb9bcc0,
  timber: 0x6e4a2b,
  green: 0x4a6b4a,
};

const _cache = new Map();
export function M(hex) { if (!_cache.has(hex)) _cache.set(hex, mat(hex)); return _cache.get(hex); }

// ---------------------------------------------------------------------------
// shift a finished model so its footprint is centred on the origin in x and z
// (y is left alone: the ground stays at y = 0).
export function centreXZ(root) {
  root.updateMatrixWorld(true);
  const b = new THREE.Box3().setFromObject(root);
  const wrap = new THREE.Group();
  wrap.add(root);
  root.position.x -= (b.min.x + b.max.x) / 2;
  root.position.z -= (b.min.z + b.max.z) / 2;
  return wrap;
}

// ---------------------------------------------------------------------------
// semicircular / elliptical arch profile points, span s, rise r
export function archPts(span, rise, n = 14) {
  const p = [];
  for (let i = 0; i <= n; i++) {
    const t = -1 + 2 * i / n;
    p.push([t * span / 2, rise * Math.sqrt(Math.max(0, 1 - t * t))]);
  }
  return p;
}
export function archShape(span, rise, n = 14) {
  const pts = archPts(span, rise, n);
  const s = new THREE.Shape();
  s.moveTo(-span / 2, 0);
  for (const [a, b] of pts) s.lineTo(a, b);
  s.lineTo(span / 2, 0); s.closePath();
  return { s, pts };
}

// ---------------------------------------------------------------------------
// GLAZED ARCHED TRAIN SHED running along X.
// len = length along x, span = width along z, rise = crown above y (the springing).
// opts: {segs, ribs, glass, iron, ridgeMat, gableA (mesh at -x end), gableB (+x end),
//        gableAMat, gableBMat, ridge:true}
export function shedX(len, span, rise, x = 0, y = 0, z = 0, o = {}) {
  const glass = M(o.glass ?? P.glassroof), iron = M(o.iron ?? P.iron);
  const { s, pts } = archShape(span, rise, o.segs ?? 14);
  const inner = new THREE.Group();
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: len, bevelEnabled: false }), glass);
  m.position.z = -len / 2;
  inner.add(m);
  const nr = o.ribs ?? Math.max(6, Math.round(len / 12));
  for (let r = 0; r <= nr; r++) {
    const zz = -len / 2 + r * len / nr;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
      const L = Math.hypot(x1 - x0, y1 - y0);
      const b = box(L, 0.7, 0.9, iron, (x0 + x1) / 2, (y0 + y1) / 2 - 0.35, zz);
      b.rotation.z = Math.atan2(y1 - y0, x1 - x0);
      inner.add(b);
    }
  }
  if (o.gableA !== false) {   // -x end screen
    const g2 = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.1, bevelEnabled: false }), M(o.gableAMat ?? P.dark));
    g2.position.z = -len / 2 - 1.1; inner.add(g2);
  }
  if (o.gableB !== false) {   // +x end screen (usually the glazed concourse gable)
    const g3 = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.1, bevelEnabled: false }), M(o.gableBMat ?? P.glassroof));
    g3.position.z = len / 2; inner.add(g3);
  }
  inner.rotation.y = Math.PI / 2;
  const outg = new THREE.Group();
  outg.add(inner);
  if (o.ridge !== false) outg.add(box(len, 1.0, 1.6, M(o.lead ?? P.lead), 0, rise + 0.1, 0));
  outg.position.set(x, y, z);
  return outg;
}

// ---------------------------------------------------------------------------
// RIDGE-AND-FURROW glazed roof: parallel ridges running along X, repeated across Z.
// len along x, width along z, n ridges, ridge height rh above the eaves y.
// opts: {camber} raises the middle strips to give an overall arched section.
export function ridgeFurrowX(len, width, n, rh, x = 0, y = 0, z = 0, o = {}) {
  const g = new THREE.Group();
  const glass = M(o.glass ?? P.glassroof), iron = M(o.iron ?? P.iron);
  const sw = width / n, camber = o.camber ?? 0;
  const base = y - (o.skirt ?? 0.6);
  for (let i = 0; i < n; i++) {
    const cz = -width / 2 + sw * (i + 0.5);
    const t = 1 - Math.abs(cz) / (width / 2);
    const yy = y + camber * Math.sin(t * Math.PI / 2);
    g.add(gableRoof(len, sw, rh, glass, 0, yy, cz, true, 0.05));
    if (o.skirt !== false) g.add(box(len, yy - base, sw, M(o.fascia ?? P.iron), 0, base, cz));
    g.add(box(len, 0.5, 0.55, iron, 0, yy - 0.5, cz - sw / 2));   // valley gutter
  }
  g.add(box(len, 0.5, 0.55, iron, 0, y - 0.5, width / 2));
  g.position.set(x, 0, z);       // gableRoof already carries the eaves height y
  return g;
}

// ---------------------------------------------------------------------------
// PLATFORM DECK: slab + alternating platforms and tracks, tracks running along x.
// len along x, width along z, nPlat island platforms.
export function platformsX(len, width, nPlat, x = 0, y = 0, z = 0, o = {}) {
  const g = new THREE.Group();
  const slab = M(o.slab ?? P.ballast), pf = M(o.platform ?? P.platform), rl = M(P.rail);
  g.add(box(len, 0.6, width, slab, 0, y - 0.6, z));
  const pitch = width / nPlat;
  const pw = o.pw ?? Math.min(9, pitch * 0.5);
  for (let i = 0; i < nPlat; i++) {
    const cz = z - width / 2 + pitch * (i + 0.5);
    g.add(box(len * (o.plen ?? 1), 1.0, pw, pf, o.px ?? 0, y, cz));
    // a pair of rails either side
    for (const s of [-1, 1]) {
      const tz = cz + s * (pitch / 2 - (pitch - pw) / 4);
      g.add(box(len, 0.25, 0.18, rl, 0, y, tz - 0.72));
      g.add(box(len, 0.25, 0.18, rl, 0, y, tz + 0.72));
    }
  }
  return g;
}

// simple ballasted track fan (no platforms), n tracks across width
export function tracksX(len, width, n, x = 0, y = 0, z = 0) {
  const g = new THREE.Group();
  g.add(box(len, 0.5, width, M(P.ballast), x, y - 0.5, z));
  for (let i = 0; i < n; i++) {
    const cz = z - width / 2 + width * (i + 0.5) / n;
    g.add(box(len, 0.25, 0.18, M(P.rail), x, y, cz - 0.72));
    g.add(box(len, 0.25, 0.18, M(P.rail), x, y, cz + 0.72));
  }
  return g;
}

// ---------------------------------------------------------------------------
// side walls of a shed with buttress piers, running along x at z = ±W/2
export function shedWallsX(len, W, h, x = 0, y = 0, z = 0, o = {}) {
  const g = new THREE.Group();
  const wall = M(o.wall ?? P.stock), pier = M(o.pier ?? P.dstone);
  const t = o.t ?? 2.4, np = o.piers ?? Math.max(4, Math.round(len / 11));
  for (const sz of [-1, 1]) {
    g.add(box(len, h, t, wall, 0, y, z + sz * (W / 2 - t / 2)));
    for (let i = 0; i < np; i++) {
      const xx = -len / 2 + len * (i + 0.5) / np;
      g.add(box(1.9, h + 2.2, t + 0.9, pier, xx, y, z + sz * (W / 2 - t / 2)));
    }
  }
  return g;
}

// ---------------------------------------------------------------------------
// PLATFORM CANOPY along x: ridged (or flat) roof on a double row of columns.
// opts: {flat:true, colMat, roofMat, valance}
export function canopyX(len, width, h, x = 0, y = 0, z = 0, o = {}) {
  const g = new THREE.Group();
  const col = M(o.colMat ?? P.iron), rf = M(o.roofMat ?? P.slate);
  const ncol = o.ncol ?? Math.max(3, Math.round(len / 9));
  for (let i = 0; i < ncol; i++) {
    const xx = -len / 2 + len * (i + 0.5) / ncol;
    g.add(cyl(0.22, 0.28, h, col, xx, 0, 0, 8));
  }
  g.add(box(len, 0.45, width * 0.35, col, 0, h, 0));         // spine beam
  if (o.flat) {
    g.add(box(len, 0.55, width, rf, 0, h + 0.45, 0));
  } else {
    g.add(gableRoof(len, width, o.rh ?? 2.2, rf, 0, h + 0.45, 0, true, 0.4));
  }
  if (o.valance !== false) for (const sz of [-1, 1])
    g.add(box(len, 0.7, 0.3, M(o.valMat ?? P.timber), 0, h + 0.45 - 0.7, sz * (width / 2 + 0.35)));
  g.position.set(x, y, z);
  return g;
}

// ---------------------------------------------------------------------------
// BRICK VIADUCT running along x: n bays of span `bay`, deck top at deckH, width W.
export function viaductX(n, bay, deckH, W, x = 0, y = 0, z = 0, o = {}) {
  const g = new THREE.Group();
  const bk = M(o.brick ?? P.stock), bkd = M(o.dark ?? 0xa08e6f), cop = M(o.coping ?? P.dstone);
  const len = n * bay;
  const pierW = o.pierW ?? bay * 0.28;
  const span = bay - pierW;
  const vert = Math.max(0.8, deckH - 1.2 - span / 2);   // crown of the arch sits 1.2 m under the deck
  // solid spandrel wall with arched holes, on both faces + the core
  const ops = [];
  for (let i = 0; i < n; i++) ops.push({ cx: -len / 2 + bay * (i + 0.5), y0: 0, w: span, h: vert, arch: true });
  for (const sz of [-1, 1]) {
    const w2 = openWall(len, deckH, 1.2, bk, ops, 0, 0, sz * (W / 2 - 0.6), 10);
    g.add(w2);
  }
  // core piers between the faces (end piers halved so the unit tiles exactly)
  for (let i = 0; i <= n; i++) {
    const xx = -len / 2 + bay * i;
    const end = o.tile && (i === 0 || i === n);
    const pw = end ? pierW / 2 : pierW;
    const off = end ? (i === 0 ? pierW / 4 : -pierW / 4) : 0;
    g.add(box(pw, deckH, W - 1.2, bkd, xx + off, 0, 0));
  }
  // deck slab + parapets
  g.add(box(len, 1.1, W, bkd, 0, deckH - 1.1, 0));
  for (const sz of [-1, 1]) {
    g.add(box(len, 1.5, 0.7, bk, 0, deckH, sz * (W / 2 - 0.35)));
    g.add(box(len, 0.35, 1.0, cop, 0, deckH + 1.5, sz * (W / 2 - 0.35)));
  }
  g.position.set(x, y, z);
  return g;
}

// iron lattice / plate girder along x (a pair either side of the deck)
export function girderX(len, depth, W, x = 0, y = 0, z = 0, o = {}) {
  const g = new THREE.Group();
  const ir = M(o.iron ?? P.iron), ird = M(o.iron2 ?? 0x4c4f54);
  for (const sz of [-1, 1]) {
    const zz = sz * (W / 2 - 0.5);
    g.add(box(len, depth, 1.0, ir, 0, 0, zz));
    g.add(box(len + 1.0, 0.9, 1.5, ird, 0, depth - 0.9, zz));   // top flange
    g.add(box(len + 1.0, 0.9, 1.5, ird, 0, 0, zz));             // bottom flange
    const nst = o.stiff ?? Math.max(6, Math.round(len / 3));
    for (let i = 0; i <= nst; i++)
      g.add(box(0.5, depth, 1.5, ird, -len / 2 + len * i / nst, 0, zz));
  }
  g.position.set(x, y, z);
  return g;
}

// ---------------------------------------------------------------------------
// iron footbridge crossing the tracks (spanning Z) with stairs at both ends
export function footbridgeZ(spanZ, h, x = 0, y = 0, z = 0, o = {}) {
  const g = new THREE.Group();
  const ir = M(o.iron ?? P.iron), dk = M(o.deck ?? P.timber), rf = M(o.roof ?? P.slate);
  const w = o.w ?? 2.6;
  g.add(box(w, 0.4, spanZ, dk, 0, h, 0));
  for (const sx of [-1, 1]) g.add(box(0.25, 1.3, spanZ, ir, sx * (w / 2), h + 0.4, 0));
  g.add(box(w + 0.3, 0.3, spanZ, ir, 0, h - 0.5, 0));
  const nl = o.legs ?? 3;
  for (let i = 0; i < nl; i++) {
    const zz = -spanZ / 2 + spanZ * (i + 0.5) / nl;
    for (const sx of [-1, 1]) g.add(cyl(0.18, 0.22, h, ir, sx * (w / 2 - 0.2), 0, zz, 6));
  }
  if (o.roofed) g.add(gableRoof(w + 1.0, spanZ, 0.9, rf, 0, h + 2.4, 0, false, 0.3));
  // stair flights at each end running along x
  for (const sz of [-1, 1]) {
    const zz = sz * (spanZ / 2 + 2.5);
    const st = new THREE.Group();
    for (let i = 0; i < 8; i++) st.add(box(1.1, 0.35, w, ir, -3.5 + i * 1.0, h * i / 8, 0));
    st.position.set(0, 0, zz);
    g.add(st);
  }
  g.position.set(x, y, z);
  return g;
}

// evenly spaced window openings as recessed dark boxes on a +Z / -Z facade
export function winGridZ(nx, ny, sx, sy, w, h, hex, x, y, z, t = 0.4) {
  const g = new THREE.Group(), dm = M(hex);
  for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++)
    g.add(box(w, h, t, dm, (i - (nx - 1) / 2) * sx, j * sy, 0));
  g.position.set(x, y, z);
  return g;
}
export function winGridX(nz, ny, sz, sy, d, h, hex, x, y, z, t = 0.4) {
  const g = new THREE.Group(), dm = M(hex);
  for (let i = 0; i < nz; i++) for (let j = 0; j < ny; j++)
    g.add(box(t, h, d, dm, 0, j * sy, (i - (nz - 1) / 2) * sz));
  g.position.set(x, y, z);
  return g;
}

// a chimney stack
export function chimney(w, d, h, hex, x, y, z, pots = 3) {
  const g = new THREE.Group();
  g.add(box(w, h, d, M(hex), 0, 0, 0));
  g.add(box(w + 0.4, 0.5, d + 0.4, M(P.dstone), 0, h, 0));
  for (let i = 0; i < pots; i++)
    g.add(cyl(0.24, 0.28, 1.0, M(0xa05a3a), (i - (pots - 1) / 2) * (w / pots), h + 0.5, 0, 6));
  g.position.set(x, y, z);
  return g;
}

// buffer stops at the +x end of n tracks
export function bufferStops(width, n, x, y, z) {
  const g = new THREE.Group();
  for (let i = 0; i < n; i++) {
    const cz = z - width / 2 + width * (i + 0.5) / n;
    g.add(box(1.6, 1.3, 3.0, M(P.iron), x, y, cz));
  }
  return g;
}
