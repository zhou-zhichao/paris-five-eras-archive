// Generic City office tower B - a 120 m dark-glass box, 30 storeys, flush curtain
// wall with a shallow setback and roof plant. Anonymous 1990s-2000s filler.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out, banded } from '../london_lib.mjs';

const g = new THREE.Group();
const W = 38, D = 34, H = 120;

g.add(banded(W, H, D, P.darkGlass, P.black, 0, 0, 0, 4.0, 0.35));
// slim aluminium mullions
for (let i = 0; i <= 9; i++) {
  const x = -W / 2 + i * W / 9;
  for (const sz of [-1, 1]) g.add(box(0.9, H, 0.9, m(P.alu), x, 0, sz * (D / 2 + 0.2)));
}
// setback crown and plant
g.add(box(W - 6, 8, D - 6, m(P.black), 0, H, 0));
g.add(box(W - 14, 4, D - 14, m(P.alu), 0, H + 8, 0));
g.add(box(W + 14, 9, D + 12, m(P.darkConcrete), 0, 0, 0));

await exportGLB(g, out('office_tower_generic_b'));
