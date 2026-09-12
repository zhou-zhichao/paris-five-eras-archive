// The Leadenhall Building, "the Cheesegrater" (2014) - 225 m, 48 storeys, RSHP.
// Wedge: one vertical face (-z, with the exposed service core) and a face raked back
// ~10 deg on +z; exposed yellow/steel megaframe bracing.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z
//             (the +z face is the raked glass slope).
import { THREE, group, m, P, box, cyl, strut, exportGLB, out, loft } from '../london_lib.mjs';

const g = new THREE.Group();
const W = 52, H = 225, D0 = 44, D1 = 5.5, Z0 = -22;      // -z face fixed at Z0

const rect = y => {
  const t = y / H, d = D0 + (D1 - D0) * t;
  return [[-W / 2, Z0], [W / 2, Z0], [W / 2, Z0 + d], [-W / 2, Z0 + d]];
};
// glazed wedge, in banded slices so the floor plates read
const N = 30;
for (let i = 0; i < N; i++) {
  const y0 = H * i / N, y1 = H * (i + 1) / N;
  g.add(loft([{ y: y0, pts: rect(y0) }, { y: y1 - 1.3, pts: rect(y1 - 1.3) }], m(P.glass)));
  const p = rect(y1).map(([x, z]) => [x * 1.01, z]);
  g.add(loft([{ y: y1 - 1.3, pts: p }, { y: y1, pts: p }], m(P.paleGlass), 0, 0, 0, false, false));
}

// --- exposed megaframe: 7-storey triangulated bracing on both end walls -----------
const NODE = 7, STEP = H / NODE;
const dAt = y => D0 + (D1 - D0) * (y / H);
for (const sx of [-1, 1]) {
  const X = sx * (W / 2 + 0.9);
  for (let i = 0; i < NODE; i++) {
    const ya = i * STEP, yb = (i + 1) * STEP;
    g.add(strut([X, ya, Z0], [X, yb, Z0 + dAt(yb)], 1.0, m(P.yellow), 5));
    g.add(strut([X, ya, Z0 + dAt(ya)], [X, yb, Z0], 1.0, m(P.yellow), 5));
    g.add(strut([X, yb, Z0], [X, yb, Z0 + dAt(yb)], 0.9, m(P.steel), 5));   // horizontal tie
  }
  // corner megacolumns
  g.add(strut([X, 0, Z0], [X, H, Z0], 1.5, m(P.steel), 6));
  g.add(strut([X, 0, Z0 + D0], [X, H, Z0 + D1], 1.5, m(P.steel), 6));
}
// bracing on the raked +z face
for (let i = 0; i < NODE; i++) {
  const ya = i * STEP, yb = (i + 1) * STEP;
  const zf = y => Z0 + dAt(y) + 0.8;
  g.add(strut([-W / 2, ya, zf(ya)], [W / 2, yb, zf(yb)], 0.9, m(P.yellow), 5));
  g.add(strut([W / 2, ya, zf(ya)], [-W / 2, yb, zf(yb)], 0.9, m(P.yellow), 5));
}

// --- north service core: separate exposed shaft on the -z side --------------------
g.add(box(W * 0.82, H, 10, m(P.alu), 0, 0, Z0 - 5.5));
for (let y = 6; y < H; y += 9) g.add(box(W * 0.85, 1.2, 11, m(P.steel), 0, y, Z0 - 5.5));
for (const sx of [-1, 1]) g.add(cyl(2.2, 2.2, H + 6, m(P.yellow), sx * W * 0.41, 0, Z0 - 10.5, 8));

// public plaza slab under the 7-storey undercroft
g.add(box(W + 10, 0.8, D0 + 10, m(P.darkConcrete), 0, 0, Z0 + D0 / 2 - 3));

await exportGLB(g, out('cheesegrater'));
