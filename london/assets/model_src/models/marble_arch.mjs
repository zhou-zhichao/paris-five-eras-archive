// Marble Arch, John Nash 1827 (moved to Cumberland Gate 1851).  Carrara marble.
// Triumphal arch of three openings, ~18.5 m wide, 9 m deep, ~16 m high.
// Orientation: long axis along X, principal face towards +Z.
import { exportGLB, box, cyl, cone, THREE, P, M, column, openWall, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const mar = M(0xe7e2d6), pale = M(P.pale), dk = M(P.dstone), dark = M(0x413c34), bronze = M(P.bronze);
const W = 18.5, D = 9.0, H = 11.0;

g.add(box(W + 2, 0.7, D + 2, dk, 0, 0, 0));
// the pierced block: one 5.2 m central arch + two 2.6 m side arches
const ops = [
  { cx: 0, y0: 0, w: 5.2, h: 4.6, arch: true },
  { cx: -6.1, y0: 0, w: 2.6, h: 3.4, arch: true },
  { cx: 6.1, y0: 0, w: 2.6, h: 3.4, arch: true },
];
for (const zz of [D / 2 - 0.9, -D / 2 + 0.9]) g.add(openWall(W, H, 1.8, mar, ops, 0, 0.7, zz, 12));
for (const sx of [-1, 1]) g.add(box(2.0, H, D, mar, sx * (W / 2 - 1.0), 0.7, 0));
for (const sx of [-1, 1]) g.add(box(3.6, H, D - 3.6, mar, sx * 3.8, 0.7, 0));
g.add(box(W - 6, 3.0, D - 3.6, dark, 0, 6.2, 0));           // shadow in the vaults
// engaged Corinthian columns on both faces
for (const zs of [1, -1]) for (const x of [-8.0, -4.0, 4.0, 8.0])
  g.add(column(0.62, 8.2, mar, x, 0.7, zs * (D / 2 + 0.4), 10));
// entablature + attic
g.add(box(W + 1.6, 1.5, D + 2.4, pale, 0, 11.7, 0));
g.add(box(W, 2.4, D, mar, 0, 13.2, 0));
g.add(box(W + 0.8, 0.8, D + 0.8, pale, 0, 15.6, 0));
// panels & spandrel reliefs
for (const zs of [1, -1]) {
  g.add(box(6.0, 1.6, 0.4, bronze, 0, 13.6, zs * (D / 2 + 0.2)));
  g.add(box(2.6, 1.8, 0.4, bronze, -6.1, 9.0, zs * (D / 2 + 0.2)));
  g.add(box(2.6, 1.8, 0.4, bronze, 6.1, 9.0, zs * (D / 2 + 0.2)));
}

await exportGLB(g, OUT + 'marble_arch.glb');
