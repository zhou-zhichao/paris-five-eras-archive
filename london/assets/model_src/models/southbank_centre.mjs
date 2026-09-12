// South Bank Centre, one model ~520 x 150 m strung along the river (+z):
// Royal Festival Hall (1951) at -x, Queen Elizabeth Hall / Purcell Room and the
// Hayward Gallery (1967-68) in the middle, National Theatre (1976) at +x.
// Board-marked concrete terraces, walkways and fly towers.
// Convention: metres, ground y=0, footprint centred on origin, long axis x,
//             front (river) +z.
import { THREE, group, m, P, box, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const C = m(P.concrete), DC = m(P.darkConcrete), G = m(P.paleGlass), ST = m(P.stone);

// --- Royal Festival Hall: glazed river front, big solid auditorium box on top ----
g.add(box(120, 14, 78, G, -180, 0, 0));                       // glazed foyer podium
for (let y = 3.5; y < 14; y += 3.6) g.add(box(121, 1.0, 79, ST, -180, y, 0));
g.add(box(86, 20, 50, ST, -180, 14, -6));                     // the auditorium shell
g.add(box(90, 2.2, 54, DC, -180, 34, -6));                    // oversailing roof
g.add(box(28, 10, 26, C, -180, 36, -14));                     // fly tower / plant

// --- Queen Elizabeth Hall + Purcell Room: raw concrete, stepped -----------------
g.add(box(88, 12, 60, C, -60, 0, 4));
g.add(box(60, 9, 40, C, -66, 12, 0));
g.add(box(26, 7, 22, DC, -44, 21, -4));                       // fly tower
g.add(box(94, 1.4, 66, DC, -60, 12, 4));                      // terrace slab

// --- Hayward Gallery: pyramidal rooflights over a concrete box ------------------
g.add(box(66, 17, 56, C, 34, 0, -6));
g.add(box(70, 1.6, 60, DC, 34, 17, -6));
for (let i = 0; i < 3; i++) for (let k = 0; k < 2; k++) {
  const x = 12 + i * 22, z = -18 + k * 24;
  g.add(box(15, 5, 15, C, x, 18.6, z));
  g.add(box(11, 3, 11, G, x, 23.6, z));
}

// --- National Theatre: stacked concrete terraces and the square fly towers ------
g.add(box(120, 11, 82, C, 180, 0, 0));
g.add(box(112, 8, 70, C, 180, 11, -2));
g.add(box(96, 8, 58, C, 180, 19, -4));
for (let i = 0; i < 4; i++) g.add(box(126 - i * 4, 1.6, 88 - i * 6, DC, 180, 5.5 + i * 7.5, 0));   // terrace edges
g.add(box(26, 22, 24, C, 152, 27, -6));                       // Olivier fly tower
g.add(box(22, 18, 20, C, 196, 27, -8));                       // Lyttelton fly tower
g.add(box(16, 12, 15, DC, 218, 27, 2));

// --- the raised walkway spine and the riverside terrace -------------------------
g.add(box(430, 1.6, 9, DC, 0, 8, 30));
for (let x = -190; x <= 200; x += 30) g.add(box(3, 8, 3, C, x, 0, 30));
g.add(box(520, 1.0, 150, DC, 0, 0, 0));

await exportGLB(g, out('southbank_centre'));
