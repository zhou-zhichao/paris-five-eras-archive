// Trellick Tower, North Kensington (1972, Erno Goldfinger) - 98 m, 31 storeys.
// Board-marked concrete slab with the lift/service tower standing free of it and
// joined by bridges every third floor; boiler house cantilevered off the top.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const C = m(P.concrete), DC = m(P.darkConcrete), G = m(P.glass);
const W = 66, D = 12, H = 93;

// --- the residential slab, with recessed balcony bands ---------------------------
g.add(box(W, H, D, C, 0, 0, 0));
for (let y = 2.5; y < H; y += 2.9) {
  g.add(box(W - 2.5, 1.9, D + 0.9, G, 0, y, 0));            // glazing / balcony recess
  g.add(box(W + 0.8, 1.0, D + 1.6, DC, 0, y + 1.9, 0));     // balcony slab edge
}
// vertical concrete fins dividing the flats
for (let i = 0; i <= 11; i++) g.add(box(1.2, H, D + 2.2, C, -W / 2 + i * W / 11, 0, 0));

// --- the detached service tower on the -z side ------------------------------------
const TX = 6, TZ = -(D / 2 + 9), TH = 98;
g.add(box(11, TH, 9, C, TX, 0, TZ));
for (let y = 3; y < TH - 8; y += 8.7) g.add(box(11.6, 1.6, 3.0, DC, TX, y, TZ + 4.6));   // stair slot lights
// the cantilevered boiler house at the top
g.add(box(15, 9, 12, C, TX, TH, TZ));
g.add(box(15.8, 1.2, 12.8, DC, TX, TH + 9, TZ));

// --- access bridges every third floor ---------------------------------------------
for (let y = 8.7; y < H - 4; y += 8.7) g.add(box(3.4, 2.6, 9.5, C, TX, y, TZ + 5.5));

// ground: podium and the low maisonette wing
g.add(box(W + 14, 5, D + 10, C, 0, 0, 2));
g.add(box(40, 11, 13, C, W / 2 + 26, 0, 0));

await exportGLB(g, out('trellick_tower'));
