// The Tower of London as completed by Edward I (c. 1300): a concentric fortress
// of two curtain walls and a moat around William I's White Tower.
// CONVENTION: metres, ground y=0 (moat water at -0.6), footprint centred on the
// origin, LONG axis along x (west entrance / Lion Gate at -x, Iron Gate at +x).
// "Front" = +z is the RIVER (south) side, with St Thomas's Tower / Traitors' Gate.
//
// True dimensions: site ~200 x 180 m over the moat; White Tower 36 x 32 m, 27 m
// to the battlements with corner turrets to 36 m; inner curtain ~12 m with 13
// towers; outer curtain ~9 m.
import {
  exportGLB, out, M, mat, box, cyl, cone, dome, gableRoof, hipRoof, lathe, group, THREE,
  wall, archPath, crenel, crenelRing, turret, pinnacle, ellipseRing,
} from './_lib_london.mjs';

const g = new THREE.Group();
const rag = M.rag, med = M.medieval, pale = M.pale, dark = M.dark, lead = M.lead;
const timb = M.darkTimber, plaster = M.whitewash, tile = M.tile;

// ---------------------------------------------------------------- moat + ward platform
const MX = 100, MZ = 88;                       // outer edge of the moat
g.add(box(MX * 2, 2.4, MZ * 2, M.water, 0, -2.4, 0));
g.add(box(MX * 2 + 14, 1.6, MZ * 2 + 14, M.grass, 0, -3.4, 0));    // counterscarp bank
const WX = 82, WZ = 70;                        // the walled island inside the moat
g.add(box(WX * 2, 3.0, WZ * 2, M.grass, 0, -2.4, 0));
g.add(box(WX * 2 - 4, 0.6, WZ * 2 - 4, mat(0x8f8f78), 0, 0.6, 0));  // outer ward surface

// ---------------------------------------------------------------- curtain wall helper
function curtain(hw, hz, h, t, m, crenH, gateGaps = []) {
  const gg = new THREE.Group();
  // four straight runs
  gg.add(box(hw * 2, h, t, m, 0, 0, -hz + t / 2));
  gg.add(box(hw * 2, h, t, m, 0, 0, hz - t / 2));
  gg.add(box(t, h, hz * 2 - 2 * t, m, -hw + t / 2, 0, 0));
  gg.add(box(t, h, hz * 2 - 2 * t, m, hw - t / 2, 0, 0));
  // wall-walk parapet
  for (const s of [-1, 1]) {
    gg.add(crenel(hw * 2, t * 0.35, m, 0, h, s * (hz - t * 0.2), true, crenH, 1.5, 1.2));
    gg.add(crenel(hz * 2 - 2 * t, t * 0.35, m, s * (hw - t * 0.2), h, 0, false, crenH, 1.5, 1.2));
  }
  return gg;
}
// a drum tower with a crenellated top
function drum(r, h, m, x, z, seg = 12, crenH = 1.4, cap = null) {
  const gg = group(
    cyl(r, r * 1.06, h, m, 0, 0, 0, seg),
    cyl(r + 0.5, r + 0.5, 0.8, m, 0, h, 0, seg),
  );
  // arrow-loop slits
  for (let i = 0; i < 4; i++) {
    const a = i * Math.PI / 2 + 0.4;
    gg.add(box(0.4, 2.6, 0.4, dark, (r - 0.1) * Math.cos(a), h * 0.55, (r - 0.1) * Math.sin(a)));
  }
  const ring = new THREE.Group();
  const n = Math.max(6, Math.round(2 * Math.PI * r / 2.2));
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    const b = box(1.4, crenH, 0.7, m, (r + 0.1) * Math.cos(a), h + 0.8, (r + 0.1) * Math.sin(a));
    b.rotation.y = Math.PI / 2 - a; ring.add(b);
  }
  gg.add(ring);
  if (cap) gg.add(cone(r + 0.6, cap, lead, 0, h + 0.8, 0, seg));
  gg.position.set(x, 0, z);
  return gg;
}

