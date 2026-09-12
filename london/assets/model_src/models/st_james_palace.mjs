// St James's Palace, built for Henry VIII 1531-36 on the site of a leper
// hospital: low ranges of diapered Tudor brick round four courts, with the famous
// gatehouse and its octagonal turrets.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x.  "Front" = +z is the north front on to St James's Street, where the
// gatehouse stands.
//
// True dimensions: about 130 x 110 m; the gatehouse ~25 m to the tops of its
// octagonal turrets; ranges of two storeys with clustered chimneys.
import {
  exportGLB, out, M, mat, box, cyl, cone, dome, gableRoof, hipRoof, lathe, group, THREE,
  wall, archPath, crenel, crenelRing, turret, pinnacle,
} from './_lib_london.mjs';

const g = new THREE.Group();
const brick = M.tudor, brick2 = M.brick, port = M.portland, pale = M.pale;
const lead = M.lead, dark = M.dark, tile = M.tile, stone = M.rag;

// A two-storey Tudor range with a tiled roof, mullioned windows and chimneys.
function range(w, d, x, z, { h = 9.5, chim = 3, roof = tile, alongX = true } = {}) {
  const gg = new THREE.Group();
  gg.add(box(w, h, d, brick, 0, 0, 0));
  const rh = Math.min(w, d) * 0.36;
  gg.add(hipRoof(w, d, rh, roof, 0, h, 0, 0.75));
  gg.add(box(w + 0.5, 0.5, d + 0.5, port, 0, h - 0.5, 0));
  for (const f of [0.24, 0.62]) {
    if (alongX) {
      const n = Math.max(2, Math.floor(w / 4.0));
      for (let i = 0; i < n; i++) for (const s of [-1, 1])
        gg.add(box(2.2, 1.8, 0.4, dark, -w / 2 + (i + 0.5) * w / n, h * f, s * d / 2));
    } else {
      const n = Math.max(2, Math.floor(d / 4.0));
      for (let i = 0; i < n; i++) for (const s of [-1, 1])
        gg.add(box(0.4, 1.8, 2.2, dark, s * w / 2, h * f, -d / 2 + (i + 0.5) * d / n));
    }
  }
  const L = alongX ? w : d;
  for (let i = 0; i < chim; i++) {
    const u = -L / 2 + (i + 0.5) * L / chim;
    const cx = alongX ? u : 0, cz = alongX ? 0 : u;
    gg.add(box(2.2, 1.5, 2.2, brick2, cx, h + rh * 0.7, cz));
    for (const o of [-0.65, 0.65]) {
      gg.add(cyl(0.5, 0.55, 5.0, brick2, cx + (alongX ? o : 0), h + rh * 0.7 + 1.5, cz + (alongX ? 0 : o), 8));
      gg.add(box(1.35, 0.45, 1.35, port, cx + (alongX ? o : 0), h + rh * 0.7 + 6.5, cz + (alongX ? 0 : o)));
    }
  }
  gg.position.set(x, 0, z);
  return gg;
}

