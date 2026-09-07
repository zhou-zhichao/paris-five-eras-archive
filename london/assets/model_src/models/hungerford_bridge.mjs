// Hungerford (Charing Cross) railway bridge, Sir John Hawkshaw 1864 — wrought-iron lattice
// girders carried on paired cast-iron cylinder piers, using Brunel's old suspension-bridge
// abutments.  ~400 m long, rail deck ~8 m above the water.
// Orientation: bridge axis along X, water level y=0, +Z is the downstream face.
import { exportGLB, box, cyl, cone, THREE, P, M, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const iron = M(P.iron), ironl = M(0x585c60), gran = M(0x8d8378), pale = M(P.pale),
  dk = M(P.dstone), rail = M(0x4a4a4a), lead = M(P.lead);

const L = 400, DECK = 8.0, GD = 5.0;      // girder depth
const PIERS = [-150, -90, -30, 30, 90, 150];
const DW = 26;                            // deck width (nine tracks + footway)

// ---------------------------------------------------------------- paired cylinder piers
for (const px of PIERS) {
  for (const zs of [-1, 1]) for (const o of [-1, 1]) {
    const z = zs * 10.5 + o * 0;
    g.add(cyl(2.2, 2.6, DECK - GD / 2 + 1.0, iron, px, 0, zs * 10.5, 12));
    g.add(cyl(2.8, 2.8, 0.9, ironl, px, DECK - GD / 2 + 1.0, zs * 10.5, 12));
  }
  g.add(cyl(2.0, 2.4, DECK - GD / 2 + 1.0, iron, px, 0, 0, 12));
  g.add(cyl(2.6, 2.6, 0.9, ironl, px, DECK - GD / 2 + 1.0, 0, 12));
  g.add(box(3.2, 1.2, DW, ironl, px, DECK - GD / 2 + 1.9, 0));
}

// ---------------------------------------------------------------- lattice girders and deck
for (const zs of [-1, 1]) {
  const z = zs * (DW / 2 - 0.6);
  g.add(box(L, 1.0, 1.4, iron, 0, DECK - GD, z));          // bottom boom
  g.add(box(L, 1.1, 1.4, iron, 0, DECK - 1.1, z));         // top boom
  // lattice diagonals
  for (let i = 0; i < 100; i++) {
    const x = -L / 2 + 2 + i * (L - 4) / 99;
    const d = box(Math.hypot(4.0, GD - 2.1), 0.45, 0.7, iron, x, DECK - GD / 2 - 0.55, z);
    d.rotation.z = (i % 2 ? 1 : -1) * Math.atan2(GD - 2.1, 4.0);
    g.add(d);
  }
  // vertical posts over the piers
  for (const px of PIERS) g.add(box(1.1, GD, 1.6, ironl, px, DECK - GD, z));
}
g.add(box(L, 1.2, DW, ironl, 0, DECK - 1.2, 0));           // deck plate
g.add(box(L, 0.4, DW - 2, rail, 0, DECK, 0));
// rails
for (let i = 0; i < 8; i++) {
  const z = -10 + i * 2.9;
  g.add(box(L, 0.28, 0.22, M(0x6a6259), 0, DECK + 0.4, z - 0.7));
  g.add(box(L, 0.28, 0.22, M(0x6a6259), 0, DECK + 0.4, z + 0.7));
}
// parapets
for (const zs of [-1, 1]) g.add(box(L, 1.4, 0.5, ironl, 0, DECK + 0.4, zs * (DW / 2 - 0.3)));

// ---------------------------------------------------------------- masonry abutments
for (const sx of [-1, 1]) {
  g.add(box(24, DECK + 2.5, DW + 10, gran, sx * (L / 2 + 10), 0, 0));
  g.add(box(26, 1.4, DW + 12, pale, sx * (L / 2 + 10), DECK + 2.5, 0));
  for (const zs of [-1, 1]) g.add(cyl(3.0, 3.4, DECK + 6, gran, sx * (L / 2 + 2), 0, zs * (DW / 2 + 3), 12));
}

await exportGLB(g, OUT + 'hungerford_bridge.glb');
