// One 12 m bay of a London brick railway viaduct (London & Greenwich / Bermondsey type).
// Two piers + a semicircular arch, deck top 7 m, 9 m wide, brick parapets with stone coping.
// Long axis (the track) along x; repeats end-to-end at 12 m centres.
import { exportGLB, box, THREE, P, M, viaductX, tracksX, OUT,
  centreXZ } from './_lib_rail.mjs';

const g = new THREE.Group();
const BAY = 12, DECK = 7.0, W = 9.0;

g.add(viaductX(1, BAY, DECK, W, 0, 0, 0, { brick: P.stock, dark: 0xa08e6f, coping: P.dstone, pierW: 3.2, tile: true }));

// stringcourse under the parapet on both faces
for (const sz of [-1, 1]) {
  g.add(box(BAY, 0.4, 1.3, M(P.dstone), 0, DECK - 1.5, sz * (W / 2 - 0.2)));
}

// voussoir ring (archivolt) picked out round the arch on both faces
{
  const span = BAY - 3.2, r = span / 2, vert = Math.max(0.8, DECK - 1.2 - r);
  const ring = M(0xa88f6d), n = 22;
  for (const sz of [-1, 1]) {
    const zz = sz * (W / 2 - 0.1);
    for (let i = 0; i < n; i++) {
      const a = Math.PI * (i + 0.5) / n;
      const b = box(0.55, 0.95, 0.7, ring, Math.cos(a) * (r + 0.35), vert + Math.sin(a) * (r + 0.35) - 0.475, zz);
      b.rotation.z = a - Math.PI / 2;
      g.add(b);
    }
    // springing imposts
    for (const sx of [-1, 1]) g.add(box(1.3, 0.5, 0.9, M(P.dstone), sx * r, vert - 0.25, zz));
  }
}
// parapet coping courses and a refuge over the pier on each side
for (const sz of [-1, 1]) {
  g.add(box(BAY, 0.22, 1.25, M(0xc9c0ab), 0, DECK + 1.85, sz * (W / 2 - 0.35)));
  for (const sx of [-1, 1]) g.add(box(1.4, 1.7, 1.0, M(P.stock), sx * (BAY / 2 - 0.7), DECK, sz * (W / 2 - 0.5)));
}
// battered plinth courses at the foot of the piers
for (const sz of [-1, 1]) for (let i = 0; i < 3; i++)
  g.add(box(BAY, 0.4, 0.9 - i * 0.2, M(0x9c8a6b), 0, i * 0.4, sz * (W / 2 - 0.15 - i * 0.1)));
// ballast + a single track on the deck
g.add(tracksX(BAY, 4.6, 1, 0, DECK, 0));
for (let i = 0; i < 8; i++) g.add(box(0.28, 0.22, 3.2, M(0x5a4a38), -BAY / 2 + BAY * (i + 0.5) / 8, DECK - 0.2, 0));

await exportGLB(centreXZ(g), OUT + 'rail_viaduct_arch_unit.glb');
