// The Royal Exchange, William Tite 1844.  Portland stone, ~90 x 55 m.
// Orientation: long axis along X.  The great 8-column Corinthian PORTICO and pediment
// face +Z (the west front to Bank junction); the campanile with its cupola and the
// grasshopper vane stands at the far (+X / east) end.  Ground y=0.
import { exportGLB, box, cyl, cone, lathe, dome, hipRoof, THREE,
  P, M, column, colonnade, pediment, balustrade, arcade, openWall, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), gold = M(P.gold), dark = M(0x4a463d), glass = M(P.glassroof);

const W = 90, D = 55, H = 19;

g.add(box(W + 4, 1.4, D + 4, dk, 0, 0, 0));
// the main block: a hollow rectangle round a glazed courtyard
for (const [w, d, x, z] of [[W, 12, 0, D / 2 - 6], [W, 12, 0, -D / 2 + 6],
[13, D - 24, -W / 2 + 6.5, 0], [13, D - 24, W / 2 - 6.5, 0]]) {
  g.add(box(w, H, d, st, x, 1.4, z));
  g.add(box(w + 1.4, 1.6, d + 1.4, pale, x, 1.4 + H, z));
  g.add(balustrade(w + 1.4, d + 1.4, 2.0, pale, x, 3.0 + H, z));
}
// glazed courtyard roof
g.add(box(W - 30, 2.0, D - 26, glass, 0, 15.5, 0));
// blind arcade + windows along the flanks
for (const zs of [1, -1]) for (let i = 0; i < 13; i++) {
  const x = -W / 2 + 6 + i * (W - 12) / 12;
  g.add(box(3.4, 6.0, 0.6, dark, x, 4.0, zs * (D / 2 + 0.1)));
  g.add(box(3.0, 4.2, 0.6, dark, x, 12.5, zs * (D / 2 + 0.1)));
  g.add(box(1.5, H, 1.2, pale, x + 3.4, 1.4, zs * (D / 2 + 0.1)));
}

// ---------------------------------------------------------------- WEST PORTICO (+z)
{
  const PZ = D / 2 + 9;
  for (let i = 0; i < 6; i++) g.add(box(28 - i * 3.4, 0.55, 15 - i * 1.1, dk, 0, i * 0.55, PZ - 1.5));
  for (let i = 0; i < 8; i++) {
    const x = -12.6 + i * 3.6;
    g.add(column(1.15, 14.0, pale, x, 3.3, PZ, 12));
    if (i === 0 || i === 7) g.add(column(1.15, 14.0, pale, x, 3.3, PZ - 5.5, 12));
  }
  g.add(box(30.5, 3.2, 13.5, pale, 0, 17.3, PZ - 2.6));
  g.add(pediment(30.5, 6.6, 13.5, pale, 0, 20.5, PZ - 2.6));
  g.add(box(26, 4.2, 0.7, dk, 0, 21.3, PZ + 3.6));            // tympanum sculpture
  g.add(box(24, 14, 1.2, dark, 0, 3.3, PZ - 5.8));            // shadowed recess
}

// ---------------------------------------------------------------- CAMPANILE (east, +x)
{
  const tx = W / 2 - 9;
  const T = new THREE.Group();
  T.add(box(13, 24, 13, st, 0, 1.4, 0));
  T.add(box(14.2, 1.4, 14.2, pale, 0, 25.4, 0));
  T.add(box(10.6, 10, 10.6, st, 0, 26.8, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const d = new THREE.Mesh(new THREE.CylinderGeometry(2.7, 2.7, 0.8, 18), M(0xe8e4d8));
    if (dz) d.rotation.x = Math.PI / 2; else d.rotation.z = Math.PI / 2;
    d.position.set(dx * 5.5, 31.8, dz * 5.5); T.add(d);
  }
  T.add(box(12.0, 1.4, 12.0, pale, 0, 36.8, 0));
  // open belfry with columns
  T.add(cyl(3.6, 3.8, 8.0, st, 0, 38.2, 0, 12));
  for (let i = 0; i < 8; i++) {
    const a = i / 8 * Math.PI * 2;
    T.add(column(0.62, 8.0, pale, Math.cos(a) * 4.6, 38.2, Math.sin(a) * 4.6, 8));
  }
  T.add(cyl(5.6, 5.6, 1.4, pale, 0, 46.2, 0, 12));
  T.add(balustrade(0, 0, 0, pale, 0, 0, 0));
  // ogee lead cupola + grasshopper vane
  T.add(lathe([[4.4, 0], [4.2, 1.4], [3.4, 3.0], [2.1, 4.4], [1.1, 5.4], [0.4, 6.0], [0, 6.3]], lead, 0, 47.6, 0, 12));
  T.add(cyl(0.7, 0.9, 1.4, gold, 0, 53.9, 0, 8));
  T.add(cyl(0.16, 0.16, 2.4, gold, 0, 55.3, 0, 6));
  T.add(box(2.2, 0.7, 0.25, gold, 0.7, 57.0, 0));            // grasshopper vane
  T.position.set(tx, 0, 0);
  g.add(T);
}

await exportGLB(g, OUT + 'royal_exchange.glb');
