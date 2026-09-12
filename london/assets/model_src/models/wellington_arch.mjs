// Wellington Arch (Constitution Arch), Decimus Burton 1826-30; Quadriga added 1912.
// Portland stone, single opening, ~25 m to the top of the bronze Quadriga.
// Orientation: long axis along X, principal face towards +Z.
import { exportGLB, box, cyl, cone, THREE, P, M, column, openWall, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), dark = M(0x413c34), bronze = M(0x4a4034);
const W = 20.0, D = 12.0, H = 14.0;

for (let i = 0; i < 2; i++) g.add(box(W + 4 - i * 2, 0.6, D + 4 - i * 2, dk, 0, i * 0.6, 0));
// pierced block with one big arch
const ops = [{ cx: 0, y0: 0, w: 8.2, h: 6.2, arch: true }];
for (const zz of [D / 2 - 1.2, -D / 2 + 1.2]) g.add(openWall(W, H, 2.4, st, ops, 0, 1.2, zz, 14));
for (const sx of [-1, 1]) g.add(box(5.4, H, D, st, sx * (W / 2 - 2.7), 1.2, 0));
g.add(box(9.0, 3.2, D - 4.8, dark, 0, 9.4, 0));
// coupled Corinthian columns on each face, flanking the arch
for (const zs of [1, -1]) for (const x of [-7.4, -5.6, 5.6, 7.4])
  g.add(column(0.68, 10.2, pale, x, 1.2, zs * (D / 2 + 0.6), 10));
// entablature + tall attic
g.add(box(W + 2.4, 1.8, D + 3.2, pale, 0, 15.2, 0));
g.add(box(W - 1.0, 4.4, D - 1.0, st, 0, 17.0, 0));
g.add(box(W + 0.4, 1.0, D + 0.4, pale, 0, 21.4, 0));
for (const zs of [1, -1]) g.add(box(10.0, 2.6, 0.4, dk, 0, 17.8, zs * (D / 2 - 0.3)));
// the Quadriga: chariot, four horses, winged Victory  (bronze, ~25 m overall)
g.add(box(11.0, 0.6, 6.0, pale, 0, 22.4, 0));
for (let i = 0; i < 4; i++) {
  const x = -3.6 + i * 2.4;
  g.add(box(1.0, 1.7, 3.0, bronze, x, 23.0, 0.4));      // horse body
  g.add(box(0.7, 1.2, 0.8, bronze, x, 24.3, 2.1));      // neck / head
}
g.add(box(2.4, 1.8, 2.6, bronze, 4.4, 23.0, 0));        // chariot
g.add(box(0.8, 2.6, 0.8, bronze, 4.4, 24.8, 0));        // Victory
g.add(box(3.4, 1.6, 0.4, bronze, 4.4, 25.4, 0));        // wings

await exportGLB(g, OUT + 'wellington_arch.glb');
