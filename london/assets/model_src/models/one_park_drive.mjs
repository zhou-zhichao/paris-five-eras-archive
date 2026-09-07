// One Park Drive, Wood Wharf (2020, Herzog & de Meuron) - 205 m, 58 storeys.
// A cylindrical drum ~33 m across, divided into three stacked zones ("loggia",
// "cluster", "bay") with different balcony rhythms - so: stacked rings.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, lathe, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const R = 16.5, H = 205;
const GL = m(P.paleGlass), BAL = m(P.steel), CN = m(P.concrete);

// --- core drum ---------------------------------------------------------------------
g.add(cyl(R - 0.4, R - 0.4, H, GL, 0, 0, 0, 28));

// --- zone 1 "loggia" 0-72 m: deep-set floors, recessed band every storey ----------
for (let y = 3; y < 72; y += 3.3) {
  g.add(cyl(R + 0.9, R + 0.9, 0.9, CN, 0, y, 0, 28));
  g.add(cyl(R + 0.5, R + 0.5, 2.4, m(P.darkGlass), 0, y + 0.9, 0, 28));
}
// --- zone 2 "cluster" 72-150 m: projecting square balcony clusters ----------------
for (let y = 73; y < 150; y += 3.3) {
  g.add(cyl(R + 1.5, R + 1.5, 1.0, BAL, 0, y, 0, 28));
  g.add(cyl(R + 0.4, R + 0.4, 2.3, GL, 0, y + 1.0, 0, 28));
}
// --- zone 3 "bay" 150-205 m: shallower, flush bands ------------------------------
for (let y = 151; y < H - 2; y += 3.3) {
  g.add(cyl(R + 0.7, R + 0.7, 0.8, BAL, 0, y, 0, 28));
}
// zone joints, expressed as deeper collars
for (const y of [72, 150]) g.add(cyl(R + 2.6, R + 2.6, 2.2, CN, 0, y, 0, 28));

// --- crown: a shallow lantern -----------------------------------------------------
g.add(lathe([[R, 0], [R * 0.92, 3], [R * 0.7, 5.5], [0, 6.5]], m(P.alu), 0, H, 0, 28));

// --- podium: the drum meets the quayside on a low plinth --------------------------
g.add(cyl(R + 6, R + 7, 9, GL, 0, 0, 0, 28));
g.add(box(58, 1.0, 52, m(P.darkConcrete), 0, 0, 0));

await exportGLB(g, out('one_park_drive'));
