// Whitehall Palace, c.1600-1690: Henry VIII's rambling brick palace of some 1500
// rooms, straddling King Street between St James's Park and the Thames.
// The Banqueting House is deliberately EXCLUDED (separate model).
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x (~400 m of river frontage).  "Front" = +z is the RIVER (Thames) side,
// with the Privy Stairs; King Street and the Holbein Gate are inland at -z.
import {
  exportGLB, out, M, mat, box, cyl, cone, dome, gableRoof, hipRoof, lathe, group, THREE,
  wall, archPath, crenel, crenelRing, turret, pinnacle, tudorChimney, profileWall, chimneys,
} from './_lib_london.mjs';

const g = new THREE.Group();
const brick = M.tudor, brick2 = M.brick, stone = M.rag, pale = M.pale, port = M.portland;
const lead = M.lead, dark = M.dark, tile = M.tile, timb = M.darkTimber, plaster = M.whitewash;
const slate = M.slate;

function rnd(i) { const v = Math.sin(i * 91.7 + i * i * 0.53 + 3.1) * 43758.5453; return v - Math.floor(v); }

// A Tudor brick range: body, tiled/leaded roof, stone-mullioned window bands,
// gabled dormers and clustered octagonal chimneys.
function range(w, d, h, x, z, { alongX = true, m = brick, roof = slate, rh = 0, chim = 0, dormers = 0, bands = 2 } = {}) {
  const gg = new THREE.Group();
  const L = alongX ? w : d, D = alongX ? d : w;
  rh = rh || Math.min(L, D) * 0.34;
  gg.add(box(w, h, d, m, 0, 0, 0));
  gg.add(hipRoof(w, d, rh, roof, 0, h, 0, 0.75));
  // window bands on both long faces
  for (let b = 0; b < bands; b++) {
    const y = 2.2 + b * (h - 2.6) / Math.max(1, bands - 0.15);
    if (y + 1.9 > h) continue;
    for (const s of [-1, 1]) {
      if (alongX) {
        const n = Math.max(2, Math.floor(w / 4.2));
        for (let i = 0; i < n; i++)
          gg.add(box(2.4, 1.9, 0.4, dark, -w / 2 + (i + 0.5) * w / n, y, s * d / 2));
      } else {
        const n = Math.max(2, Math.floor(d / 4.2));
        for (let i = 0; i < n; i++)
          gg.add(box(0.4, 1.9, 2.4, dark, s * w / 2, y, -d / 2 + (i + 0.5) * d / n));
      }
    }
  }
  // gabled dormers on the river/front face
  for (let i = 0; i < dormers; i++) {
    const u = -L / 2 + (i + 0.5) * L / dormers;
    if (alongX) {
      gg.add(box(3.2, rh * 0.8, D / 2, m, u, h, D / 4));
      gg.add(gableRoof(D / 2, 3.2, 2.0, roof, u, h + rh * 0.8, D / 4, false, 0.25));
      gg.add(box(1.8, 1.4, 0.4, dark, u, h + 0.7, D / 2 - 0.1));
    } else {
      gg.add(box(D / 2, rh * 0.8, 3.2, m, D / 4, h, u));
      gg.add(gableRoof(D / 2, 3.2, 2.0, roof, D / 4, h + rh * 0.8, u, true, 0.25));
    }
  }
  // clustered Tudor chimneys along the ridge
  for (let i = 0; i < chim; i++) {
    const u = -L / 2 + (i + 0.5) * L / chim;
    const cx = alongX ? u : 0, cz = alongX ? 0 : u;
    gg.add(box(2.4, 1.6, 2.4, brick2, cx, h + rh * 0.75, cz));
    for (const o of [-0.7, 0.7]) {
      gg.add(cyl(0.55, 0.6, 5.5, brick2, cx + (alongX ? o : 0), h + rh * 0.75 + 1.6, cz + (alongX ? 0 : o), 8));
      gg.add(box(1.5, 0.5, 1.5, stone, cx + (alongX ? o : 0), h + rh * 0.75 + 7.1, cz + (alongX ? 0 : o)));
    }
  }
  gg.position.set(x, 0, z);
  return gg;
}

