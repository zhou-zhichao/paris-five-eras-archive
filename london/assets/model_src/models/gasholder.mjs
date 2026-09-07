// Victorian gasholder (as at King's Cross, Bethnal Green, Battersea) - a 60 m
// diameter cast-iron guide frame, 40 m tall: 16 clustered columns tied by three
// tiers of latticed girders, with the telescopic bell part-raised inside.
// Convention: metres, ground y=0, centred on the origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, strut, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const IR = m(P.darkConcrete), RD = m(P.red), STL = m(P.alu), BR = m(P.brick);
const R = 30, H = 40, N = 16;

// --- the guide-frame columns --------------------------------------------------------
for (let i = 0; i < N; i++) {
  const a = i * 2 * Math.PI / N, c = Math.cos(a), s = Math.sin(a);
  g.add(cyl(1.0, 1.5, H, IR, R * c, 0, R * s, 8));
  g.add(cyl(2.2, 2.6, 3.0, BR, R * c, 0, R * s, 8));            // brick plinth
  g.add(cyl(1.7, 1.7, 1.4, IR, R * c, H, R * s, 8));            // capital
}
// --- three tiers of latticed ring girders between the columns ----------------------
for (const y of [12.5, 25.5, 38.5]) {
  for (let i = 0; i < N; i++) {
    const a0 = i * 2 * Math.PI / N, a1 = (i + 1) * 2 * Math.PI / N;
    const A = [R * Math.cos(a0), y, R * Math.sin(a0)], B = [R * Math.cos(a1), y, R * Math.sin(a1)];
    g.add(strut(A, B, 0.6, IR, 5));                             // bottom chord
    g.add(strut([A[0], y + 2.6, A[2]], [B[0], y + 2.6, B[2]], 0.6, IR, 5));   // top chord
    // the arched lattice web
    const M = [(A[0] + B[0]) / 2 * 0.995, y + 2.6, (A[2] + B[2]) / 2 * 0.995];
    g.add(strut(A, M, 0.35, IR, 4));
    g.add(strut(B, M, 0.35, IR, 4));
  }
}

// --- the telescopic bell, floating part-raised inside the frame --------------------
g.add(cyl(R - 2.5, R - 2.5, 17, RD, 0, 4, 0, 24));
g.add(cyl(R - 2.0, R - 2.0, 1.2, IR, 0, 20.4, 0, 24));          // lift cup
g.add(cyl(R - 4.5, R - 4.5, 9, RD, 0, 21.6, 0, 24));
g.add(cyl(R - 4.0, R - 4.0, 1.0, IR, 0, 30.2, 0, 24));
g.add(cyl(R - 5.5, R - 5.5, 0.8, STL, 0, 31.2, 0, 24));         // crown plate

// --- the water tank kerb and the yard ------------------------------------------------
g.add(cyl(R + 3.5, R + 4.5, 4, BR, 0, 0, 0, 32));
g.add(cyl(R + 1.5, R + 1.5, 3.4, m(P.glass), 0, 0.3, 0, 32));   // the water in the tank
g.add(box(2 * R + 26, 0.8, 2 * R + 26, m(P.darkConcrete), 0, 0, 0));

await exportGLB(g, out('gasholder'));
