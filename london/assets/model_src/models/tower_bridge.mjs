// Tower Bridge, Horace Jones / John Wolfe Barry, 1886-1894.
// Orientation: bridge axis along X, water level y=0, roadway deck 8.6 m above water.
// Total length 244 m; two Gothic towers 65 m on piers; central bascule span 61 m clear;
// two 82 m suspension side spans with chains to shore abutments; high-level walkways at 43 m.
// (The upstream/downstream faces are identical; +Z is arbitrarily the downstream face.)
import { exportGLB, box, cyl, cone, lathe, prism, gableRoof, hipRoof, THREE,
  P, M, pinnacle, openWall, arcade, OUT } from './_lib_wren_edwardian.mjs';

const g = new THREE.Group();
const gran = M(0x8d8378), st = M(P.stone), pale = M(P.pale), slate = M(P.slate),
  cop = M(P.copper), iron = M(P.iron), dark = M(0x2f3134), road = M(0x55565a), blue = M(0x3f5f78);

const DECK = 8.6;          // roadway level
const TX = 30.5;           // tower centre  (61 m clear bascule span between the pier faces)
const AX = 112;            // shore abutment tower centre
const TOWH = 65;           // top of the tower spires

// ---------------------------------------------------------------- piers
for (const s of [-1, 1]) {
  g.add(box(30, DECK + 1.4, 26, gran, s * TX, 0, 0));
  g.add(box(32, 1.2, 28, gran, s * TX, DECK - 1.0, 0));
  // cutwaters
  for (const zs of [-1, 1]) g.add(cyl(6.5, 7.5, DECK, gran, s * TX, 0, zs * 13, 12));
}

// ---------------------------------------------------------------- roadway deck
g.add(box(244, 1.6, 18, iron, 0, DECK - 1.6, 0));
g.add(box(244, 0.5, 16, road, 0, DECK, 0));
// deck edge girders / parapet
for (const zs of [-1, 1]) g.add(box(244, 1.6, 0.8, blue, 0, DECK + 0.5, zs * 8.4));
// bascule joint marks
for (const s of [-1, 1]) g.add(box(0.6, 1.9, 18, dark, s * 0.4, DECK - 1.7, 0));

// ---------------------------------------------------------------- main towers (65 m)
function tower(sx) {
  const T = new THREE.Group();
  const y0 = DECK - 1.0;             // 7.6
  const H1 = 30;                     // lower stage -> 37.6 m
  // the two legs either side of the roadway
  for (const zs of [-1, 1]) {
    T.add(box(19, H1, 5.0, st, 0, y0, zs * 7.6));
    for (let i = 0; i < 3; i++) T.add(box(3.4, 8, 0.6, dark, -6 + i * 6, y0 + 6, zs * 10.2));
    for (let i = 0; i < 3; i++) T.add(box(3.0, 6, 0.6, dark, -6 + i * 6, y0 + 19, zs * 10.2));
  }
  // end screens with the big pointed arch the road passes through (facing +-x)
  for (const s of [-1, 1]) {
    const w = openWall(20, H1, 1.8, st, [{ cx: 0, y0: 0, w: 11, h: 9, arch: 'pointed', pointed: 1.35 }], 0, 0, 0, 6);
    const gg = new THREE.Group(); gg.add(w); gg.rotation.y = Math.PI / 2; gg.position.set(s * 9.0, y0, 0);
    T.add(gg);
  }
  T.add(box(20.5, 1.6, 21.5, pale, 0, y0 + H1, 0));         // cornice ~39 m
  // middle stage carrying the walkways
  T.add(box(17, 8, 18, st, 0, y0 + 31.6, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.7 : 8, 5.5, dz ? 0.7 : 8, dark, dx * 8.6, y0 + 33, dz * 8.6));
  T.add(box(19, 1.6, 20, pale, 0, y0 + 39.6, 0));           // walkway-level cornice ~48 m
  // upper stage
  T.add(box(14, 6, 15, st, 0, y0 + 41.2, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.7 : 6, 4.0, dz ? 0.7 : 6, dark, dx * 7.1, y0 + 42.2, dz * 7.1));
  T.add(box(15.5, 1.4, 16.5, pale, 0, y0 + 47.2, 0));
  // steep pyramidal roof + lantern spire, apex 65 m
  T.add(hipRoof(14, 15, 5.0, cop, 0, y0 + 48.6, 0, 0.15));
  T.add(cyl(1.2, 1.6, 1.5, pale, 0, y0 + 53.6, 0, 8));
  T.add(cone(1.5, 1.8, cop, 0, y0 + 55.1, 0, 8));
  T.add(cyl(0.2, 0.2, 0.5, M(P.gold), 0, y0 + 56.9, 0, 6));
  // four corner turrets with conical caps
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) {
    const px = dx * 9.2, pz = dz * 9.8;
    T.add(cyl(2.3, 2.5, 42, st, px, y0, pz, 8));
    T.add(cyl(2.9, 2.9, 1.2, pale, px, y0 + 42, pz, 8));
    T.add(cone(2.8, 7.0, cop, px, y0 + 43.2, pz, 8));
    T.add(cyl(0.18, 0.18, 1.2, M(P.gold), px, y0 + 50.2, pz, 6));
  }
  T.position.set(sx, 0, 0);
  return T;
}
g.add(tower(-TX));
g.add(tower(TX));