// ---------------------------------------------------------------- the gatehouse (+z front)
{
  const gx = -20, gz = 52;
  g.add(wall(11.5, 16, 12, brick, [archPath(0, 4.6, 0, 4.2, 3.2, 1, 8)], gx, 0, gz));
  // diapered brickwork on the street face
  for (let i = 0; i < 6; i++) for (let j = 0; j < 5; j++) {
    if ((i + j) % 2) continue;
    g.add(box(0.9, 0.9, 0.25, brick2, gx - 4.2 + j * 2.1, 6.5 + i * 1.7, gz + 6.1));
  }
  for (const s of [-1, 1]) g.add(box(3.0, 2.2, 0.4, dark, gx + s * 3.0, 9.5, gz + 6.05));
  g.add(box(2.4, 2.6, 0.5, port, gx, 9.3, gz + 6.1));                  // the clock/arms panel
  g.add(box(12.2, 1.0, 12.7, port, gx, 16, gz));
  g.add(crenelRing(12.2, 12.7, 0.8, port, gx, 17, gz, 1.4, 1.4, 1.2));
  // four octagonal turrets to ~25 m
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]]) {
    const tx = gx + a[0] * 6.6, tz = gz + a[1] * 6.9;
    g.add(cyl(2.4, 2.6, 21, brick, tx, 0, tz, 8));
    for (let i = 0; i < 5; i++) for (let j = 0; j < 4; j++) {
      if ((i + j) % 2) continue;
      const aa = j * Math.PI / 2 + 0.4;
      g.add(box(0.9, 0.9, 0.22, brick2, tx + 2.55 * Math.cos(aa), 3.0 + i * 2.9, tz + 2.55 * Math.sin(aa)));
    }
    g.add(cyl(3.0, 3.0, 0.9, port, tx, 21, tz, 8));
    g.add(crenel(4.6, 0.6, port, tx, 21.9, tz, true, 1.1, 0.9, 0.8));
    g.add(lathe([[2.7, 0], [2.9, 1.0], [1.9, 3.0], [0.8, 4.4], [0.2, 5.2]], lead, tx, 21.9, tz, 8));
    g.add(box(0.12, 1.8, 0.12, M.gold, tx, 27.1, tz));
    g.add(box(1.0, 0.5, 0.08, M.gold, tx + 0.5, 28.3, tz));
  }
}

// ---------------------------------------------------------------- the four courts
// north front ranges either side of the gatehouse
g.add(range(38, 12, -50, 52, { chim: 3 }));
g.add(range(52, 12, 26, 52, { chim: 4 }));
// Colour Court (behind the gate)
g.add(range(12, 34, -44, 30, { chim: 3, alongX: false }));
g.add(range(12, 34, 4, 30, { chim: 3, alongX: false }));
g.add(range(50, 12, -20, 10, { chim: 4 }));
g.add(box(34, 0.3, 30, mat(0x968f7d), -20, 0, 30));
// Ambassadors' Court (west)
g.add(range(12, 44, -62, 8, { chim: 3, alongX: false }));
g.add(range(46, 12, -40, -18, { chim: 4 }));
g.add(box(36, 0.3, 32, mat(0x968f7d), -40, 0, 8));
// Friary Court and Engine Court (east)
g.add(range(12, 46, 50, 20, { chim: 3, alongX: false }));
g.add(range(12, 40, 16, 16, { chim: 3, alongX: false }));
g.add(range(44, 12, 32, -8, { chim: 4 }));
g.add(box(28, 0.3, 40, mat(0x968f7d), 33, 0, 20));
// south ranges
g.add(range(40, 12, -6, -40, { chim: 3 }));
g.add(range(34, 12, 40, -38, { chim: 3 }));
g.add(range(12, 26, 58, -22, { chim: 2, alongX: false }));

// ---------------------------------------------------------------- Chapel Royal
{
  const cx = 22, cz = 34;
  g.add(box(26, 12, 11, brick, cx, 0, cz));
  g.add(gableRoof(26, 11, 5.6, lead, cx, 12, cz, true, 0.6));
  for (let i = 0; i < 5; i++) for (const s of [-1, 1])
    g.add(box(2.2, 5.4, 0.45, dark, cx - 10 + i * 5, 4.5, cz + s * 5.5));
  g.add(box(0.5, 6.0, 6.0, dark, cx + 13.2, 4.0, cz));
  for (const s of [-1, 1]) g.add(turret(1.6, 16, brick, lead, cx + s * 13, 0, cz - 5.5, 8, 4.0));
}

// ---------------------------------------------------------------- the garden to the south
g.add(box(90, 0.4, 26, M.grass, 0, 0, -60));
for (let i = 0; i < 6; i++) for (let j = 0; j < 2; j++)
  g.add(box(11, 0.6, 9, mat(0x86a55c), -38 + i * 15, 0.4, -66 + j * 12));
for (const s of [-1, 1]) g.add(box(1.2, 2.6, 26, brick, s * 46, 0, -60));

await exportGLB(g, out('st_james_palace'));
