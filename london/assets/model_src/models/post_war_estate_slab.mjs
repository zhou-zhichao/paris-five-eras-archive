// Generic post-war LCC/GLC housing slab - 11 storeys, 80 x 14 m on plan, 33 m tall.
// Board-marked concrete frame with recessed access-deck / balcony bands and a
// projecting stair-lift core.
// Convention: metres, ground y=0, footprint centred on origin, long axis x,
//             front (balcony/access-deck side) +z.
import { THREE, group, m, P, box, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const C = m(P.concrete), DC = m(P.darkConcrete), G = m(P.glass);
const W = 80, D = 14, H = 33, FH = 3.0;

g.add(box(W, H, D, C, 0, 0, 0));
for (let i = 0; i < 11; i++) {
  const y = i * FH;
  g.add(box(W - 1.6, 2.1, D + 1.0, G, 0, y + 0.5, 0));       // glazing / open balcony
  g.add(box(W + 1.2, 0.9, D + 1.8, DC, 0, y + 2.6, 0));      // balcony slab edge
}
// vertical party-wall fins
for (let i = 0; i <= 10; i++) g.add(box(0.9, H, D + 2.2, C, -W / 2 + i * W / 10, 0, 0));
// projecting stair / lift core on the -z side
g.add(box(9, H + 2, 7, C, -14, 0, -(D / 2 + 3)));
g.add(box(9, H + 2, 7, C, 20, 0, -(D / 2 + 3)));
// roof parapet, tank room and the ground-floor undercroft
g.add(box(W + 1.6, 1.2, D + 1.6, DC, 0, H, 0));
g.add(box(14, 2.6, 9, C, 3, H + 1.2, 0));
g.add(box(W + 12, 0.8, D + 22, DC, 0, 0, 0));

await exportGLB(g, out('post_war_estate_slab'));