// ---------------------------------------------------------------- high-level walkways (43 m)
for (const zs of [-1, 1]) {
  const z = zs * 5.2;
  g.add(box(2 * TX + 10, 1.2, 4.4, iron, 0, 42.2, z));
  g.add(box(2 * TX + 10, 3.4, 0.5, blue, 0, 43.4, z + 2.1));
  g.add(box(2 * TX + 10, 3.4, 0.5, blue, 0, 43.4, z - 2.1));
  g.add(box(2 * TX + 10, 0.9, 4.8, iron, 0, 46.8, z));
  // lattice bracing under the walkways
  for (let i = 0; i < 14; i++) {
    const x = -TX + 2 + i * (2 * TX - 4) / 13;
    g.add(box(0.5, 2.6, 0.5, iron, x, 39.6, z));
  }
}
g.add(box(2 * TX - 12, 1.0, 12, iron, 0, 39.0, 0));   // cross bracing between walkways

// ---------------------------------------------------------------- shore abutment towers
for (const s of [-1, 1]) {
  const x = s * AX;
  g.add(box(16, DECK + 12, 22, gran, x, 0, 0));
  g.add(box(17.5, 1.4, 23.5, pale, x, DECK + 12, 0));
  for (const zs of [-1, 1]) {
    g.add(cyl(2.0, 2.2, DECK + 18, st, x - 6.5, 0, zs * 9.5, 8));
    g.add(cyl(2.0, 2.2, DECK + 18, st, x + 6.5, 0, zs * 9.5, 8));
    g.add(cone(2.4, 5.0, cop, x - 6.5, DECK + 18, zs * 9.5, 8));
    g.add(cone(2.4, 5.0, cop, x + 6.5, DECK + 18, zs * 9.5, 8));
  }
}

// ---------------------------------------------------------------- suspension chains + hangers
// straight-segment chain from the tower (high) down to the abutment (low), slight sag
function chain(sx, zs) {
  const x0 = sx * (TX + 10), y1 = 38.0;         // springing at the tower
  const x1 = sx * (AX - 8), y2 = 18.0;          // anchorage at the abutment
  const n = 8, sag = 3.2;
  let px = x0, py = y1;
  for (let i = 1; i <= n; i++) {
    const t = i / n;
    const nx = x0 + (x1 - x0) * t;
    const ny = y1 + (y2 - y1) * t - Math.sin(Math.PI * t) * sag;
    const len = Math.hypot(nx - px, ny - py);
    const seg = box(len, 1.5, 1.4, blue, (nx + px) / 2, (ny + py) / 2 - 0.75, zs * 8.0);
    seg.rotation.z = Math.atan2(ny - py, nx - px);
    g.add(seg);
    // vertical hanger down to the deck
    if (i < n) g.add(box(0.5, ny - DECK - 1.6, 0.5, blue, nx, DECK + 1.0, zs * 8.0));
    px = nx; py = ny;
  }
}
for (const sx of [-1, 1]) for (const zs of [-1, 1]) chain(sx, zs);

// approach viaduct arches beyond the abutments
for (const s of [-1, 1]) {
  g.add(box(12, DECK - 0.5, 16, gran, s * 118, 0, 0));
}

await exportGLB(g, OUT + 'tower_bridge.glb');
