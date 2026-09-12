// The Royal Courts of Justice, George Edmund Street 1873-82.  Victorian Gothic, Portland stone.
// Orientation: long axis along X; the ~140 m STRAND FRONT with its great porch, clock tower
// and central spires faces +Z.  Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, gableRoof, hipRoof, THREE,
  P, M, pinnacle, openWall, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), dark = M(0x494236), glass = M(P.glassroof);

const W = 140, FD = 24, H = 22, FZ = 46;

function turret(r, h, spire, x, y, z) {
  const t = new THREE.Group();
  t.add(cyl(r, r * 1.08, h, st, 0, 0, 0, 8));
  t.add(cyl(r * 1.3, r * 1.3, 0.9, pale, 0, h - 0.9, 0, 8));
  t.add(cone(r * 1.25, spire, slate, 0, h, 0, 8));
  t.position.set(x, y, z);
  return t;
}
function gothWin(n, x0, x1, w, h, y, z) {
  for (let i = 0; i < n; i++) {
    const x = x0 + (x1 - x0) * i / (n - 1);
    g.add(box(w, h, 0.6, dark, x, y, z));
    g.add(cone(w * 0.72, w * 0.8, dark, x, y + h, z, 6));
  }
}

// ---------------------------------------------------------------- Strand front range
g.add(box(W + 4, 1.4, FD + 4, dk, 0, 0, FZ - FD / 2));
g.add(box(W, H, FD, st, 0, 1.4, FZ - FD / 2));
g.add(box(W + 1.4, 1.4, FD + 1.4, pale, 0, 1.4 + H, FZ - FD / 2));
g.add(gableRoof(W, FD, 9.0, slate, 0, 2.8 + H, FZ - FD / 2, true, 0.5));
for (const zz of [FZ + 0.1, FZ - FD - 0.1]) {
  gothWin(26, -W / 2 + 5, W / 2 - 5, 2.6, 5.0, 4.0, zz);
  gothWin(26, -W / 2 + 5, W / 2 - 5, 2.4, 4.2, 13.0, zz);
}
// gabled dormer bays punctuating the roof
for (let i = 0; i < 9; i++) {
  const x = -W / 2 + 9 + i * (W - 18) / 8;
  if (Math.abs(x) < 18) continue;
  g.add(box(9, H + 5, 4.0, st, x, 1.4, FZ - 1.5));
  g.add(gableRoof(4.0, 9, 5.0, slate, x, 1.4 + H + 5, FZ - 1.5, false, 0.3));
  g.add(box(6, 5.0, 0.6, dark, x, 24.0, FZ + 0.6));
}
// end pavilions with steep roofs
for (const sx of [-1, 1]) {
  const px = sx * (W / 2 - 10);
  g.add(box(22, H + 6, FD + 6, st, px, 1.4, FZ - FD / 2));
  g.add(box(23.6, 1.6, FD + 7.6, pale, px, 1.4 + H + 6, FZ - FD / 2));
  g.add(hipRoof(22, FD + 6, 11.0, slate, px, 3.0 + H + 6, FZ - FD / 2, 0.3));
  g.add(turret(2.4, H + 14, 8.0, px - 10.5, 1.4, FZ - 1.0));
  g.add(turret(2.4, H + 14, 8.0, px + 10.5, 1.4, FZ - 1.0));
}

// ---------------------------------------------------------------- ranges behind, round the Great Hall
g.add(box(W - 30, 20, 30, st, 0, 1.4, FZ - FD - 26));
g.add(gableRoof(W - 30, 30, 8.0, slate, 0, 21.4, FZ - FD - 26, true, 0.4));
for (const sx of [-1, 1]) {
  g.add(box(24, 20, 60, st, sx * 50, 1.4, FZ - FD - 42));
  g.add(gableRoof(24, 60, 7.0, slate, sx * 50, 21.4, FZ - FD - 42, false, 0.4));
}
// the Great Hall itself, a tall aisled space with a steep roof
g.add(box(30, 28, 62, st, 0, 1.4, FZ - FD - 42));
g.add(box(31.4, 1.4, 63.4, pale, 0, 29.4, FZ - FD - 42));
g.add(gableRoof(30, 62, 13.0, slate, 0, 30.8, FZ - FD - 42, false, 0.4));
for (const zs of [1, -1]) for (let i = 0; i < 8; i++)
  g.add(box(0.6, 9.0, 3.2, dark, zs * 15.1, 16.0, FZ - FD - 68 + i * 7.4));

