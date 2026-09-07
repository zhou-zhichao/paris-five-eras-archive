// The Palace of Placentia, Greenwich - Humphrey of Gloucester's Bella Court of
// 1433, refaced in brick by Henry VII and the birthplace of Henry VIII and
// Elizabeth I; demolished after the Civil War.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x (the ~220 m river frontage).  "Front" = +z is the RIVER (Thames) side,
// with the water gate; the tiltyard and Duke Humphrey's tower lie inland at -z.
import {
  exportGLB, out, M, mat, box, cyl, cone, dome, gableRoof, hipRoof, lathe, group, THREE,
  wall, archPath, crenel, crenelRing, turret, pinnacle,
} from './_lib_london.mjs';

const g = new THREE.Group();
const brick = M.tudor, brick2 = M.brick, port = M.portland, pale = M.pale, stone = M.rag;
const lead = M.lead, dark = M.dark, tile = M.tile, timb = M.darkTimber;

// A brick range with mullioned windows, gabled dormers and clustered chimneys.
function range(w, d, x, z, { h = 12, chim = 4, dormers = 0, roof = tile, alongX = true, bands = 3 } = {}) {
  const gg = new THREE.Group();
  const rh = Math.min(w, d) * 0.38;
  gg.add(box(w, h, d, brick, 0, 0, 0));
  gg.add(hipRoof(w, d, rh, roof, 0, h, 0, 0.8));
  gg.add(box(w + 0.5, 0.5, d + 0.5, port, 0, h - 0.5, 0));
  for (let b = 0; b < bands; b++) {
    const y = 1.8 + b * (h - 2.6) / bands;
    const n = Math.max(2, Math.floor((alongX ? w : d) / 4.2));
    for (let i = 0; i < n; i++) for (const s of [-1, 1]) {
      const u = -(alongX ? w : d) / 2 + (i + 0.5) * (alongX ? w : d) / n;
      gg.add(alongX ? box(2.4, 1.9, 0.4, dark, u, y, s * d / 2) : box(0.4, 1.9, 2.4, dark, s * w / 2, y, u));
    }
  }
  const L = alongX ? w : d, D = alongX ? d : w;
  for (let i = 0; i < dormers; i++) {
    const u = -L / 2 + (i + 0.5) * L / dormers;
    gg.add(box(3.2, rh * 0.8, D / 2, brick, alongX ? u : D / 4, h, alongX ? D / 4 : u));
    gg.add(gableRoof(D / 2, 3.2, 2.0, roof, alongX ? u : D / 4, h + rh * 0.8, alongX ? D / 4 : u, !alongX, 0.25));
  }
  for (let i = 0; i < chim; i++) {
    const u = -L / 2 + (i + 0.5) * L / chim;
    const cx = alongX ? u : 0, cz = alongX ? 0 : u;
    gg.add(box(2.4, 1.5, 2.4, brick2, cx, h + rh * 0.72, cz));
    for (const o of [-0.7, 0.7]) {
      gg.add(cyl(0.52, 0.58, 5.2, brick2, cx + (alongX ? o : 0), h + rh * 0.72 + 1.5, cz + (alongX ? 0 : o), 8));
      gg.add(box(1.4, 0.45, 1.4, port, cx + (alongX ? o : 0), h + rh * 0.72 + 6.7, cz + (alongX ? 0 : o)));
    }
  }
  gg.position.set(x, 0, z);
  return gg;
}

// ---------------------------------------------------------------- the long river range (+z)
g.add(range(96, 15, -60, 34, { chim: 6, dormers: 7 }));
g.add(range(84, 15, 62, 34, { chim: 5, dormers: 6 }));
// projecting bay-window towers along the river front
for (const tx of [-104, -74, -44, -14, 34, 66, 98]) {
  g.add(box(9, 18, 10, brick, tx, 0, 44));
  for (const f of [0.18, 0.44, 0.70]) g.add(box(5.2, 2.6, 0.4, dark, tx, 18 * f, 49.1));
  g.add(box(9.8, 0.8, 10.8, port, tx, 18, 44));
  g.add(hipRoof(9.5, 10.5, 3.6, lead, tx, 18.8, 44, 0.2));
  g.add(cone(1.2, 3.4, lead, tx, 22.4, 44, 6));
}
// the water gate in the middle of the frontage
{
  g.add(wall(16, 14, 12, brick, [archPath(0, 5.6, 0, 4.4, 3.6, 1, 8)], 0, 0, 40));
  g.add(box(16.6, 1.0, 12.6, port, 0, 14, 40));
  g.add(crenelRing(16.6, 12.6, 0.8, port, 0, 15, 40, 1.3, 1.3, 1.1));
  for (const s of [-1, 1]) {
    g.add(cyl(2.8, 3.0, 22, brick, s * 9.5, 0, 40, 8));
    g.add(lathe([[3.1, 0], [3.3, 1.0], [2.1, 3.2], [0.9, 4.8], [0.2, 5.8]], lead, s * 9.5, 22, 40, 8));
  }
  g.add(box(26, 2.6, 12, stone, 0, -0.6, 52));                 // the landing stage
  g.add(box(20, 1.0, 7, stone, 0, 2.0, 55));
}
// the river wall
g.add(box(230, 2.6, 1.4, stone, 0, 0, 50));

