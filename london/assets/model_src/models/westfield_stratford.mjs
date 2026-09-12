// Westfield Stratford City (2011) - a ~500 x 200 m shopping centre: three linked
// mall blocks under long curved barrel roofs, with the multi-storey car parks and
// the bridge to the Olympic Park.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, exportGLB, out, loft, roundRect } from '../london_lib.mjs';

const g = new THREE.Group();
const AL = m(P.alu), STL = m(P.steel), GL = m(P.paleGlass), DC = m(P.darkConcrete), CN = m(P.concrete);

// --- the main mall mass ------------------------------------------------------------
g.add(box(470, 22, 170, AL, 0, 0, 0));
for (let y = 5; y < 22; y += 5.5) g.add(box(471, 1.4, 171, CN, 0, y, 0));
// glazed shopfront band along the +z front
g.add(box(460, 9, 6, GL, 0, 1, 86));

// --- three curved barrel roofs running along x -------------------------------------
for (const z of [-56, 0, 56]) {
  g.add(loft([{ y: 22, pts: roundRect(466, 50, 12, 4, 0, z) },
              { y: 29, pts: roundRect(452, 34, 10, 4, 0, z) },
              { y: 33, pts: roundRect(430, 14, 6, 4, 0, z) }], STL));
  // rooflight ridge
  g.add(box(400, 1.4, 9, GL, 0, 33, z));
}

// --- department-store anchors at each end -------------------------------------------
for (const sx of [-1, 1]) {
  g.add(box(70, 30, 96, CN, sx * 254, 0, -20));
  for (let y = 5; y < 30; y += 6) g.add(box(71, 1.5, 97, AL, sx * 254, y, -20));
  g.add(box(74, 2, 100, DC, sx * 254, 30, -20));
}

// --- multi-storey car parks behind (-z) ---------------------------------------------
for (const x of [-120, 120]) {
  g.add(box(150, 24, 60, CN, x, 0, -130));
  for (let y = 3; y < 24; y += 3.4) g.add(box(151, 1.6, 61, DC, x, y, -130));
}

// --- entrance drum and the bridge to the Olympic Park -------------------------------
g.add(cyl(26, 26, 26, GL, -140, 0, 60, 20));
g.add(cyl(28, 28, 2, STL, -140, 26, 60, 20));
g.add(box(16, 6, 76, GL, -230, 12, 124));
g.add(box(560, 1.0, 300, DC, 0, 0, -20));

await exportGLB(g, out('westfield_stratford'));
