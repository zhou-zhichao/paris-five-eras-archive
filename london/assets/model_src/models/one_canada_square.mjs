// One Canada Square, Canary Wharf (1991) - 235.1 m, 50 storeys, 55 m square plan.
// Cesar Pelli. Stainless-steel clad shaft with a 30 m pyramid roof + aircraft light.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, cone, exportGLB, out, banded } from '../london_lib.mjs';

const g = new THREE.Group();
const W = 55, SHAFT = 205, PYR = 30;      // 205 + 30 = 235 m

// shaft: stainless steel with horizontal spandrel banding
g.add(banded(W, SHAFT, W, P.glass, P.steel, 0, 0, 0, 4.1, 0.5));
// slight vertical piers at the corners to break the box up
for (const sx of [-1, 1]) for (const sz of [-1, 1])
  g.add(box(5, SHAFT, 5, m(P.steel), sx * (W / 2 - 1.5), 0, sz * (W / 2 - 1.5)));

// pyramid roof (square, so 4 segments, rotated 45 deg to align with the plan)
const p = cone(W / 2 * Math.SQRT2, PYR, m(P.steel), 0, SHAFT, 0, 4);
p.rotation.y = Math.PI / 4;
g.add(p);
// mast + aircraft warning light
g.add(cyl(0.4, 0.7, 6, m(P.steel), 0, SHAFT + PYR - 1, 0, 6));

// podium / lobby
g.add(box(78, 12, 70, m(P.stone), 0, 0, 0));
g.add(box(84, 1.0, 76, m(P.darkConcrete), 0, 0, 0));

await exportGLB(g, out('one_canada_square'));