// ---------------------------------------------------------------- Great Hall and Chapel
{
  const cx = -22, cz = 8, w = 36, d = 15, eaves = 15, ridge = 23;
  g.add(box(w, eaves, d, stone, cx, 0, cz));
  g.add(box(w + 0.8, 0.8, d + 0.8, port, cx, eaves - 0.8, cz));
  g.add(gableRoof(w, d, ridge - eaves, lead, cx, eaves, cz, true, 0.7));
  for (let i = 0; i < 5; i++) for (const s of [-1, 1]) {
    g.add(box(3.0, 7.5, 0.45, dark, cx - 13 + i * 6.5, 5.0, cz + s * d / 2));
    g.add(box(0.3, 7.5, 0.55, port, cx - 13 + i * 6.5, 5.0, cz + s * (d / 2 + 0.05)));
  }
  for (let i = 0; i <= 5; i++) for (const s of [-1, 1])
    g.add(box(1.3, eaves + 0.8, 1.8, port, cx - 16.2 + i * 6.5, 0, cz + s * (d / 2 + 0.7)));
  g.add(box(4.0, 3.0, 4.0, port, cx, ridge - 1.2, cz));
  g.add(lathe([[2.8, 0], [3.0, 0.9], [1.9, 2.9], [0.7, 4.6], [0.2, 5.6]], lead, cx, ridge + 1.8, cz, 8));
  g.add(cone(0.7, 2.2, M.gold, cx, ridge + 7.4, cz, 6));
}
{
  const cx = 40, cz = 8;
  g.add(box(28, 13, 11, stone, cx, 0, cz));
  g.add(gableRoof(28, 11, 6.0, lead, cx, 13, cz, true, 0.6));
  for (let i = 0; i < 5; i++) for (const s of [-1, 1])
    g.add(box(2.4, 6.0, 0.45, dark, cx - 11 + i * 5.5, 4.5, cz + s * 5.5));
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
    g.add(turret(1.7, 18, stone, lead, cx + a[0] * 14, 0, cz + a[1] * 5.5, 8, 4.5));
}

// ---------------------------------------------------------------- inner courts, friary and tiltyard
g.add(range(12, 46, -80, 8, { chim: 3, alongX: false }));
g.add(range(12, 46, 6, 8, { chim: 3, alongX: false }));
g.add(range(70, 13, -46, -20, { chim: 5, dormers: 5 }));
g.add(range(56, 13, 50, -20, { chim: 4, dormers: 4 }));
g.add(range(12, 40, 96, 6, { chim: 3, alongX: false }));
g.add(box(60, 0.3, 34, mat(0x968f7d), -46, 0, 12));
g.add(box(46, 0.3, 30, mat(0x968f7d), 60, 0, 12));

// the tiltyard, its two towers, and Duke Humphrey's tower on the hill behind
g.add(box(96, 0.4, 30, mat(0x9c9375), -20, 0, -52));
for (const s of [-1, 1]) {
  g.add(box(9, 20, 9, brick, -20 + s * 34, 0, -52));
  g.add(crenelRing(9.6, 9.6, 0.8, port, -20 + s * 34, 20, -52, 1.3, 1.3, 1.1));
  g.add(hipRoof(8.5, 8.5, 3.5, lead, -20 + s * 34, 20.8, -52, 0.15));
  for (const f of [0.3, 0.6, 0.85]) g.add(box(3.0, 2.0, 0.4, dark, -20 + s * 34, 20 * f, -47.4));
}
g.add(box(110, 2.4, 1.2, brick, -20, 0, -68));
{
  const tx = 78, tz = -66;                                    // Duke Humphrey's tower
  g.add(box(14, 24, 14, stone, tx, 0, tz));
  g.add(box(15, 1.0, 15, port, tx, 24, tz));
  g.add(crenelRing(15, 15, 0.9, port, tx, 25, tz, 1.5, 1.5, 1.3));
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
    g.add(turret(2.0, 6.5, stone, lead, tx + a[0] * 6.5, 25, tz + a[1] * 6.5, 8, 4.0));
  for (const f of [0.28, 0.55, 0.80]) for (const s of [-1, 1])
    g.add(box(2.4, 2.4, 0.4, dark, tx, 24 * f, tz + s * 7));
}

g.position.z = -2;
await exportGLB(g, out('greenwich_palace_placentia'));
