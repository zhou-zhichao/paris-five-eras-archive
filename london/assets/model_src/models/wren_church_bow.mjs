// St Mary-le-Bow, Cheapside, Christopher Wren 1671-80 — steeple 68 m: square tower,
// a circular temple of Ionic columns, a stage of inverted consoles, then an obelisk
// spire carrying the copper dragon vane.
// Long axis along X, tower at the WEST end (-X), south side towards +Z.  Ground y=0.
import { exportGLB, box, cyl, cone, lathe, THREE, P, M,
  balustrade, churchBody, OUT } from './_lib_church.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), lead = M(P.lead), gold = M(P.gold),
  cop = M(P.copper), dark = M(0x4a463d);

const L = 30, W = 20, H = 14;
const X0 = -L / 2 + 6;
churchBody(g, X0, L, W, H, { bays: 4 });

// ---------------------------------------------------------------- steeple
const TX = X0 - 7.0;
const T = new THREE.Group();
T.add(box(12.5, 30, 12.5, st, 0, 1.0, 0));
// the rusticated west doorway and tall belfry openings
T.add(box(0.6, 8.0, 4.4, dark, -6.4, 3.0, 0));
for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
  T.add(box(dx ? 0.6 : 4.2, 8.0, dz ? 0.6 : 4.2, dark, dx * 6.4, 19.0, dz * 6.4));
T.add(box(13.8, 1.6, 13.8, pale, 0, 31.0, 0));
T.add(box(11.4, 5.0, 11.4, st, 0, 32.6, 0));
T.add(box(13.0, 1.4, 13.0, pale, 0, 37.6, 0));
T.add(balustrade(13.0, 13.0, 1.8, pale, 0, 39.0, 0));
for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
  T.add(cyl(0.75, 0.95, 3.0, pale, dx * 5.8, 40.8, dz * 5.8, 8));

// ---- circular temple of twelve Ionic columns with flying buttresses
T.add(cyl(3.4, 3.6, 8.0, st, 0, 40.8, 0, 12));
for (let i = 0; i < 12; i++) {
  const a = i / 12 * Math.PI * 2;
  T.add(cyl(0.45, 0.5, 8.0, pale, Math.cos(a) * 4.7, 40.8, Math.sin(a) * 4.7, 6));
}
for (let i = 0; i < 4; i++) {          // scrolled buttresses down to the balustrade
  const a = (i + 0.5) / 4 * Math.PI * 2;
  const b = box(3.6, 0.8, 0.9, pale, Math.cos(a) * 4.4, 41.6, Math.sin(a) * 4.4);
  b.rotation.y = -a; b.rotation.z = -0.55; T.add(b);
}
T.add(cyl(5.6, 5.6, 1.2, pale, 0, 48.8, 0, 12));
T.add(cyl(5.4, 5.4, 0.9, pale, 0, 50.0, 0, 12));

// ---- stage of inverted consoles
T.add(cyl(2.4, 2.8, 4.6, st, 0, 50.9, 0, 12));
for (let i = 0; i < 8; i++) {
  const a = i / 8 * Math.PI * 2;
  const c = box(1.8, 4.6, 0.7, pale, Math.cos(a) * 2.9, 50.9, Math.sin(a) * 2.9);
  c.rotation.y = -a; T.add(c);
}
T.add(cyl(3.6, 3.6, 1.0, pale, 0, 55.5, 0, 12));

// ---- obelisk spire, ball and the copper dragon vane (68 m)
T.add(lathe([[2.3, 0], [2.0, 1.4], [1.5, 3.0], [1.0, 4.4]], pale, 0, 56.5, 0, 8));
T.add(cone(1.1, 5.4, pale, 0, 60.9, 0, 8));
T.add(cyl(0.55, 0.55, 0.9, gold, 0, 66.3, 0, 8));
T.add(cyl(0.14, 0.14, 1.6, gold, 0, 67.2, 0, 6));
T.add(box(2.6, 0.9, 0.2, cop, 0.9, 68.0, 0));          // the dragon weathervane
T.position.set(TX, 0, 0);
g.add(T);

await exportGLB(g, OUT + 'wren_church_bow.glb');