// ---------------------------------------------------------------- central porch, clock tower and spires
{
  // the great gabled entrance porch
  g.add(box(30, H + 8, 8.0, st, 0, 1.4, FZ + 2.0));
  g.add(openWall(30, 20, 8.0, st, [{ cx: 0, y0: 0, w: 10, h: 7, arch: 'pointed', pointed: 1.3 }], 0, 1.4, FZ + 2.0, 12));
  g.add(box(12, 18, 1.0, dark, 0, 1.4, FZ - 2.0));
  g.add(box(31.6, 1.6, 9.6, pale, 0, 1.4 + H + 8, FZ + 2.0));
  g.add(gableRoof(9.6, 31.6, 12.0, st, 0, 3.0 + H + 8, FZ + 2.0, false, 0.2));
  g.add(box(18, 7.0, 0.6, dk, 0, 34.0, FZ + 5.8));
  // flanking turrets
  g.add(turret(2.8, 44, 12.0, -16.5, 1.4, FZ + 2.0));
  g.add(turret(2.8, 44, 12.0, 16.5, 1.4, FZ + 2.0));
  // the clock tower with its steep spire (~60 m)
  const T = new THREE.Group();
  T.add(box(14, 40, 14, st, 0, 1.4, 0));
  for (let s = 0; s < 4; s++) for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 3.2, 5.0, dz ? 0.6 : 3.2, dark, dx * 7.1, 8 + s * 8.5, dz * 7.1));
  T.add(box(15.4, 1.4, 15.4, pale, 0, 41.4, 0));
  T.add(box(12.6, 7.0, 12.6, pale, 0, 42.8, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const d = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2.5, 0.8, 16), M(0xe8e4d8));
    if (dz) d.rotation.x = Math.PI / 2; else d.rotation.z = Math.PI / 2;
    d.position.set(dx * 6.5, 46.3, dz * 6.5); T.add(d);
  }
  T.add(box(14.2, 1.4, 14.2, pale, 0, 49.8, 0));
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    T.add(pinnacle(1.3, 7.0, pale, dx * 6.2, 49.8, dz * 6.2, 6));
  T.add(cone(8.4, 13.0, slate, 0, 51.2, 0, 8));
  T.add(cyl(0.4, 0.6, 2.0, lead, 0, 64.2, 0, 6));
  T.position.set(-30, 0, FZ - 12);
  g.add(T);
  // the smaller spired tower to the east
  const T2 = new THREE.Group();
  T2.add(box(11, 32, 11, st, 0, 1.4, 0));
  T2.add(box(12.2, 1.2, 12.2, pale, 0, 33.4, 0));
  T2.add(box(9.6, 7.0, 9.6, st, 0, 34.6, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T2.add(box(dx ? 0.6 : 4.6, 5.0, dz ? 0.6 : 4.6, dark, dx * 4.9, 35.6, dz * 4.9));
  T2.add(box(11.0, 1.2, 11.0, pale, 0, 41.6, 0));
  T2.add(cone(6.6, 14.0, slate, 0, 42.8, 0, 8));
  T2.add(cyl(0.35, 0.5, 1.8, lead, 0, 56.8, 0, 6));
  T2.position.set(30, 0, FZ - 12);
  g.add(T2);
}

await exportGLB(g, OUT + 'royal_courts_of_justice.glb');
