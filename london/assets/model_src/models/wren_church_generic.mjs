// A typical City-of-London Wren parish church (generic filler for the skyline):
// 35 x 18 m rectangular body with a parapet, and a square west tower carrying a
// small lead lantern and spirelet, ~45 m overall.  Portland stone / stock brick.
// Long axis along X, tower at the WEST end (-X), south side towards +Z.  Ground y=0.
import { exportGLB, box, cyl, cone, lathe, THREE, P, M,
  balustrade, churchBody, OUT } from './_lib_church.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), lead = M(P.lead), gold = M(P.gold), dark = M(0x4a463d);

const L = 35, W = 18, H = 13;
const X0 = -L / 2 + 5.5;
churchBody(g, X0, L, W, H, { bays: 4 });

// ---------------------------------------------------------------- west tower
const TX = X0 - 5.5;
const T = new THREE.Group();
T.add(box(10.0, 26, 10.0, st, 0, 1.0, 0));
T.add(box(0.6, 6.5, 3.6, dark, -5.1, 2.0, 0));                  // west door
for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
  T.add(box(dx ? 0.6 : 3.2, 6.0, dz ? 0.6 : 3.2, dark, dx * 5.1, 18.0, dz * 5.1));
T.add(box(11.2, 1.4, 11.2, pale, 0, 27.0, 0));
T.add(balustrade(11.2, 11.2, 1.8, pale, 0, 28.4, 0));
for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
  T.add(cyl(0.65, 0.85, 2.6, pale, dx * 4.7, 30.2, dz * 4.7, 8));
// octagonal lead lantern + spirelet
T.add(cyl(2.9, 3.2, 6.0, st, 0, 30.2, 0, 8));
for (let i = 0; i < 8; i++) {
  const a = (i + 0.5) / 8 * Math.PI * 2;
  T.add(box(1.3, 3.8, 0.6, dark, Math.cos(a) * 3.0, 31.2, Math.sin(a) * 3.0));
}
T.add(cyl(3.9, 3.9, 0.9, pale, 0, 36.2, 0, 8));
T.add(lathe([[2.9, 0], [2.6, 1.0], [1.9, 2.2], [1.1, 3.1]], lead, 0, 37.1, 0, 8));
T.add(cone(1.2, 3.6, lead, 0, 40.2, 0, 8));
T.add(cyl(0.2, 0.2, 1.4, gold, 0, 43.8, 0, 6));
T.position.set(TX, 0, 0);
g.add(T);

await exportGLB(g, OUT + 'wren_church_generic.glb');
