// Generic City office tower A - a 100 m Portland-stone clad slab, 25 storeys,
// punched windows, deep cornice, low retail podium. Fills out anonymous skyline.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const S = m(P.stone), DK = m(P.darkGlass), AL = m(P.alu);
const W = 44, D = 28, H = 100;

g.add(box(W, H, D, S, 0, 0, 0));
// punched window bands with stone piers between them
for (let y = 5; y < H - 3; y += 3.8) {
  g.add(box(W - 4, 2.3, D + 0.5, DK, 0, y, 0));
  g.add(box(W + 0.5, 2.3, D - 4, DK, 0, y, 0));
}
for (let i = 0; i <= 11; i++) g.add(box(1.8, H, D + 1.0, S, -W / 2 + i * W / 11, 0, 0));
// setback at the top plus the cornice and plant room
g.add(box(W + 2.4, 2.0, D + 2.4, S, 0, H - 12, 0));
g.add(box(W - 8, 12, D - 8, S, 0, H - 10, 0));
g.add(box(W - 5, 1.6, D - 5, AL, 0, H, 0));
g.add(box(W + 16, 10, D + 12, S, 0, 0, 0));

await exportGLB(g, out('office_tower_generic_a'));