// ---------------------------------------------------------------- outer curtain (9 m)
const OX = 78, OZ = 66;
g.add(curtain(OX, OZ, 9, 4.0, rag, 1.3));
for (const x of [-52, -26, 0, 26, 52]) for (const s of [-1, 1]) g.add(drum(5.4, 11, rag, x, s * OZ, 10));
for (const s of [-1, 1]) for (const t of [-1, 1]) g.add(drum(6.2, 12, rag, s * OX, t * OZ, 10));
for (const z of [-33, 33]) for (const s of [-1, 1]) g.add(drum(5.4, 11, rag, s * OX, z, 10));

// ---------------------------------------------------------------- inner curtain (12 m) + 13 towers
const IX = 54, IZ = 40;
g.add(curtain(IX, IZ, 12, 5.0, med, 1.6));
const innerTowers = [
  [-IX, -IZ], [IX, -IZ], [-IX, IZ], [IX, IZ],          // corner towers
  [-27, -IZ], [0, -IZ], [27, -IZ],                     // north (Devereux/Flint/Bowyer side)
  [-30, IZ], [0, IZ], [30, IZ],                        // river side: Bell, Wakefield, Lanthorn
  [-IX, 0], [IX, 0], [IX, -20],                        // Beauchamp, Broad Arrow, Salt
];
for (const [x, z] of innerTowers) g.add(drum(6.0, 17, med, x, z, 12, 1.6));
// Wakefield Tower: the big drum on the river side by the water gate
g.add(drum(8.0, 20, med, -30, IZ, 14, 1.8));

// ---------------------------------------------------------------- White Tower
{
  const w = 36, d = 32, h = 27, cx = 6, cz = -4;
  g.add(box(w, h, d, pale, cx, 0, cz));
  // pilaster strips
  for (const bx of [-12, 0, 12]) for (const s of [-1, 1]) g.add(box(2.6, h, 1.0, pale, cx + bx, 0, cz + s * (d / 2)));
  for (const bz of [-8, 8]) for (const s of [-1, 1]) g.add(box(1.0, h, 2.6, pale, cx + s * (w / 2), 0, cz + bz));
  // two bands of round-headed Norman windows
  for (const f of [0.42, 0.68]) {
    for (const bx of [-14, -7, 0, 7, 14]) for (const s of [-1, 1])
      g.add(box(1.8, 3.6, 0.5, dark, cx + bx, h * f, cz + s * (d / 2)));
    for (const bz of [-10, -3, 4, 11]) for (const s of [-1, 1])
      g.add(box(0.5, 3.6, 1.8, dark, cx + s * (w / 2), h * f, cz + bz));
  }
  // apsidal projection of St John's Chapel at the south-east corner
  g.add(cyl(6.0, 6.0, h, pale, cx + w / 2 + 2.0, 0, cz + 8, 12));
  // battlements + the four corner turrets (three square, one round) to 36 m
  g.add(box(w + 1.6, 1.2, d + 1.6, pale, cx, h, cz));
  g.add(crenelRing(w + 1.6, d + 1.6, 1.0, pale, cx, h + 1.2, cz, 1.7, 1.7, 1.5));
  const T = [[-1, -1, 'sq'], [1, -1, 'sq'], [-1, 1, 'rd'], [1, 1, 'sq']];
  for (const [sx, sz, kind] of T) {
    const tx = cx + sx * (w / 2 - 1.5), tz = cz + sz * (d / 2 - 1.5);
    if (kind === 'sq') {
      g.add(box(6.4, 9.0, 6.4, pale, tx, h, tz));
      g.add(crenelRing(7.0, 7.0, 0.9, pale, tx, h + 9.0, tz, 1.3, 1.3, 1.1));
      g.add(lathe([[3.4, 0], [3.6, 1.4], [2.4, 3.6], [0.9, 5.4], [0.25, 6.6]], lead, tx, h + 9.9, tz, 10));
    } else {
      g.add(cyl(3.4, 3.4, 9.0, pale, tx, h, tz, 12));
      g.add(cyl(3.9, 3.9, 0.8, pale, tx, h + 9.0, tz, 12));
      g.add(lathe([[3.6, 0], [3.8, 1.4], [2.5, 3.8], [1.0, 5.6], [0.25, 6.8]], lead, tx, h + 9.8, tz, 12));
    }
    g.add(box(0.15, 2.2, 0.15, M.gold, tx, h + 16.4, tz));
    g.add(box(1.4, 0.7, 0.1, M.gold, tx + 0.7, h + 17.6, tz));
  }
}