// ---------------------------------------------------------------- river frontage (+z)
g.add(range(120, 16, 13, -110, 56, { chim: 6, dormers: 8 }));
g.add(range(90, 16, 13, 30, 56, { chim: 5, dormers: 6, roof: tile }));
g.add(range(60, 15, 12, 140, 54, { chim: 3, dormers: 4 }));
// river-front towers / bay windows
for (const tx of [-168, -52, -6, 74, 168]) {
  g.add(box(11, 20, 11, brick, tx, 0, 62));
  g.add(hipRoof(11, 11, 4.0, lead, tx, 20, 62, 0.15));
  g.add(cone(1.4, 4.0, lead, tx, 24, 62, 6));
  for (const f of [0.28, 0.58, 0.82]) g.add(box(5.0, 2.6, 0.4, dark, tx, 20 * f, 67.6));
}
// Privy Stairs / water gate out into the river
g.add(box(20, 3.0, 26, stone, -6, -0.6, 82));
g.add(box(16, 1.0, 20, stone, -6, 2.4, 84));
for (const s of [-1, 1]) {
  g.add(cyl(1.4, 1.6, 6.0, port, -6 + s * 6.5, 3.4, 78, 8));
  g.add(dome(1.5, port, -6 + s * 6.5, 9.4, 78, 8, 1.1));
}
g.add(box(26, 1.2, 5.0, stone, -6, -0.6, 94));

// ---------------------------------------------------------------- Great Hall & Chapel Royal
g.add(range(44, 17, 16, -78, 24, { chim: 0, bands: 1 }));
g.add(gableRoof(44, 17, 8.5, lead, -78, 16, 24, true, 0.7));
for (const s of [-1, 1]) {                      // tall hall windows
  const n = 6;
  for (let i = 0; i < n; i++) g.add(box(2.6, 8.0, 0.5, dark, -78 - 18 + i * 7.2, 5.5, 24 + s * 8.5));
  for (let i = 0; i <= n; i++) g.add(box(1.4, 17, 1.6, stone, -78 - 21.5 + i * 7.2, 0, 24 + s * 9.0));
}
g.add(box(4.5, 4.0, 4.5, lead, -78, 24.5, 24));           // roof louvre
g.add(cone(3.0, 4.0, lead, -78, 28.5, 24, 8));
g.add(cone(0.8, 2.5, M.gold, -78, 32.5, 24, 6));
// Chapel Royal
g.add(box(30, 15, 12, stone, 28, 0, 22));
g.add(gableRoof(30, 12, 7.0, lead, 28, 15, 22, true, 0.6));
for (const s of [-1, 1]) for (let i = 0; i < 5; i++)
  g.add(box(2.8, 8.0, 0.5, dark, 28 - 12 + i * 6, 5, 22 + s * 6));
for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
  g.add(turret(1.6, 20, stone, lead, 28 + a[0] * 15, 0, 22 + a[1] * 6, 8, 5));

// ---------------------------------------------------------------- Privy Gallery & courtyards
g.add(range(150, 12, 11, -60, 30, { chim: 6, dormers: 0, bands: 2 }));    // Privy Gallery
g.add(range(12, 70, 11, -140, 8, { alongX: false, chim: 3 }));            // west range
g.add(range(12, 60, 11, 12, 6, { alongX: false, chim: 3 }));
g.add(range(70, 12, 11, -100, -22, { chim: 3, dormers: 4, roof: tile }));
g.add(range(58, 12, 11, 60, 30, { chim: 3, dormers: 3 }));
g.add(range(46, 13, 12, 120, 24, { chim: 3, dormers: 3, roof: tile }));
g.add(range(12, 46, 11, 150, -2, { alongX: false, chim: 2 }));
g.add(range(40, 12, 10, 176, -22, { chim: 2 }));
// the Cockpit and Tiltyard buildings west of King Street
g.add(cyl(9.5, 10.0, 9.0, brick, -128, 0, -56, 8));
g.add(cone(10.6, 5.0, tile, -128, 9.0, -56, 8));
g.add(cone(1.0, 3.0, lead, -128, 14.0, -56, 6));
g.add(range(56, 12, 10, -80, -62, { chim: 3, dormers: 4, roof: tile }));
g.add(range(34, 12, 10, 60, -58, { chim: 2, dormers: 3 }));

// ---------------------------------------------------------------- Privy Garden
{
  const gx = -30, gz = -2, w = 76, d = 44;
  g.add(box(w, 0.5, d, M.grass, gx, 0, gz));
  g.add(box(w + 2, 1.4, 1.0, stone, gx, 0, gz - d / 2));
  g.add(box(w + 2, 1.4, 1.0, stone, gx, 0, gz + d / 2));
  for (let i = 0; i < 4; i++) for (let j = 0; j < 2; j++) {
    const bx = gx - w / 2 + 6 + i * (w - 12) / 3, bz = gz - d / 4 + j * d / 2;
    g.add(box(13, 0.7, 15, mat(0x86a55c), bx, 0.5, bz));
    g.add(box(10, 0.4, 12, mat(0x9db06a), bx, 1.2, bz));
  }
  g.add(cyl(1.2, 1.6, 5.5, port, gx, 0.5, gz, 8));     // sundial column
  g.add(dome(1.0, port, gx, 6.0, gz, 8, 1.0));
  for (const s of [-1, 1]) for (const t of [-1, 1])
    g.add(cyl(0.8, 1.0, 3.0, port, gx + s * (w / 2 - 4), 0.5, gz + t * (d / 2 - 4), 8));
}

