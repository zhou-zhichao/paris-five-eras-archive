// Nelson's Column, Trafalgar Square, William Railton 1843 (lions by Landseer, 1867).
// Corinthian column of Dartmoor granite; overall 51.6 m to the top of the 5.5 m statue.
// Orientation: pedestal centred on the origin, four lions on a ~30 x 30 m stepped base;
// the principal (south) face looks +Z.
import { exportGLB, box, cyl, cone, lathe, THREE, P, M, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const gran = M(0x6f6a63), pale = M(P.pale), bronze = M(P.bronze), dk = M(P.dstone);

// stepped base
for (let i = 0; i < 4; i++) g.add(box(30 - i * 4, 0.7, 30 - i * 4, dk, 0, i * 0.7, 0));
// four Landseer lions (6.1 m long, 3.4 m high) on low plinths
for (const [sx, sz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) {
  const L = new THREE.Group();
  L.add(box(8.0, 1.6, 4.6, dk, 0, 0, 0));
  L.add(box(6.1, 2.0, 2.4, bronze, 0, 1.6, 0));           // body
  L.add(box(1.7, 1.5, 1.8, bronze, 2.6, 3.1, 0));         // head & mane
  L.add(box(2.6, 1.4, 2.2, bronze, -2.0, 3.0, 0));        // haunch
  L.rotation.y = sx > 0 ? 0 : Math.PI;
  L.position.set(sx * 9.5, 2.8, sz * 6.0);
  g.add(L);
}
// pedestal with bronze relief panels
g.add(box(11, 1.2, 11, dk, 0, 2.8, 0));
g.add(box(8.4, 8.0, 8.4, gran, 0, 4.0, 0));
for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
  g.add(box(dx ? 0.5 : 6.2, 4.0, dz ? 0.5 : 6.2, bronze, dx * 4.3, 6.0, dz * 4.3));
g.add(box(9.6, 1.4, 9.6, pale, 0, 12.0, 0));
g.add(box(7.0, 3.0, 7.0, gran, 0, 13.4, 0));
g.add(box(8.0, 1.0, 8.0, pale, 0, 16.4, 0));
// the fluted Corinthian column: base, 25 m shaft, acanthus capital
g.add(cyl(2.4, 2.7, 1.8, pale, 0, 17.4, 0, 16));
g.add(cyl(1.95, 2.25, 21.6, gran, 0, 19.2, 0, 16));
for (let i = 0; i < 16; i++) {
  const a = i / 16 * Math.PI * 2, r = 2.15;
  const f = box(0.36, 21.6, 0.36, M(0x7c766e), Math.cos(a) * r, 19.2, Math.sin(a) * r);
  f.rotation.y = -a; g.add(f);
}
g.add(lathe([[2.0, 0], [2.5, 1.0], [3.0, 2.4], [2.9, 3.2]], bronze, 0, 40.8, 0, 16));
g.add(box(6.4, 1.0, 6.4, pale, 0, 44.0, 0));             // abacus
g.add(box(4.0, 1.6, 4.0, pale, 0, 45.0, 0));             // statue plinth
// Nelson, 5.5 m
g.add(cyl(0.62, 0.78, 4.2, M(0x8a8378), 0, 46.6, 0, 10));
g.add(cyl(0.42, 0.5, 0.9, M(0x8a8378), 0, 50.8, 0, 8));

await exportGLB(g, OUT + 'nelsons_column.glb');