// ---------------------------------------------------------------- Traitors' Gate / St Thomas's Tower (river, +z)
{
  const gx = -34;
  // the outer wall here is pierced by a wide water gate
  g.add(wall(26, 9, 4.0, rag, [archPath(0, 12.0, 0, 3.6, 4.4, 0, 10)], gx, 0, OZ - 2.0));
  g.add(box(13.0, 3.2, 6.0, M.water, gx, -1.0, OZ - 2.0));       // the water basin behind it
  g.add(box(13.0, 0.4, 20.0, M.water, gx, -1.0, OZ - 10));
  // St Thomas's Tower above: stone base, timber-framed upper storey, two turrets
  g.add(box(26, 4.5, 13.0, rag, gx, 9, OZ - 5.5));
  g.add(box(24, 4.2, 12.0, plaster, gx, 13.5, OZ - 5.5));
  for (const bx of [-8, -3, 2, 7]) g.add(box(0.5, 4.2, 12.2, timb, gx + bx, 13.5, OZ - 5.5));
  g.add(box(22, 2.2, 0.5, dark, gx, 15.0, OZ + 0.6));
  g.add(hipRoof(26, 13.5, 4.5, lead, gx, 17.7, OZ - 5.5, 0.6));
  for (const s of [-1, 1]) g.add(drum(3.2, 22, rag, gx + s * 13.5, OZ - 2.0, 10, 1.2, 5.0));
}

// ---------------------------------------------------------------- west entrance: Middle & Byward towers
{
  for (const s of [-1, 1]) g.add(drum(5.0, 14, rag, -OX + 1, 12 + s * 9, 10, 1.3));
  g.add(box(9, 15, 20, rag, -OX + 1, 0, 12));
  g.add(box(5.0, 6.5, 21, dark, -OX + 1, 0, 12));                 // gate passage
  g.add(crenelRing(10, 22, 0.9, rag, -OX + 1, 15, 12, 1.4, 1.5, 1.2));
  // causeway and the Lion Tower barbican out over the moat
  g.add(box(24, 3.0, 12, M.rag, -OX - 12, -0.6, 12));
  g.add(box(22, 9, 20, rag, -MX + 8, 0, 12));
  g.add(box(4.6, 6.0, 21, dark, -MX + 8, 0, 12));
  for (const s of [-1, 1]) g.add(drum(4.4, 12, rag, -MX + 8, 12 + s * 10, 10, 1.2));
}

// ---------------------------------------------------------------- inner ward buildings
// Great Hall / royal lodgings range along the river side of the inner ward
g.add(box(42, 11, 15, plaster, -14, 0.6, 24));
for (const bx of [-18, -10, -2, 6, 14]) g.add(box(0.5, 11, 15.2, timb, -14 + bx, 0.6, 24));
g.add(gableRoof(42, 15, 6.5, tile, -14, 11.6, 24, true, 0.6));
for (const bx of [-14, 0, 14]) g.add(box(1.6, 4.0, 1.6, M.brick, -14 + bx, 17.2, 24));
// Wardrobe / storehouse ranges
g.add(box(26, 9, 12, med, 30, 0.6, 24));
g.add(gableRoof(26, 12, 5.0, tile, 30, 9.6, 24, true, 0.5));
g.add(box(18, 8, 11, med, -34, 0.6, -26));
g.add(gableRoof(18, 11, 4.5, tile, -34, 8.6, -26, true, 0.5));
// Tower Green
g.add(box(26, 0.3, 18, M.grass, -28, 0.8, 4));

await exportGLB(g, out('tower_of_london'));
