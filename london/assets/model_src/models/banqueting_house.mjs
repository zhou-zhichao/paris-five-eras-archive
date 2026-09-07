// The Banqueting House, Whitehall - Inigo Jones, 1619-22, England's first fully
// classical building; refaced in Portland stone.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x.  "Front" = +z is the main (Whitehall) facade.
//
// True dimensions: 34 x 21 m on plan, ~22 m to the top of the balustrade; a
// rusticated basement, an Ionic lower order and a Composite upper order of seven
// bays, the centre three bays carried on engaged columns.
import {
  exportGLB, out, M, mat, box, cyl, cone, dome, gableRoof, hipRoof, group, THREE,
  crenel, colonnade,
} from './_lib_london.mjs';

const g = new THREE.Group();
const port = M.portland, pale = M.pale, dark = M.dark, lead = M.lead;
const W = 34, D = 21;
const BASE = 5.0, LOW = 7.2, UPP = 6.6;              // basement / Ionic / Composite storeys

// ---- rusticated basement
g.add(box(W, BASE, D, pale, 0, 0, 0));
for (let i = 0; i < 5; i++) g.add(box(W + 0.5, 0.25, D + 0.5, port, 0, 0.6 + i * 0.8, 0));
g.add(box(W + 1.0, 0.7, D + 1.0, port, 0, BASE - 0.7, 0));
for (let i = 0; i < 7; i++) for (const s of [-1, 1])
  g.add(box(1.9, 2.2, 0.4, dark, -W / 2 + (i + 0.5) * W / 7, 1.6, s * D / 2));
for (const s of [-1, 1]) for (let i = 0; i < 4; i++)
  g.add(box(0.4, 2.2, 1.9, dark, s * W / 2, 1.6, -D / 2 + (i + 0.5) * D / 4));

// ---- main block: two classical orders
g.add(box(W, LOW + UPP, D, port, 0, BASE, 0));
for (let i = 0; i < 7; i++) {
  const bx = -W / 2 + (i + 0.5) * W / 7;
  for (const s of [-1, 1]) {
    g.add(box(2.2, 4.2, 0.45, dark, bx, BASE + 1.4, s * D / 2));
    g.add(box(2.9, 0.4, 0.7, pale, bx, BASE + 5.8, s * D / 2));
    if (i % 2 === 0) g.add(box(2.9, 0.9, 0.7, pale, bx, BASE + 6.2, s * D / 2));
    g.add(box(2.2, 3.8, 0.45, dark, bx, BASE + LOW + 1.4, s * D / 2));
    g.add(box(2.9, 0.35, 0.6, pale, bx, BASE + LOW + 5.4, s * D / 2));
  }
}
for (const s of [-1, 1]) for (let i = 0; i < 4; i++) {
  const bz = -D / 2 + (i + 0.5) * D / 4;
  g.add(box(0.45, 4.2, 2.2, dark, s * W / 2, BASE + 1.4, bz));
  g.add(box(0.45, 3.8, 2.2, dark, s * W / 2, BASE + LOW + 1.4, bz));
}
// pilasters on the flanking bays, engaged columns on the centre three
for (let i = 0; i <= 7; i++) {
  const bx = -W / 2 + i * W / 7, mid = i >= 2 && i <= 5;
  for (const s of [-1, 1]) {
    if (mid) {
      g.add(cyl(0.62, 0.68, LOW - 1.0, port, bx, BASE + 0.4, s * (D / 2 + 0.5), 10));
      g.add(box(1.7, 0.45, 1.7, pale, bx, BASE + LOW - 0.6, s * (D / 2 + 0.5)));
      g.add(cyl(0.58, 0.64, UPP - 1.2, port, bx, BASE + LOW + 0.4, s * (D / 2 + 0.5), 10));
      g.add(box(1.6, 0.45, 1.6, pale, bx, BASE + LOW + UPP - 0.8, s * (D / 2 + 0.5)));
    } else {
      g.add(box(1.2, LOW - 1.0, 0.45, pale, bx, BASE + 0.4, s * (D / 2 + 0.15)));
      g.add(box(1.6, 0.45, 0.6, pale, bx, BASE + LOW - 0.6, s * (D / 2 + 0.15)));
      g.add(box(1.1, UPP - 1.2, 0.45, pale, bx, BASE + LOW + 0.4, s * (D / 2 + 0.15)));
      g.add(box(1.5, 0.45, 0.6, pale, bx, BASE + LOW + UPP - 0.8, s * (D / 2 + 0.15)));
    }
  }
}
for (const s of [-1, 1]) for (const bz of [-D / 2 + 0.6, -D / 6, D / 6, D / 2 - 0.6]) {
  g.add(box(0.45, LOW - 1.0, 1.2, pale, s * (W / 2 + 0.15), BASE + 0.4, bz));
  g.add(box(0.6, 0.45, 1.6, pale, s * (W / 2 + 0.15), BASE + LOW - 0.6, bz));
  g.add(box(0.45, UPP - 1.2, 1.1, pale, s * (W / 2 + 0.15), BASE + LOW + 0.4, bz));
}
// band course between the orders, carved frieze under the main cornice
g.add(box(W + 1.4, 0.9, D + 1.4, pale, 0, BASE + LOW - 0.15, 0));
g.add(box(W + 0.6, 0.8, D + 0.6, mat(0xcfc7b3), 0, BASE + LOW + UPP - 1.6, 0));

// ---- entablature, balustrade and low leaded roof
const TOP = BASE + LOW + UPP;
g.add(box(W + 2.4, 1.5, D + 2.4, port, 0, TOP, 0));
g.add(box(W + 2.0, 0.5, D + 2.0, pale, 0, TOP + 1.5, 0));
for (const s of [-1, 1]) {
  g.add(crenel(W + 2.0, 0.7, pale, 0, TOP + 2.0, s * (D / 2 + 0.65), true, 1.5, 0.5, 0.7));
  g.add(crenel(D + 2.0, 0.7, pale, s * (W / 2 + 0.65), TOP + 2.0, 0, false, 1.5, 0.5, 0.7));
}
g.add(box(W + 2.2, 0.4, D + 2.2, pale, 0, TOP + 3.5, 0));
g.add(hipRoof(W - 1, D - 1, 2.6, lead, 0, TOP + 1.5, 0, 0.75));
// entrance steps and door on the +z front
g.add(box(9.0, 1.2, 3.0, pale, 0, 0, D / 2 + 1.5));
g.add(box(3.0, 4.4, 0.5, dark, 0, 1.2, D / 2 + 0.1));

await exportGLB(g, out('banqueting_house'));
