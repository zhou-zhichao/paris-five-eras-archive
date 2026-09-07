// Guy's Tower, Guy's Hospital, Southwark (1974; re-clad 2014) - 143 m, 34 storeys.
// Two joined slabs - the wide ward block and the narrower communications block -
// with the tall plant/comms crown that makes the silhouette.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out, banded } from '../london_lib.mjs';

const g = new THREE.Group();
const H = 121;                       // top of the occupied floors; crown above

// --- the two joined slabs ----------------------------------------------------------
g.add(banded(46, H, 24, P.paleGlass, P.alu, -13, 0, 0, 3.5, 0.45));      // ward block
g.add(banded(28, H, 20, P.paleGlass, P.alu, 24, 0, 2, 3.5, 0.45));       // comms block
// the joint expressed as a solid stair/lift core
g.add(box(9, H + 4, 26, m(P.concrete), 8, 0, 0));

// --- the plant / communications crown (the recognisable top) ---------------------
g.add(box(46, 6, 24, m(P.darkConcrete), -13, H, 0));
g.add(box(30, 16, 20, m(P.alu), -13, H + 6, 0));
for (let y = H + 7; y < H + 21; y += 3.2) g.add(box(31, 1.2, 21, m(P.steel), -13, y, 0));
g.add(box(20, 12, 16, m(P.alu), 22, H, 2));
g.add(box(9, 143 - (H + 22), 9, m(P.darkConcrete), -13, H + 22, 0));     // to 143 m

// --- hospital podium and the low ward wings --------------------------------------
g.add(box(96, 20, 54, m(P.stone), -6, 0, -8));
for (let y = 3; y < 20; y += 3.5) g.add(box(97, 1.3, 55, m(P.glass), -6, y, -8));
g.add(box(60, 12, 30, m(P.brick), -70, 0, 22));
g.add(box(120, 1.0, 80, m(P.darkConcrete), -12, 0, 0));

await exportGLB(g, out('guys_tower'));