// ---------------------------------------------------------------- King Street (runs along x at z = -40)
g.add(box(400, 0.3, 13, mat(0x8f8776), 0, 0, -40));

// ---------------------------------------------------------------- Holbein Gate (1532)
{
  const gx = -18, gz = -40, w = 13, d = 22, h = 19;
  // chequered flint-and-stone body with a carriage arch through it along x
  g.add(wall(w, h, d, stone, [archPath(0, 6.0, 0, 5.0, 3.4, 0, 8)], gx, 0, gz, Math.PI / 2));
  // the famous chequerboard on both street faces
  const cs = 1.6;
  for (let i = 0; i < 8; i++) for (let j = 0; j < 11; j++) {
    if ((i + j) % 2) continue;
    const yy = 1.0 + i * cs * 1.35, zz = gz - d / 2 + 0.9 + j * cs * 1.25;
    if (yy > h - 2.4) continue;
    for (const s of [-1, 1]) g.add(box(0.3, cs, cs, dark, gx + s * (w / 2 + 0.05), yy, zz));
  }
  g.add(box(w + 0.8, 1.2, d + 0.8, stone, gx, h, gz));
  g.add(crenelRing(w + 0.8, d + 0.8, 0.8, stone, gx, h + 1.2, gz, 1.5, 1.5, 1.3));
  // four octagonal turrets to ~20 m with lead cupolas and vanes
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]]) {
    const tx = gx + a[0] * (w / 2 + 0.3), tz = gz + a[1] * (d / 2 + 0.3);
    g.add(cyl(2.3, 2.5, 20.5, stone, tx, 0, tz, 8));
    for (let i = 0; i < 6; i++) for (let j = 0; j < 4; j++) {
      if ((i + j) % 2) continue;
      const aa = j * Math.PI / 2 + 0.4, yy = 2.0 + i * 2.6;
      g.add(box(1.3, 1.3, 0.25, dark, tx + 2.45 * Math.cos(aa), yy, tz + 2.45 * Math.sin(aa)));
    }
    g.add(cyl(2.9, 2.9, 0.9, stone, tx, 20.5, tz, 8));
    g.add(crenel(2.9 * 2 * 0.8, 0.6, stone, tx, 21.4, tz, true, 1.1, 0.9, 0.8));
    g.add(lathe([[2.6, 0], [2.8, 1.0], [1.8, 3.0], [0.7, 4.6], [0.2, 5.6]], lead, tx, 21.4, tz, 8));
    g.add(box(0.12, 2.0, 0.12, M.gold, tx, 27.0, tz));
    g.add(box(1.1, 0.6, 0.08, M.gold, tx + 0.55, 28.4, tz));
  }
  // small ranges either side, tying the gate into the palace
  for (const s of [-1, 1]) g.add(range(20, 12, 10, gx + s * 18, gz + s * 9, { chim: 1 }));
}

// ---------------------------------------------------------------- King Street Gate (1611)
{
  const gx = 118, gz = -40, w = 11, d = 16, h = 14;
  g.add(wall(w, h, d, port, [archPath(0, 5.4, 0, 4.4, 3.0, 0, 8)], gx, 0, gz, Math.PI / 2));
  g.add(box(w + 0.8, 1.0, d + 0.8, port, gx, h, gz));
  for (const s of [-1, 1]) {
    g.add(cyl(3.2, 3.4, 15.5, port, gx, 0, gz + s * (d / 2 - 0.6), 10));
    g.add(dome(3.4, lead, gx, 15.5, gz + s * (d / 2 - 0.6), 10, 1.1));
    g.add(cone(0.8, 2.6, M.gold, gx, 19.3, gz + s * (d / 2 - 0.6), 6));
    for (const f of [0.3, 0.62]) g.add(box(0.4, 2.4, 2.6, dark, gx + 3.2, 15.5 * f, gz + s * (d / 2 - 0.6)));
  }
  g.add(crenelRing(w + 0.8, d + 0.8, 0.7, port, gx, h + 1.0, gz, 1.2, 1.2, 1.0));
}

// ---------------------------------------------------------------- courtyard surfaces
for (const [cx, cz, cw, cd] of [[-60, 46, 90, 12], [70, 46, 60, 12], [150, 12, 30, 22]])
  g.add(box(cw, 0.3, cd, mat(0x9b9583), cx, 0, cz));

g.position.z = -13;   // centre the footprint on the origin
await exportGLB(g, out('whitehall_palace'));
