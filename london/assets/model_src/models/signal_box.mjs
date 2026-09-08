// Generic 1900s London railway signal box, 10 x 4 x 6 m.
// Brick locking-room below, glazed timber operating floor above, hipped slate roof,
// external stair.  Long axis along x, the glazed front facing +z (towards the tracks).
import { exportGLB, box, cyl, hipRoof, THREE, P, M, chimney, OUT,
  centreXZ } from './_lib_rail.mjs';

const g = new THREE.Group();
const W = 10, D = 4, BASE = 2.3, UPPER = 2.2;

const bk = M(P.red), st = M(P.dstone), tim = M(0x5e6f5e), gl = M(P.darkglass), sl = M(P.slate), ir = M(P.iron);

// brick locking room
g.add(box(W, BASE, D, bk, 0, 0, 0));
g.add(box(W + 0.5, 0.35, D + 0.5, st, 0, BASE, 0));           // string course
for (let i = 0; i < 5; i++) g.add(box(1.0, 1.0, 0.3, gl, -3.6 + i * 1.8, 1.0, D / 2));

// glazed operating floor, slightly oversailing
g.add(box(W + 0.7, UPPER, D + 0.7, tim, 0, BASE + 0.35, 0));
g.add(box(W + 0.8, UPPER - 0.9, 0.3, gl, 0, BASE + 0.75, (D + 0.7) / 2));   // front glazing
g.add(box(W + 0.8, UPPER - 0.9, 0.3, gl, 0, BASE + 0.75, -(D + 0.7) / 2));
for (const sx of [-1, 1]) g.add(box(0.3, UPPER - 0.9, D + 0.7, gl, sx * (W + 0.7) / 2, BASE + 0.75, 0));
// glazing bars
for (let i = 0; i < 19; i++) g.add(box(0.13, UPPER - 0.9, D + 0.9, tim, -5.0 + i * 0.55, BASE + 0.75, 0));
for (const sz of [-1, 1]) for (let i = 0; i < 7; i++)
  g.add(box(W + 0.9, 0.12, 0.14, tim, 0, BASE + 0.75 + (UPPER - 0.9) * (i + 1) / 8, sz * (D + 0.7) / 2));
for (const sx of [-1, 1]) for (let i = 0; i < 5; i++)
  g.add(box(0.14, 0.12, D + 0.7, tim, sx * (W + 0.7) / 2, BASE + 0.75 + (UPPER - 0.9) * (i + 1) / 6, 0));

// hipped slate roof with deep eaves
const EY = BASE + 0.35 + UPPER;
g.add(box(W + 1.6, 0.25, D + 1.6, tim, 0, EY, 0));
g.add(hipRoof(W + 1.6, D + 1.6, 1.0, sl, 0, EY + 0.25, 0, 0.45));
g.add(chimney(0.85, 0.85, 0.9, P.red, -W / 2 + 1.2, EY - 0.85, 0, 1));
// nameboard on the front, roof finial and a lamp bracket
g.add(box(5.0, 0.7, 0.25, M(0x2e4636), 0, EY - 1.2, (D + 0.7) / 2 + 0.3));
g.add(box(5.4, 0.15, 0.35, tim, 0, EY - 1.35, (D + 0.7) / 2 + 0.3));

g.add(box(0.14, 0.14, 1.4, ir, W / 2 + 0.3, BASE + 2.4, (D + 0.7) / 2));
g.add(box(0.5, 0.6, 0.5, M(0xe8e4d8), W / 2 + 0.3, BASE + 2.1, (D + 0.7) / 2 + 0.6));
// brick plinth courses and a locking-room door
for (let i = 0; i < 3; i++) g.add(box(W + 0.4 - i * 0.12, 0.3, D + 0.4 - i * 0.12, M(0x8a4436), 0, i * 0.3, 0));
g.add(box(1.1, 1.9, 0.3, M(P.dark), W / 2 - 1.4, 0.9, D / 2));

// external stair on the -x end, rising towards -x
for (let i = 0; i < 12; i++) g.add(box(0.55, 0.15, 1.2, ir, -W / 2 - 4.2 + i * 0.55, 0.215 * i, D / 2 + 0.4));
g.add(box(1.4, 0.24, 2.0, ir, -W / 2 - 0.7, BASE + 0.35, D / 2 + 0.4));
for (const sz of [-1, 1])
  g.add(box(6.0, 1.1, 0.14, ir, -W / 2 - 2.4, BASE * 0.55, D / 2 + 0.4 + sz * 0.6));

await exportGLB(centreXZ(g), OUT + 'signal_box.glb');
