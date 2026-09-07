// Westminster Cathedral, John Francis Bentley 1895-1903.  Neo-Byzantine, striped red brick
// and Portland stone; nave ~110 m long under four shallow domes; St Edward's campanile 87 m.
// Orientation: liturgical long axis along X, the WEST FRONT and the campanile at -X,
// apse at +X; the long south side faces +Z.  Ground y=0, footprint centred on x,z.
import { exportGLB, box, cyl, cone, lathe, dome, gableRoof, THREE,
  P, M, openWall, arcade, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const bk = M(0x9e5a45), pale = M(P.pale), st = M(P.stone), dk = M(P.dstone),
  lead = M(P.lead), gold = M(P.gold), dark = M(0x4a3a30), cop = M(P.copper);

const L = 110, W = 47, H = 30;
const X0 = -L / 2 + 8;                    // west end of the nave

// helper: a course of alternating brick and stone banding
function stripes(w, h, d, x, y0, z, n = 8) {
  for (let i = 0; i < n; i++) g.add(box(w + 0.5, 1.0, d + 0.5, pale, x, y0 + i * (h / n), z));
}

// ---------------------------------------------------------------- nave and aisles
g.add(box(L + 4, 1.4, W + 4, dk, X0 + L / 2 - 4, 0, 0));
g.add(box(L, 18, W, bk, X0 + L / 2, 1.4, 0));                     // aisles / outer wall
stripes(L, 18, W, X0 + L / 2, 3.6, 0, 6);
g.add(box(L + 1.4, 1.6, W + 1.4, pale, X0 + L / 2, 19.4, 0));
g.add(box(L - 4, H - 21, 26, bk, X0 + L / 2, 21.0, 0));            // nave clerestory box
stripes(L - 4, H - 21, 26, X0 + L / 2, 22.5, 0, 3);
g.add(box(L - 3, 1.4, 27.4, pale, X0 + L / 2, 21.0 + H - 21, 0));
// aisle and clerestory windows
for (const zs of [1, -1]) for (let i = 0; i < 14; i++) {
  const x = X0 + 5 + i * (L - 10) / 13;
  g.add(box(2.6, 5.0, 0.6, dark, x, 8.0, zs * (W / 2 + 0.1)));
  const hd = new THREE.Mesh(new THREE.CylinderGeometry(1.3, 1.3, 0.6, 10, 1, false, 0, Math.PI), dark);
  hd.rotation.x = zs > 0 ? -Math.PI / 2 : Math.PI / 2;
  hd.position.set(x, 13.0, zs * (W / 2 + 0.1)); g.add(hd);
  if (i % 2 === 0) g.add(box(3.2, 4.0, 0.6, dark, x, 23.5, zs * 13.1));
}

// ---------------------------------------------------------------- the four shallow saucer domes
for (let i = 0; i < 4; i++) {
  const cx = X0 + 16 + i * 24;
  g.add(box(28, 3.0, 28, bk, cx, 30.4, 0));
  g.add(box(29.4, 1.2, 29.4, pale, cx, 33.4, 0));
  g.add(cyl(11.6, 12.4, 3.0, bk, cx, 34.6, 0, 16));
  g.add(cyl(12.8, 12.8, 1.0, pale, cx, 37.6, 0, 16));
  g.add(lathe([[11.4, 0], [11.0, 1.2], [9.6, 2.8], [7.4, 4.2], [4.6, 5.2], [1.8, 5.7], [0, 5.8]],
    lead, cx, 38.6, 0, 16));
  g.add(cyl(0.9, 1.2, 1.4, pale, cx, 44.4, 0, 8));
  g.add(cone(1.0, 1.4, gold, cx, 45.8, 0, 8));
}

// ---------------------------------------------------------------- apse and sanctuary (east, +x)
{
  const ax = X0 + L;
  const half = (r, h, m, y) => {
    const c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 18, 1, false, -Math.PI / 2, Math.PI), m);
    c.position.set(ax, y + h / 2, 0); g.add(c);
  };
  half(14, 18, bk, 1.4); half(15, 1.6, pale, 19.4);
  half(12, 8, bk, 21.0); half(13, 1.4, pale, 29.0);
  g.add(lathe([[12.0, 0], [11.4, 1.6], [9.4, 3.6], [6.6, 5.2], [3.2, 6.2], [0, 6.5]], lead, ax, 30.4, 0, 16));
}

