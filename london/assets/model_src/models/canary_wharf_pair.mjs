// Canary Wharf, the towers around One Canada Square (1991-2003).
// ORIGIN = the One Canada Square site, deliberately left EMPTY so the separate
// one_canada_square.glb drops straight into the gap.
// Local axes: +x = ENE along the estate spine (Canada Square -> Churchill Place),
// +z = north (towards North Dock).  Offsets used (metres from One Canada Square):
//   8 Canada Square  (HSBC, 200 m, 45x45)      x=-105  z=  +6
//   25 Canada Square (Citigroup, 200 m, 45x45) x=+105  z=  +8
//   10 Upper Bank St (151 m, 47x40)            x=+152  z=-152
//   40 Bank St       (153 m, 44x38)            x=-128  z=-146
//   1 Churchill Place(156 m, 46x40)            x=+218  z= -58
// Convention: metres, ground y=0, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out, banded } from '../london_lib.mjs';

const g = new THREE.Group();

// --- the two 200 m flanking towers ------------------------------------------------
for (const [x, z, name] of [[-105, 6, 'hsbc'], [105, 8, 'citi']]) {
  g.add(banded(45, 186, 45, P.darkGlass, P.alu, x, 0, z, 4.0, 0.45));
  // corner mullion piers
  for (const sx of [-1, 1]) for (const sz of [-1, 1])
    g.add(box(4, 186, 4, m(P.steel), x + sx * 20.5, 0, z + sz * 20.5));
  // set-back plant crown
  g.add(box(40, 10, 40, m(P.alu), x, 186, z));
  g.add(box(30, 4, 30, m(P.black), x, 196, z));
  g.add(box(56, 11, 52, m(P.stone), x, 0, z));                 // podium
}

// --- the 150 m second-rank towers, simpler banded boxes ---------------------------
for (const [x, z, w, d, h] of [[152, -152, 47, 40, 151], [-128, -146, 44, 38, 153], [218, -58, 46, 40, 156]]) {
  g.add(banded(w, h, d, P.glass, P.alu, x, 0, z, 4.0, 0.45));
  g.add(box(w * 0.8, 7, d * 0.8, m(P.black), x, h, z));
  g.add(box(w + 14, 9, d + 14, m(P.stone), x, 0, z));
}

// --- the dock water and the estate deck between them -----------------------------
g.add(box(150, 0.6, 62, m(P.glass), 20, 0, 118));              // North Dock
g.add(box(170, 0.6, 58, m(P.glass), 30, 0, -240));             // South Dock
g.add(box(70, 6, 46, m(P.paleGlass), 0, 0, 92));               // Canada Square gardens / station
g.add(box(380, 1.2, 210, m(P.darkConcrete), 55, 0, -55));      // estate deck

await exportGLB(g, out('canary_wharf_pair'));
