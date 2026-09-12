// BT Tower / Post Office Tower (1964) - 177 m to the roof, 189 m with the mast.
// Slender concrete cylinder ~15 m dia on a wider base, microwave-dish galleries at
// two-thirds height, glazed revolving-restaurant ring near the top, lattice mast.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, strut, exportGLB, out, bandedCyl } from '../london_lib.mjs';

const g = new THREE.Group();
const RS = 7.5;                            // shaft radius (15 m diameter)

// wider base building + plinth
g.add(box(46, 8, 34, m(P.concrete), 0, 0, 0));
g.add(cyl(11.5, 12.5, 16, m(P.concrete), 0, 0, 0, 16));

// main shaft
g.add(cyl(RS, RS, 96, m(P.concrete), 0, 16, 0, 16));

// --- microwave dish galleries (three collars at ~112-142 m) -----------------------
for (const yb of [112, 124, 136]) {
  g.add(cyl(10.5, 10.5, 7.5, m(P.darkConcrete), 0, yb, 0, 16));
  g.add(cyl(11.2, 11.2, 0.8, m(P.alu), 0, yb + 7.5, 0, 16));
  for (let i = 0; i < 8; i++) {                       // dishes / horn antennae
    const a = i * Math.PI / 4;
    const c = Math.cos(a), s = Math.sin(a);
    g.add(strut([10 * c, yb + 3.8, 10 * s], [13.6 * c, yb + 3.8, 13.6 * s], 2.3, m(P.steel), 8));
  }
}
g.add(cyl(RS, RS, 12, m(P.concrete), 0, 144, 0, 16));

// --- glazed observation / revolving restaurant ring (156-172 m) -------------------
g.add(cyl(10.2, 10.2, 1.0, m(P.concrete), 0, 155, 0, 20));
g.add(bandedCyl(9.8, 16, P.paleGlass, P.alu, 0, 156, 0, 4.0, 20, 0.3));
g.add(cyl(10.6, 10.6, 1.2, m(P.concrete), 0, 172, 0, 20));

// plant deck to 177 m, then the mast to 189 m
g.add(cyl(6.0, 6.6, 4, m(P.darkConcrete), 0, 173.2, 0, 16));
g.add(cyl(1.0, 1.9, 9, m(P.steel), 0, 177, 0, 8));
g.add(cyl(0.35, 0.9, 4, m(P.red), 0, 186, 0, 6));

await exportGLB(g, out('bt_tower'));
