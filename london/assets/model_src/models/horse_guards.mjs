// Horse Guards, William Kent / John Vardy, 1751-53.  Palladian, Portland stone.
// Orientation: long axis along X (~110 m); the three-part FRONT with its central archway
// and clock tower faces +Z (Whitehall).  Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, hipRoof, THREE,
  P, M, column, pediment, balustrade, openWall, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), dark = M(0x4a463d), grav = M(0xa89b82);

const W = 110, D = 32;
g.add(box(W + 6, 0.6, D + 20, grav, 0, 0, -6));

// ---------------------------------------------------------------- two-storey wings
for (const sx of [-1, 1]) {
  const px = sx * 36;
  g.add(box(38, 12.5, D, st, px, 0.6, 0));
  g.add(box(39.4, 1.4, D + 1.4, pale, px, 13.1, 0));
  g.add(hipRoof(38, D, 4.6, slate, px, 14.5, 0, 0.5));
  // pedimented centrepiece of each wing
  g.add(box(16, 15.5, D + 3, st, px, 0.6, 0));
  g.add(box(17.4, 1.4, D + 4.4, pale, px, 16.1, 0));
  g.add(pediment(17.4, 3.6, 4.6, pale, px, 17.5, D / 2 + 1.4));
  g.add(hipRoof(16, D + 3, 4.0, slate, px, 17.5, 0, 0.45));
  // windows
  for (let i = 0; i < 9; i++) {
    const x = px - 17 + i * 4.3;
    g.add(box(2.0, 3.4, 0.6, dark, x, 2.6, D / 2 + 0.2));
    g.add(box(1.8, 2.8, 0.6, dark, x, 8.4, D / 2 + 0.2));
    g.add(box(2.0, 3.4, 0.6, dark, x, 2.6, -D / 2 - 0.2));
    g.add(box(1.8, 2.8, 0.6, dark, x, 8.4, -D / 2 - 0.2));
  }
  // outer end pavilions
  const ex = sx * (W / 2 - 7);
  g.add(box(14, 14.5, D + 2, st, ex, 0.6, 0));
  g.add(box(15.4, 1.4, D + 3.4, pale, ex, 15.1, 0));
  g.add(hipRoof(14, D + 2, 4.2, slate, ex, 16.5, 0, 0.45));
}

// ---------------------------------------------------------------- central block with the archway
{
  const CW = 26;
  const ops = [{ cx: 0, y0: 0, w: 5.6, h: 4.4, arch: true },
  { cx: -9.5, y0: 0, w: 3.2, h: 3.4, arch: true },
  { cx: 9.5, y0: 0, w: 3.2, h: 3.4, arch: true }];
  for (const zz of [D / 2 - 1.5, -D / 2 + 1.5]) g.add(openWall(CW, 16, 3.0, st, ops, 0, 0.6, zz, 12));
  for (const sx of [-1, 1]) g.add(box(3.0, 16, D, st, sx * (CW / 2 - 1.5), 0.6, 0));
  for (const px of [-5.9, 5.9]) g.add(box(2.6, 16, D - 4, st, px, 0.6, 0));
  g.add(box(CW, 5.5, D, st, 0, 11.1, 0));                       // solid upper part
  g.add(box(CW + 1.6, 1.6, D + 1.6, pale, 0, 16.6, 0));
  g.add(balustrade(CW + 1.6, D + 1.6, 1.8, pale, 0, 18.2, 0));
  for (const zs of [1, -1]) for (const x of [-9.5, 9.5])
    g.add(box(3.2, 3.0, 0.6, dark, x, 12.0, zs * (D / 2 + 0.2)));
  // the clock tower (~30 m)
  g.add(box(12, 3.6, 12, st, 0, 18.2, 0));
  g.add(box(13.2, 1.0, 13.2, pale, 0, 21.8, 0));
  g.add(cyl(4.6, 5.0, 3.8, st, 0, 22.8, 0, 8));                 // octagonal clock stage
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const d = new THREE.Mesh(new THREE.CylinderGeometry(1.9, 1.9, 0.7, 16), M(0x2f2b26));
    if (dz) d.rotation.x = Math.PI / 2; else d.rotation.z = Math.PI / 2;
    d.position.set(dx * 4.9, 24.7, dz * 4.9); g.add(d);
  }
  g.add(cyl(5.6, 5.6, 0.9, pale, 0, 26.6, 0, 8));
  g.add(lathe([[4.6, 0], [4.4, 0.9], [3.4, 2.0], [2.0, 2.9], [0.9, 3.5], [0, 3.8]], lead, 0, 27.5, 0, 8));
  g.add(cyl(0.3, 0.3, 1.6, lead, 0, 31.3, 0, 6));
}

await exportGLB(g, OUT + 'horse_guards.glb');
