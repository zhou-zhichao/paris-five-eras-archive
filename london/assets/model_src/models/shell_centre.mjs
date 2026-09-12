// Shell Centre, York Road / South Bank (1961, Sir Howard Robertson) - 107 m
// Portland stone clad tower with a clock stage and stepped crown, surrounded by
// long 10-storey stone wings around a courtyard.
// Convention: metres, ground y=0, footprint centred on origin, long axis x,
//             front (river) +z.
import { THREE, group, m, P, box, cyl, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const S = m(P.stone), G = m(P.glass), DC = m(P.darkConcrete);
const W = 34, D = 30, H = 96;

// --- the tower: stone piers with recessed windows --------------------------------
g.add(box(W, H, D, S, 0, 0, 0));
for (let y = 4; y < H - 2; y += 3.4) {
  g.add(box(W - 3.2, 2.1, D + 0.5, G, 0, y, 0));
  g.add(box(W + 0.5, 2.1, D - 3.2, G, 0, y, 0));
}
// stepped crown with the clock stage
g.add(box(W + 2.2, 2.5, D + 2.2, S, 0, H, 0));            // cornice
g.add(box(W * 0.72, 8, D * 0.72, S, 0, H + 2.5, 0));      // clock stage
for (const [dx, dz] of [[W * 0.36, 0], [-W * 0.36, 0], [0, D * 0.36], [0, -D * 0.36]])
  g.add(cyl(3.0, 3.0, 0.6, m(P.gold), dx, H + 6.5, dz, 12).rotateX(dz ? Math.PI / 2 : 0).rotateZ(dx ? Math.PI / 2 : 0));
g.add(box(W * 0.5, 3, D * 0.5, S, 0, H + 10.5, 0));
g.add(cyl(0.4, 0.6, 6, m(P.alu), 0, H + 13.5, 0, 6));     // flagstaff -> ~107 m

// --- the low wings around the courtyard -------------------------------------------
const wing = (x, z, w, d) => {
  g.add(box(w, 40, d, S, x, 0, z));
  for (let y = 4; y < 40; y += 3.4) { g.add(box(w - 3, 2.0, d + 0.4, G, x, y, z)); g.add(box(w + 0.4, 2.0, d - 3, G, x, y, z)); }
  g.add(box(w + 1.6, 1.8, d + 1.6, S, x, 40, z));
};
wing(0, 78, 190, 30);          // riverside (upstream) wing
wing(0, -78, 190, 30);
wing(-105, 0, 30, 130);
wing(105, 0, 30, 130);
g.add(box(230, 1.0, 200, DC, 0, 0, 0));

await exportGLB(g, out('shell_centre'));
