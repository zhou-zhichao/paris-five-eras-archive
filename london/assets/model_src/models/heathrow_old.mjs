// Heathrow central area, c.1955-70 - the Europa / Oceanic / Britannic terminal
// blocks (T1-T3) around the central apron, with the 1955 control tower.
// Low, flat-roofed, curtain-walled 1950s blocks with finger piers.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const S = m(P.stone), GL = m(P.glass), AL = m(P.alu), DC = m(P.darkConcrete);

// helper: a low curtain-walled terminal block with banded glazing
function term(x, z, w, d, h) {
  g.add(box(w, h, d, S, x, 0, z));
  for (let y = 3; y < h; y += 3.6) { g.add(box(w + 0.5, 2.0, d - 2.5, GL, x, y, z)); g.add(box(w - 2.5, 2.0, d + 0.5, GL, x, y, z)); }
  g.add(box(w + 2, 1.2, d + 2, AL, x, h, z));
}

// --- the three terminals round the central area ----------------------------------
term(-140, 40, 150, 46, 18);        // Terminal 2 / Europa Building (1955)
term(120, 55, 170, 44, 21);         // Terminal 3 / Oceanic (1961)
term(-10, -110, 190, 50, 16);       // Terminal 1 (1968)

// --- finger piers reaching out to the aircraft stands ----------------------------
for (const [x, z, len] of [[-190, -40, 90], [-90, -40, 90], [60, -30, 80], [190, -30, 80],
                           [-90, 100, 70], [90, 110, 70]]) {
  g.add(box(16, 9, len, S, x, 0, z));
  for (let y = 3; y < 9; y += 3.2) g.add(box(16.6, 2.0, len - 2, GL, x, y, z));
  g.add(box(18, 1.0, len + 2, AL, x, 9, z));
}

// --- the 1955 control tower -------------------------------------------------------
g.add(box(11, 30, 11, S, 20, 0, 0));
for (let y = 3; y < 30; y += 3.6) g.add(box(11.6, 2.0, 8, GL, 20, y, 0));
g.add(box(16, 5, 16, GL, 20, 30, 0));
g.add(box(17.5, 1.4, 17.5, DC, 20, 35, 0));
g.add(cyl(0.4, 0.6, 8, AL, 20, 36.4, 0, 6));

// --- multi-storey car park and apron ---------------------------------------------
g.add(box(90, 16, 60, DC, 150, 0, -70));
for (let y = 3; y < 16; y += 3.2) g.add(box(91, 1.2, 61, S, 150, y, -70));
g.add(box(560, 0.8, 340, DC, 0, 0, 0));

await exportGLB(g, out('heathrow_old'));
