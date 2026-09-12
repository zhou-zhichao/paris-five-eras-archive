// The Old Palace of Westminster (1097-1834): Westminster Hall, St Stephen's
// Chapel, the Painted Chamber and a jumble of medieval and Tudor lodgings, courts
// and cloisters on the Thames bank.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x.  "Front" = +z is the RIVER (Thames) side, with the water stairs.
//
// True dimensions: Westminster Hall 73 x 20 m externally, ridge ~28 m (the widest
// unsupported medieval roof in Europe); St Stephen's Chapel ~30 m high.
import {
  exportGLB, out, M, mat, box, cyl, cone, dome, gableRoof, hipRoof, lathe, group, THREE,
  wall, archPath, crenel, crenelRing, turret, pinnacle, lancets, rose, profileWall, windowBand,
} from './_lib_london.mjs';

const g = new THREE.Group();
const stone = M.rag, pale = M.pale, med = M.medieval, port = M.portland;
const lead = M.lead, dark = M.dark, tile = M.tile, brick = M.tudor, timb = M.darkTimber;

// ---------------------------------------------------------------- Westminster Hall (1097 / roof 1399)
{
  const cx = -46, cz = -14, w = 73, d = 21, eaves = 17, ridge = 28;
  g.add(box(w, eaves, d, stone, cx, 0, cz));
  g.add(box(w + 1.2, 1.0, d + 1.2, med, cx, eaves - 1.0, cz));
  g.add(gableRoof(w, d, ridge - eaves, lead, cx, eaves, cz, true, 0.8));
  // the great buttresses and two-light windows of the hall
  for (let i = 0; i <= 6; i++) {
    const bx = cx - w / 2 + i * w / 6;
    for (const s of [-1, 1]) {
      g.add(box(2.2, eaves + 1.5, 3.0, med, bx, 0, cz + s * (d / 2 + 1.2)));
      g.add(pinnacle(1.5, 5.0, med, bx, eaves + 1.5, cz + s * (d / 2 + 1.2)));
    }
  }
  for (let i = 0; i < 6; i++) {
    const bx = cx - w / 2 + (i + 0.5) * w / 6;
    for (const s of [-1, 1]) g.add(box(3.4, 8.0, 0.5, dark, bx, 7.5, cz + s * d / 2));
  }
  // north front (-x): great window, porch and the two flanking towers
  g.add(profileWall([[-d / 2, 0], [d / 2, 0], [0, ridge - eaves]], 3.0, stone, cx - w / 2, eaves, cz, Math.PI / 2));
  g.add(box(0.8, 11.0, 11.0, dark, cx - w / 2 - 0.3, 8.0, cz));
  g.add(box(8.0, 12.0, 9.0, med, cx - w / 2 - 4.0, 0, cz));
  g.add(gableRoof(8.0, 9.0, 4.5, lead, cx - w / 2 - 4.0, 12.0, cz, false, 0.4));
  g.add(box(0.6, 7.0, 4.6, dark, cx - w / 2 - 8.2, 0, cz));
  for (const s of [-1, 1]) {
    g.add(box(6.2, 26, 6.2, med, cx - w / 2 + 1.5, 0, cz + s * (d / 2 - 1.0)));
    g.add(crenelRing(6.8, 6.8, 0.8, med, cx - w / 2 + 1.5, 26, cz + s * (d / 2 - 1.0), 1.3, 1.3, 1.1));
    g.add(cone(3.6, 6.0, lead, cx - w / 2 + 1.5, 26.8, cz + s * (d / 2 - 1.0), 8));
  }
}

// ---------------------------------------------------------------- St Stephen's Chapel (1292-1348)
{
  const cx = 22, cz = 6, w = 30, d = 12, h = 30;
  // vaulted undercroft (St Mary Undercroft) + the tall upper chapel
  g.add(box(w, h, d, pale, cx, 0, cz));
  g.add(box(w + 1.0, 1.0, d + 1.0, port, cx, 11.5, cz));            // string course at chapel floor
  g.add(box(w + 1.0, 1.2, d + 1.0, port, cx, h - 1.2, cz));
  g.add(crenelRing(w + 1.0, d + 1.0, 0.8, port, cx, h, cz, 1.4, 1.4, 1.2));
  g.add(hipRoof(w - 1, d - 1, 4.5, lead, cx, h, cz, 0.75));
  for (let i = 0; i < 5; i++) {
    const bx = cx - w / 2 + (i + 0.5) * w / 5;
    for (const s of [-1, 1]) {
      g.add(box(3.4, 13.0, 0.5, dark, bx, 14.0, cz + s * d / 2));   // tall upper windows
      g.add(box(2.4, 5.0, 0.4, dark, bx, 3.5, cz + s * d / 2));     // undercroft lights
    }
  }
  for (let i = 0; i <= 5; i++) {
    const bx = cx - w / 2 + i * w / 5;
    for (const s of [-1, 1]) {
      g.add(box(1.8, h, 2.4, port, bx, 0, cz + s * (d / 2 + 0.9)));
      g.add(pinnacle(1.3, 6.0, port, bx, h, cz + s * (d / 2 + 0.9)));
    }
  }
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]]) {           // corner stair turrets
    g.add(cyl(2.2, 2.4, h + 5, port, cx + a[0] * (w / 2 + 0.4), 0, cz + a[1] * (d / 2 + 0.4), 8));
    g.add(cone(2.7, 6.0, lead, cx + a[0] * (w / 2 + 0.4), h + 5, cz + a[1] * (d / 2 + 0.4), 8));
  }
  g.add(box(0.8, 16.0, 9.0, dark, cx + w / 2 + 0.3, 13.0, cz));     // great east window
  // St Stephen's cloister on the river side
  const clx = cx + 2, clz = cz + 22;
  for (const [ox, oz, ww, dd] of [[0, -10, 26, 6], [0, 10, 26, 6], [-10, 0, 6, 14], [10, 0, 6, 14]]) {
    g.add(box(ww, 8.0, dd, pale, clx + ox, 0, clz + oz));
    g.add(hipRoof(ww, dd, 3.0, lead, clx + ox, 8.0, clz + oz, 0.6));
  }
  g.add(box(14, 0.4, 14, M.grass, clx, 0.2, clz));
}

