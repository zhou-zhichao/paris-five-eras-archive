// Thames Barrier, Woolwich Reach (1982) - 520 m across the river, nine piers
// under stainless-steel shell hoods, rising gates shown lowered (open to shipping).
// Convention: metres, WATER SURFACE y=0, structure centred on the origin,
//             long axis x across the river, front (downstream) +z.
import { THREE, group, m, P, box, exportGLB, out, loft, ellipse, roundRect } from '../london_lib.mjs';

const g = new THREE.Group();
const CONC = m(P.concrete), STL = m(P.steel), DK = m(P.darkConcrete);

// pier centres: four big central piers, then progressively smaller ones outboard
const PIERS = [[-224, 0.58], [-168, 0.78], [-112, 1.00], [-56, 1.00], [0, 1.00],
               [56, 1.00], [112, 1.00], [168, 0.78], [224, 0.58]];

for (const [x, s] of PIERS) {
  const L = 28 * s, Wd = 12 * s, HH = 20 * s;             // hood length / width / height
  // concrete pier sitting in the water
  g.add(box(L * 0.92, 6, Wd + 5, CONC, x, -2.5, 0));
  g.add(box(L * 0.82, 3.5, Wd + 8, DK, x, 3.5, 0));
  // the stainless shell hood: a curved shell, pointed at both ends
  const secs = [];
  const NN = 8;
  for (let i = 0; i <= NN; i++) {
    const t = i / NN;
    secs.push({ y: 7 + HH * t, pts: ellipse(L / 2 * Math.pow(1 - t, 0.45), Wd / 2 * Math.pow(1 - t, 0.75), 16) });
  }
  g.add(loft(secs, STL, x, 0, 0, true, false));
}

// --- the lowered gates lying in their sills on the river bed ---------------------
for (let i = 0; i < PIERS.length - 1; i++) {
  const x0 = PIERS[i][0], x1 = PIERS[i + 1][0];
  g.add(box((x1 - x0) - 16, 3.5, 16, DK, (x0 + x1) / 2, -4.5, 0));
}
// river bed sill and the bank abutments
g.add(box(500, 2.5, 30, DK, 0, -7, 0));
g.add(box(44, 12, 50, CONC, -248, -4, 0));
g.add(box(44, 12, 50, CONC, 248, -4, 0));

await exportGLB(g, out('thames_barrier'));
