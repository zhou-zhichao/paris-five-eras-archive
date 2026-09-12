// Broadgate Tower, Primrose Street (2008, SOM) - 164.3 m, 35 storeys, with big
// exposed diagonal cross-bracing running up the two short (end) elevations.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, strut, exportGLB, out, banded } from '../london_lib.mjs';

const g = new THREE.Group();
const W = 42, D = 30, H = 164.3;

g.add(banded(W, H, D, P.glass, P.darkGlass, 0, 0, 0, 4.2, 0.4));

// --- exposed X bracing on both end walls, in 5-storey modules ---------------------
const NODE = 8, ST = H / NODE;
for (const sx of [-1, 1]) {
  const X = sx * (W / 2 + 0.7);
  for (let i = 0; i < NODE; i++) {
    const ya = i * ST, yb = (i + 1) * ST;
    g.add(strut([X, ya, -D / 2 + 1], [X, yb, D / 2 - 1], 1.0, m(P.steel), 5));
    g.add(strut([X, ya, D / 2 - 1], [X, yb, -D / 2 + 1], 1.0, m(P.steel), 5));
    g.add(strut([X, yb, -D / 2], [X, yb, D / 2], 0.9, m(P.alu), 5));
  }
}
// slimmer bracing carried round onto the long facades
for (const sz of [-1, 1]) {
  const Z = sz * (D / 2 + 0.7);
  for (let i = 0; i < NODE; i++) {
    const ya = i * ST, yb = (i + 1) * ST;
    g.add(strut([-W / 2 + 1, ya, Z], [W / 2 - 1, yb, Z], 0.7, m(P.steel), 5));
    g.add(strut([W / 2 - 1, ya, Z], [-W / 2 + 1, yb, Z], 0.7, m(P.steel), 5));
  }
}

// rooftop plant and the linked lower block (201 Bishopsgate) on the -x side
g.add(box(W * 0.85, 7, D * 0.85, m(P.black), 0, H, 0));
g.add(banded(56, 56, D + 6, P.paleGlass, P.alu, -W / 2 - 30, 0, 0, 4.2, 0.4));
g.add(box(W + 74, 8, D + 20, m(P.stone), -18, 0, 0));

await exportGLB(g, out('broadgate_tower'));
