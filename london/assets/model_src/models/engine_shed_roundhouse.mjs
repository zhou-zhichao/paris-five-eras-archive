// Engine shed of the Camden Roundhouse type (Robert Dockray / Branson & Gwyther, 1847).
// 50 m diameter brick drum, ring of round-headed windows, conical slate roof rising to
// ~18 m with a central smoke lantern; turntable inside, entrance bay and track on -x.
import { exportGLB, box, cyl, cone, lathe, THREE, P, M, tracksX, OUT,
  centreXZ } from './_lib_rail.mjs';

const g = new THREE.Group();
const R = 25, WALL = 9.0, ROOF = 8.0, SEG = 24;
const bk = M(P.stock), bkd = M(0xa08e6f), st = M(P.dstone), sl = M(P.slate),
  gl = M(P.darkglass), ir = M(P.iron), gr = M(P.ballast);

// ---- brick drum with a plinth, buttress piers and a ring of round-headed windows
g.add(cyl(R + 0.6, R + 1.0, 1.2, bkd, 0, 0, 0, SEG));
g.add(cyl(R, R + 0.4, WALL, bk, 0, 1.2, 0, SEG));
for (let i = 0; i < SEG; i++) {
  const a = i * 2 * Math.PI / SEG;
  const cx = Math.cos(a) * (R - 0.1), cz = Math.sin(a) * (R - 0.1);
  // pier
  const p = box(1.8, WALL + 1.4, 1.4, bkd, cx, 1.2, cz);
  p.rotation.y = -a; g.add(p);
  // window between the piers
  const a2 = a + Math.PI / SEG;
  const wx = Math.cos(a2) * (R - 0.2), wz = Math.sin(a2) * (R - 0.2);
  const w = box(2.6, 4.2, 0.8, gl, wx, 5.4, wz);
  w.rotation.y = -a2; g.add(w);
  const w2 = box(3.4, 0.5, 1.0, st, wx, 4.7, wz);
  w2.rotation.y = -a2; g.add(w2);
}
// eaves cornice
g.add(cyl(R + 1.6, R + 1.6, 1.0, st, 0, WALL + 1.2, 0, SEG));

// ---- conical slate roof + louvred smoke lantern
const EAVES = WALL + 2.2, RR = R + 1.8;
g.add(cone(RR, ROOF, sl, 0, EAVES, 0, SEG));
const LY = EAVES + ROOF * (1 - 4.6 / RR);            // where the cone is 4.6 m in radius
g.add(cyl(4.6, 4.8, 1.8, M(0x5b6068), 0, LY - 0.4, 0, 16));
for (let i = 0; i < 16; i++) {
  const a = i * 2 * Math.PI / 16;
  const b = box(0.5, 1.4, 1.5, ir, Math.cos(a) * 4.7, LY - 0.1, Math.sin(a) * 4.7);
  b.rotation.y = -a; g.add(b);
}
g.add(cone(5.2, 2.0, sl, 0, LY + 1.4, 0, 16));
g.add(cyl(0.35, 0.45, 1.2, ir, 0, LY + 3.4, 0, 8));
// lead ribs following the slope of the cone
const slope = Math.atan2(ROOF, RR), L = Math.hypot(RR, ROOF) - 5.6;
for (let i = 0; i < SEG; i++) {
  const a = i * 2 * Math.PI / SEG + Math.PI / SEG;
  const arm = new THREE.Group();
  const rib = new THREE.Group();
  rib.add(box(L, 0.28, 0.5, M(P.lead), L / 2, -0.14, 0));   // runs along +x from the local origin
  rib.rotation.z = Math.PI - slope;                          // tip it up the slope, inwards
  rib.position.set(RR - 0.1, EAVES + 0.1, 0);
  arm.add(rib);
  arm.rotation.y = -a;
  g.add(arm);
}

// ---- entrance bay on -x with the approach track, and the turntable pit
g.add(box(9.0, 8.0, 12.0, bk, -R - 2.5, 0, 0));
g.add(box(10.0, 1.0, 13.0, st, -R - 2.5, 8.0, 0));
g.add(box(1.0, 6.4, 7.0, M(P.dark), -R - 6.9, 0, 0));    // dark opening
g.add(tracksX(30, 4.4, 1, -R - 12, 0.05, 0));
// turntable
g.add(cyl(9.5, 9.5, 0.5, gr, 0, 0.1, 0, 20));
g.add(box(19.0, 0.9, 2.2, ir, 0, 0.6, 0));

await exportGLB(centreXZ(g), OUT + 'engine_shed_roundhouse.glb');