// ---------------------------------------------------------------- west front (-x)
{
  const wx = X0 - 2;
  g.add(box(10, 34, 34, bk, wx - 3, 1.4, 0));
  stripes(10, 34, 34, wx - 3, 4.0, 0, 10);
  g.add(box(11.4, 1.6, 35.4, pale, wx - 3, 35.4, 0));
  // great arched west window and portal
  const ww = openWall(34, 30, 2.0, bk, [
    { cx: 0, y0: 12, w: 16, h: 4, arch: true },
    { cx: 0, y0: 0, w: 7.5, h: 4.5, arch: true }], 0, 0, 0, 14);
  const grp = new THREE.Group(); grp.add(ww); grp.rotation.y = -Math.PI / 2; grp.position.set(wx - 8.2, 1.4, 0);
  g.add(grp);
  g.add(box(1.0, 26, 22, dark, wx - 7.0, 1.4, 0));
  // gable + turrets
  g.add(box(4.0, 6.0, 34, bk, wx - 8.0, 35.4, 0));
  for (const zs of [1, -1]) {
    g.add(cyl(3.0, 3.2, 44, bk, wx - 6, 1.4, zs * 15.5, 8));
    g.add(cyl(3.6, 3.6, 1.2, pale, wx - 6, 45.4, zs * 15.5, 8));
    g.add(lathe([[3.4, 0], [3.1, 1.2], [2.2, 2.6], [1.1, 3.6], [0, 4.0]], lead, wx - 6, 46.6, zs * 15.5, 8));
  }
}

// ---------------------------------------------------------------- St Edward's Tower (campanile, 87 m)
{
  const tx = X0 - 6, tz = -W / 2 - 6;
  const T = new THREE.Group();
  T.add(box(15, 62, 15, bk, 0, 0, 0));
  for (let i = 0; i < 16; i++) T.add(box(15.6, 1.0, 15.6, pale, 0, 4 + i * 3.8, 0));
  for (let s = 0; s < 4; s++) for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 3.0, 6.0, dz ? 0.6 : 3.0, dark, dx * 7.6, 12 + s * 12, dz * 7.6));
  T.add(box(16.6, 1.8, 16.6, pale, 0, 62, 0));
  // open belfry stage
  T.add(box(13.5, 10, 13.5, bk, 0, 63.8, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.7 : 9.0, 7.5, dz ? 0.7 : 9.0, dark, dx * 6.9, 65.0, dz * 6.9));
  T.add(box(15.4, 1.6, 15.4, pale, 0, 73.8, 0));
  T.add(balustrade(15.4, 15.4, 1.8, pale, 0, 75.4, 0));
  // small drum, lead cupola and gold cross to 87 m
  T.add(cyl(5.4, 5.8, 3.0, bk, 0, 77.2, 0, 12));
  T.add(cyl(6.4, 6.4, 1.0, pale, 0, 80.2, 0, 12));
  T.add(lathe([[5.4, 0], [5.0, 1.2], [3.9, 2.4], [2.2, 3.4], [0, 3.8]], lead, 0, 81.2, 0, 12));
  T.add(cyl(0.7, 0.9, 1.2, gold, 0, 85.0, 0, 8));
  T.add(box(0.3, 2.0, 0.3, gold, 0, 86.2, 0));
  T.add(box(1.1, 0.3, 0.3, gold, 0, 86.9, 0));
  T.position.set(tx, 0, tz);
  g.add(T);
}

await exportGLB(g, OUT + 'westminster_cathedral.glb');
