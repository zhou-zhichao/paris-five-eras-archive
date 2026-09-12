// 30 St Mary Axe, "the Gherkin" (2003) - 180 m, 41 storeys, max diameter 56.5 m at level 16.
// Foster + Partners. Curved lathe form + six dark spiralling light-well stripes over a diagrid.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, cyl, dome, box, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();

// --- radius profile (metres) -------------------------------------------------------
const PROF = [[0, 24.5], [18, 26.6], [40, 27.8], [72, 28.25], [100, 27.3], [125, 24.6],
              [145, 20.6], [160, 15.6], [170, 10.6], [176, 6.0], [180, 2.2]];
function rAt(y) {
  for (let i = 0; i < PROF.length - 1; i++) {
    const [y0, r0] = PROF[i], [y1, r1] = PROF[i + 1];
    if (y <= y1) return r0 + (r1 - r0) * (y - y0) / (y1 - y0);
  }
  return PROF[PROF.length - 1][1];
}

// --- skin built as quads so the spiral stripes can be coloured individually ---------
const SEG = 24, LEV = 26, TOP = 180;
const glassPos = [], darkPos = [], bandPos = [];
const V = (i, y, k = 1) => { const a = i * 2 * Math.PI / SEG, r = rAt(y) * k; return [r * Math.cos(a), y, r * Math.sin(a)]; };
const quad = (arr, a, b, c, d) => { arr.push(...a, ...b, ...c, ...a, ...c, ...d); };

for (let L = 0; L < LEV; L++) {
  const y0 = TOP * L / LEV, y1 = TOP * (L + 1) / LEV;
  for (let i = 0; i < SEG; i++) {
    const j = (i + 1) % SEG;
    // six spiralling light wells: stripe advances one sector per level
    const dark = ((i + L) % 4) === 0;
    quad(dark ? darkPos : glassPos, V(i, y0), V(j, y0), V(j, y1), V(i, y1));
  }
  // thin diagrid ring, slightly proud
  if (L % 2 === 1 && L < LEV - 3) for (let i = 0; i < SEG; i++) {
    const j = (i + 1) % SEG, yb = y1 - 0.7;
    quad(bandPos, V(i, yb, 1.015), V(j, yb, 1.015), V(j, y1, 1.015), V(i, y1, 1.015));
  }
}
const mk = (arr, mat) => {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(arr, 3));
  return new THREE.Mesh(geo, mat);
};
g.add(mk(glassPos, m(P.greenGlass)));
g.add(mk(darkPos, m(P.darkGlass)));
g.add(mk(bandPos, m(P.alu)));

// --- the glass lens / dome cap ------------------------------------------------------
g.add(dome(3.6, m(P.paleGlass), 0, 179.4, 0, 12, 0.9));

// --- low granite plaza and entrance canopy ------------------------------------------
g.add(cyl(34, 34, 1.2, m(P.darkConcrete), 0, 0, 0, 24));
g.add(cyl(25.5, 25.5, 7.5, m(P.paleGlass), 0, 1.2, 0, 24));

await exportGLB(g, out('gherkin'));