// ---------------------------------------------------------------- Painted Chamber & royal lodgings
{
  const cx = 68, cz = 14;
  g.add(box(26, 14, 11, med, cx, 0, cz));
  g.add(gableRoof(26, 11, 6.0, lead, cx, 14, cz, true, 0.6));
  for (let i = 0; i < 4; i++) for (const s of [-1, 1])
    g.add(box(2.6, 6.0, 0.5, dark, cx - 9 + i * 6, 5.5, cz + s * 5.5));
  for (const s of [-1, 1]) g.add(turret(2.0, 19, med, lead, cx + s * 13, 0, cz - 5.5, 8, 5));
  // Prince's Chamber / Queen's lodgings, stepping down to the river
  g.add(box(20, 12, 12, brick, cx + 4, 0, cz + 20));
  g.add(hipRoof(20, 12, 5.0, tile, cx + 4, 12, cz + 20, 0.6));
  for (const o of [-6, 0, 6]) {
    g.add(box(1.8, 1.4, 1.8, M.brick, cx + 4 + o, 16.4, cz + 20));
    g.add(cyl(0.5, 0.55, 4.6, M.brick, cx + 4 + o, 17.8, cz + 20, 8));
  }
}

// ---------------------------------------------------------------- river range and water stairs (+z)
{
  g.add(box(120, 11, 13, med, 20, 0, 44));
  g.add(hipRoof(120, 13, 5.0, tile, 20, 11, 44, 0.85));
  for (let i = 0; i < 16; i++) for (const s of [-1, 1])
    g.add(box(2.2, 2.2, 0.4, dark, -36 + i * 7.5, 5.0, 44 + s * 6.5));
  for (const tx of [-30, 10, 50, 76]) {
    g.add(box(9, 17, 9, med, tx, 0, 48));
    g.add(hipRoof(9, 9, 3.5, lead, tx, 17, 48, 0.15));
  }
  // the Palace stairs into the Thames
  g.add(box(18, 2.6, 22, med, 30, -0.6, 62));
  g.add(box(14, 1.0, 16, med, 30, 2.0, 64));
  for (const s of [-1, 1]) {
    g.add(cyl(1.2, 1.4, 5.0, port, 30 + s * 5.5, 3.0, 58, 8));
    g.add(dome(1.3, port, 30 + s * 5.5, 8.0, 58, 8, 1.1));
  }
}

// ---------------------------------------------------------------- the jumble: courts, offices, lodgings
const jumble = [
  [-96, 16, 22, 12, 10], [-70, 22, 26, 12, 9], [-30, 24, 24, 12, 10],
  [-4, 30, 20, 11, 9], [-96, -34, 20, 12, 9], [-64, -36, 26, 12, 10],
  [-24, -34, 22, 11, 9], [4, -30, 18, 12, 9], [44, -26, 24, 12, 10],
  [80, -20, 20, 12, 9], [96, 6, 16, 20, 10], [-112, -6, 14, 26, 10],
];
for (const [x, z, w, d, h] of jumble) {
  const m = (x + z) % 3 === 0 ? brick : med;
  g.add(box(w, h, d, m, x, 0, z));
  g.add(gableRoof(Math.max(w, d), Math.min(w, d), Math.min(w, d) * 0.4, tile, x, h, z, w >= d, 0.5));
  const n = Math.max(2, Math.floor(Math.max(w, d) / 5));
  for (let i = 0; i < n; i++) {
    const u = -Math.max(w, d) / 2 + (i + 0.5) * Math.max(w, d) / n;
    if (w >= d) g.add(box(1.8, 1.8, 0.4, dark, x + u, h * 0.45, z + d / 2));
    else g.add(box(0.4, 1.8, 1.8, dark, x + w / 2, h * 0.45, z + u));
  }
  g.add(box(1.4, 3.4, 1.4, M.brick, x, h + Math.min(w, d) * 0.3, z));
}

// ---------------------------------------------------------------- the Jewel Tower (1365)
{
  const cx = -108, cz = 34;
  g.add(box(11, 14, 11, med, cx, 0, cz));
  g.add(box(6, 15, 6, med, cx + 6, 0, cz - 5));
  g.add(crenelRing(11.6, 11.6, 0.8, med, cx, 14, cz, 1.4, 1.4, 1.2));
  g.add(hipRoof(10, 10, 3.5, lead, cx, 14, cz, 0.2));
  g.add(cyl(1.8, 2.0, 19, med, cx - 5.5, 0, cz + 5.5, 8));
  g.add(cone(2.2, 4.0, lead, cx - 5.5, 19, cz + 5.5, 8));
  for (const f of [0.3, 0.62]) for (const s of [-1, 1]) g.add(box(1.6, 2.4, 0.4, dark, cx, 14 * f, cz + s * 5.5));
  g.add(box(26, 1.0, 20, M.water, cx + 2, -0.7, cz + 4));     // its moat
}

// ---------------------------------------------------------------- yards
g.add(box(54, 0.3, 34, mat(0x968f7d), -50, 0, 24));           // New Palace Yard
g.add(box(40, 0.3, 26, mat(0x968f7d), 44, 0, -8));            // Old Palace Yard

g.position.z = -8;
await exportGLB(g, out('old_palace_of_westminster'));
