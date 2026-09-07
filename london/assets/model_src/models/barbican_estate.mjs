// Barbican Estate, City of London (1965-76, Chamberlin Powell & Bon) - ~480 x 320 m
// of board-marked concrete: three 123 m triangular-plan towers with serrated
// balconies, long 7-storey terrace blocks on a raised podium around the lake,
// and the Barbican Centre at the south.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, exportGLB, out, poly, regular } from '../london_lib.mjs';

const g = new THREE.Group();
const C = m(P.concrete), DC = m(P.darkConcrete);
const PD = 6;                                   // podium deck level

// --- raised podium deck, lake and gardens ----------------------------------------
g.add(box(480, PD, 320, C, 0, 0, 0));
g.add(box(150, 0.8, 50, m(P.glass), 15, PD - 0.4, -35));       // the lake
g.add(box(110, 0.4, 44, m(P.pitch), -150, PD, -80));           // gardens

// --- three triangular towers, 123 m, 42 storeys ----------------------------------
// Lauderdale (west), Cromwell (north), Shakespeare (east)
const TOW = [[-140, 20, 0.0], [-20, 110, 0.9], [140, 55, 0.5]];
for (const [tx, tz, rot] of TOW) {
  g.add(poly(regular(3, 15, rot, tx, tz), 123, C, 0, PD, 0));
  // rounded corner "petals" carrying the balconies
  for (let k = 0; k < 3; k++) {
    const a = rot + k * 2 * Math.PI / 3 + Math.PI / 3;
    g.add(cyl(5.5, 5.5, 123, C, tx + 13 * Math.cos(a), PD, tz + 13 * Math.sin(a), 8));
  }
  // serrated balcony bands, one per floor
  for (let i = 0; i < 38; i++)
    g.add(poly(regular(3, 18.5, rot, tx, tz), 1.1, DC, 0, PD + 8 + i * 3.0, 0));
  g.add(poly(regular(3, 12, rot, tx, tz), 8, DC, 0, PD + 123, 0));   // roof plant crown
}

// --- long 7-storey terrace blocks (21 m) with balcony banding --------------------
// [cx, cz, length along x, depth in z]  (rotated ones are given already swapped)
const TER = [[-20, 145, 400, 18], [-140, -140, 170, 18], [110, -145, 200, 18],
             [-222, 5, 18, 200], [222, -20, 18, 230], [30, 78, 250, 16], [-70, -18, 140, 16]];
for (const [x, z, w, d] of TER) {
  g.add(box(w, 21, d, C, x, PD, z));
  for (let i = 0; i < 7; i++) g.add(box(w + 1.8, 1.1, d + 1.8, DC, x, PD + 1.4 + i * 2.9, z));
  g.add(box(w - 4, 3.2, d - 3, C, x, PD + 21, z));             // set-back penthouse
}

// --- Barbican Centre / Guildhall School (low concrete masses, south side) --------
g.add(box(180, 24, 80, C, 10, 0, -145));
g.add(box(120, 12, 56, DC, 10, 24, -145));
g.add(box(52, 36, 44, C, -110, 0, -150));                      // theatre fly tower
g.add(box(80, 12, 40, m(P.paleGlass), -190, PD, -25));         // conservatory glasshouse

// --- St Giles Cripplegate church, marooned in the middle -------------------------
g.add(box(32, 13, 13, m(P.brick), 60, PD, -5));
g.add(box(10, 25, 10, m(P.brick), 46, PD, -5));

await exportGLB(g, out('barbican_estate'));
