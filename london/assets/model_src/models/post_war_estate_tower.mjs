// Generic post-war point block - 22 storeys, 24 x 24 m on plan, 66 m tall.
// Precast concrete panels, one balcony per flat on each face, roof tank room.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const C = m(P.concrete), DC = m(P.darkConcrete), G = m(P.glass);
const W = 24, H = 66, FH = 3.0;

g.add(box(W, H, W, C, 0, 0, 0));
for (let i = 0; i < 22; i++) {
  const y = i * FH;
  g.add(box(W - 5, 2.0, W + 0.8, G, 0, y + 0.5, 0));
  g.add(box(W + 0.8, 2.0, W - 5, G, 0, y + 0.5, 0));
  g.add(box(W + 1.6, 0.8, W + 1.6, DC, 0, y + 2.5, 0));     // floor slab edge
}
// the four corner piers and the central service core expressed above the roof
for (const sx of [-1, 1]) for (const sz of [-1, 1])
  g.add(box(5, H, 5, C, sx * (W / 2 - 2), 0, sz * (W / 2 - 2)));
g.add(box(W + 2, 1.4, W + 2, DC, 0, H, 0));
g.add(box(11, 4, 11, C, 0, H + 1.4, 0));                    // lift motor / tank room
g.add(box(1.8, 3, 1.8, DC, 5, H + 5.4, 3));                 // flue
g.add(box(W + 18, 0.8, W + 18, DC, 0, 0, 0));

await exportGLB(g, out('post_war_estate_tower'));
