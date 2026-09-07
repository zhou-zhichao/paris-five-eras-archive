// Heron Tower / 110 Bishopsgate (2011, KPF) - 202 m to the roof, 230 m with the mast.
// Stacked three-storey "villages" read as a stepped facade; the service core is
// expressed as a separate slab on the -z side; exposed steel bracing on the +z face.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, strut, exportGLB, out, banded } from '../london_lib.mjs';

const g = new THREE.Group();
const W = 44, D = 32, H = 202;

// --- main glazed shaft, stepping back twice on the +x end -------------------------
g.add(banded(W, H, D, P.glass, P.darkGlass, 0, 0, 0, 4.0, 0.4));
g.add(banded(13, 150, D, P.glass, P.darkGlass, W / 2 + 6, 0, 0, 4.0, 0.4));
g.add(banded(13, 96, D, P.glass, P.darkGlass, W / 2 + 18.5, 0, 0, 4.0, 0.4));

// --- expressed service core slab on the -z side, taller than the office floors ----
g.add(box(W * 0.66, H + 10, 9, m(P.alu), 0, 0, -(D / 2 + 4.5)));
for (let y = 6; y < H; y += 12) g.add(box(W * 0.68, 1.4, 10, m(P.steel), 0, y, -(D / 2 + 4.5)));

// --- exposed inclined steel bracing on the +z (south) facade ----------------------
const NODE = 8, ST = H / NODE, ZF = D / 2 + 0.8;
for (let i = 0; i < NODE; i++) {
  const ya = i * ST, yb = (i + 1) * ST;
  g.add(strut([-W / 2 + 2, ya, ZF], [W / 2 - 2, yb, ZF], 0.8, m(P.steel), 5));
  g.add(strut([W / 2 - 2, ya, ZF], [-W / 2 + 2, yb, ZF], 0.8, m(P.steel), 5));
  g.add(strut([-W / 2, yb, ZF], [W / 2, yb, ZF], 0.9, m(P.steel), 5));
  // three-storey "village" split lines, slightly proud
  g.add(box(W + 1.2, 1.8, D + 1.2, m(P.alu), 0, yb - 1.8, 0));
}

// --- rooftop plant and the 28 m mast ----------------------------------------------
g.add(box(W * 0.8, 8, D * 0.8, m(P.black), 0, H, 0));
g.add(cyl(0.6, 1.6, 20, m(P.steel), 0, H + 8, 0, 8));
g.add(cyl(0.25, 0.6, 6, m(P.red), 0, H + 22, 0, 6));

// podium
g.add(box(W + 40, 9, D + 24, m(P.stone), 6, 0, 0));

await exportGLB(g, out('heron_tower'));
