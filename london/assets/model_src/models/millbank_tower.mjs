// Millbank Tower (1963, Ronald Ward & Partners) - 118 m, 32 storeys. A glass slab
// with fully curved (semicircular) ends, on a low riverside podium.
// Convention: metres, ground y=0, footprint centred on origin, long axis x,
//             front (river) +z.
import { THREE, group, m, P, box, exportGLB, out, loft, roundRect } from '../london_lib.mjs';

const g = new THREE.Group();
const W = 42, D = 21, H = 118;

const plan = roundRect(W, D, D / 2, 10);           // stadium shape: fully curved ends
g.add(loft([{ y: 0, pts: plan }, { y: H, pts: plan }], m(P.glass)));

// strong horizontal spandrel banding, one band per floor
const big = roundRect(W + 0.9, D + 0.9, D / 2 + 0.45, 10);
for (let y = 3; y < H; y += 3.5) g.add(loft([{ y, pts: big }, { y: y + 1.3, pts: big }], m(P.paleGlass), 0, 0, 0, false, false));
// the two vertical service slots on the long facades
for (const sz of [-1, 1]) g.add(box(6, H, D + 1.4, m(P.stone), 0, 0, 0));

// crown: plant room and the mast
g.add(loft([{ y: H, pts: roundRect(W * 0.8, D * 0.8, D * 0.4, 8) },
            { y: H + 6, pts: roundRect(W * 0.8, D * 0.8, D * 0.4, 8) }], m(P.darkConcrete)));

// --- low riverside blocks ----------------------------------------------------------
g.add(box(86, 14, 30, m(P.stone), -8, 0, -34));
for (let y = 3; y < 14; y += 3.5) g.add(box(87, 1.2, 31, m(P.paleGlass), -8, y, -34));
g.add(box(58, 10, 26, m(P.stone), 42, 0, 16));
g.add(box(130, 1.0, 88, m(P.darkConcrete), 0, 0, -10));

await exportGLB(g, out('millbank_tower'));
