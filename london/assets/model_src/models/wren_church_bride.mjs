// St Bride's, Fleet Street, Christopher Wren 1672-1703 — the tiered "wedding-cake"
// steeple, 69 m (four diminishing octagonal stages and an obelisk).
// Long axis along X, tower at the WEST end (-X), south side towards +Z.  Ground y=0.
import { exportGLB, box, cyl, cone, lathe, THREE, P, M,
  balustrade, churchBody, OUT } from './_lib_church.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), lead = M(P.lead), gold = M(P.gold), dark = M(0x4a463d);

const L = 34, W = 17, H = 14;
const X0 = -L / 2 + 6;
churchBody(g, X0, L, W, H, { bays: 4 });

// ---------------------------------------------------------------- the tower
const TX = X0 - 6.5;
const T = new THREE.Group();
T.add(box(11.5, 26, 11.5, st, 0, 1.0, 0));
for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
  T.add(box(dx ? 0.6 : 3.4, 6.0, dz ? 0.6 : 3.4, dark, dx * 5.9, 5.0, dz * 5.9));
  T.add(box(dx ? 0.6 : 3.4, 6.6, dz ? 0.6 : 3.4, dark, dx * 5.9, 17.0, dz * 5.9));
}
T.add(box(12.8, 1.4, 12.8, pale, 0, 27.0, 0));
T.add(box(10.4, 8.0, 10.4, st, 0, 28.4, 0));
for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
  T.add(box(dx ? 0.6 : 4.0, 6.0, dz ? 0.6 : 4.0, dark, dx * 5.3, 29.4, dz * 5.3));
T.add(box(12.0, 1.4, 12.0, pale, 0, 36.4, 0));
T.add(balustrade(12.0, 12.0, 1.6, pale, 0, 37.8, 0));

// ---- the four diminishing octagonal open stages
let y = 39.4;
const rs = [4.5, 3.7, 2.9, 2.1], hs = [5.6, 4.9, 4.2, 3.4];
for (let s = 0; s < 4; s++) {
  const r = rs[s], h = hs[s];
  T.add(cyl(r * 0.55, r * 0.6, h, st, 0, y, 0, 8));            // slim core
  for (let i = 0; i < 8; i++) {                                 // ring of columns
    const a = i / 8 * Math.PI * 2;
    T.add(cyl(r * 0.14, r * 0.16, h, pale, Math.cos(a) * r, y, Math.sin(a) * r, 6));
  }
  T.add(cyl(r * 1.22, r * 1.22, 0.9, pale, 0, y + h, 0, 8));    // entablature
  T.add(cyl(r * 1.10, r * 1.16, 0.8, pale, 0, y + h + 0.9, 0, 8));
  y += h + 1.7;
}
// the obelisk finial
T.add(cone(1.7, 4.0, pale, 0, y, 0, 8));
T.add(cyl(0.24, 0.24, 1.4, gold, 0, y + 4.0, 0, 6));
T.position.set(TX, 0, 0);
g.add(T);

await exportGLB(g, OUT + 'wren_church_bride.glb');
