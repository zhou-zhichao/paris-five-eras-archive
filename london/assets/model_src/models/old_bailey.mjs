// The Central Criminal Court ("the Old Bailey"), E. W. Mountford 1907.  English Baroque,
// Portland stone; dome carrying the gilt figure of Justice, 67 m to the tip of her sword.
// Orientation: long axis along X, ~68 x 52 m; the main front with the domed centrepiece
// faces +Z.  Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, hipRoof, THREE,
  P, M, column, ringColonnade, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), gold = M(P.gold), dark = M(0x4a463d), gran = M(0x7d7367);

const W = 68, D = 52, H = 25;

g.add(box(W + 4, 1.4, D + 4, dk, 0, 0, 0));
g.add(box(W, 7.0, D, gran, 0, 1.4, 0));                   // rusticated granite base
g.add(box(W, H - 7.0, D, st, 0, 8.4, 0));
g.add(box(W + 1.8, 2.0, D + 1.8, pale, 0, 1.4 + H, 0));
g.add(balustrade(W + 1.8, D + 1.8, 2.2, pale, 0, 3.4 + H, 0));
g.add(hipRoof(W - 8, D - 8, 6.0, slate, 0, 3.4 + H, 0, 0.4));

// window tiers and a giant pilaster order
for (const zs of [1, -1]) for (let i = 0; i < 13; i++) {
  const x = -W / 2 + 4 + i * (W - 8) / 12;
  g.add(box(2.6, 3.6, 0.6, dark, x, 3.6, zs * (D / 2 + 0.1)));
  if (Math.abs(x) > 12) {
    g.add(box(2.0, 15.0, 1.2, pale, x + 3.0, 9.0, zs * (D / 2 + 0.2)));
    g.add(box(2.8, 5.0, 0.6, dark, x, 10.5, zs * (D / 2 + 0.1)));
    g.add(box(2.4, 3.4, 0.6, dark, x, 18.5, zs * (D / 2 + 0.1)));
  }
}
for (const sx of [-1, 1]) for (let i = 0; i < 9; i++) {
  const z = -D / 2 + 4 + i * (D - 8) / 8;
  g.add(box(0.6, 5.0, 2.8, dark, sx * (W / 2 + 0.1), 10.5, z));
  g.add(box(0.6, 3.4, 2.4, dark, sx * (W / 2 + 0.1), 18.5, z));
}
// end pavilions with segmental pediments
for (const sx of [-1, 1]) {
  const px = sx * (W / 2 - 8);
  g.add(box(17, H + 3, D + 3, st, px, 1.4, 0));
  g.add(box(18.6, 1.8, D + 4.6, pale, px, 1.4 + H + 3, 0));
  g.add(balustrade(18.6, D + 4.6, 2.2, pale, px, 3.2 + H + 3, 0));
}

// ---------------------------------------------------------------- domed centrepiece (+z)
{
  const CZ = 2;
  g.add(box(26, H + 5, 26, st, 0, 1.4, CZ));
  g.add(box(27.6, 2.0, 27.6, pale, 0, 1.4 + H + 5, CZ));
  g.add(balustrade(27.6, 27.6, 2.4, pale, 0, 3.4 + H + 5, CZ));
  // entrance portico
  for (let i = 0; i < 4; i++) g.add(column(1.15, 13.0, pale, -7.5 + i * 5.0, 8.4, D / 2 + 2.0, 12));
  g.add(box(24, 2.8, 5.0, pale, 0, 21.4, D / 2 + 2.0));
  g.add(pediment(24, 4.6, 5.0, pale, 0, 24.2, D / 2 + 2.0));
  // drum + peristyle
  const Y = 3.4 + H + 5 + 2.4;                 // 35.8
  g.add(cyl(9.6, 10.2, 3.0, st, 0, Y, CZ, 16));
  g.add(cyl(8.2, 8.2, 9.5, st, 0, Y + 3.0, CZ, 16));
  g.add(ringColonnade(16, 9.4, 0.6, 9.5, pale, 0, Y + 3.0, CZ, 6));
  g.add(cyl(10.4, 10.4, 1.5, pale, 0, Y + 12.5, CZ, 16));
  g.add(cyl(10.5, 10.5, 1.4, pale, 0, Y + 14.0, CZ, 16));
  // the dome
  g.add(lathe([[8.0, 0], [7.8, 1.2], [7.0, 3.0], [5.8, 4.6], [4.2, 5.9], [2.2, 6.8], [0, 7.1]],
    lead, 0, Y + 15.4, CZ, 16));
  // lantern
  g.add(cyl(2.4, 2.8, 3.0, pale, 0, Y + 22.5, CZ, 12));
  g.add(cyl(3.2, 3.2, 1.0, pale, 0, Y + 25.5, CZ, 12));
  g.add(lathe([[2.6, 0], [2.2, 1.0], [1.4, 2.0], [0.5, 2.7], [0, 3.0]], lead, 0, Y + 26.5, CZ, 12));
  // the gilt figure of Justice: scales in one hand, sword raised in the other (3.7 m)
  const jy = Y + 29.5;                         // 65.3 -> sword tip ~67 m
  g.add(cyl(0.7, 0.9, 1.2, pale, 0, jy - 1.2, CZ, 8));
  g.add(box(0.9, 2.6, 0.7, gold, 0, jy, CZ));
  g.add(box(3.6, 0.22, 0.22, gold, 0, jy + 2.2, CZ));      // outstretched arms
  g.add(box(0.2, 0.9, 0.2, gold, -1.7, jy + 1.3, CZ));     // scales
  g.add(box(1.2, 0.16, 0.16, gold, -1.7, jy + 1.3, CZ));
  g.add(box(0.22, 3.0, 0.22, gold, 1.75, jy + 2.2, CZ));   // sword
}

await exportGLB(g, OUT + 'old_bailey.glb');
