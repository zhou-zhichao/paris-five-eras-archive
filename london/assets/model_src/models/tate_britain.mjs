// Tate Britain (the National Gallery of British Art), Sidney R. J. Smith, 1897.
// Portland stone, ~120 m Millbank front with a hexastyle Corinthian portico and a
// low dome over the octagon behind.  Orientation: long axis along X, PORTICO faces +Z
// (the river side).  Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, hipRoof, THREE,
  P, M, column, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), dark = M(0x4a463d), glass = M(P.glassroof);

const W = 120, D = 62, H = 16;

g.add(box(W + 6, 1.6, D + 6, dk, 0, 0, 0));
g.add(box(W, H, D, st, 0, 1.6, 0));
g.add(box(W + 1.8, 2.0, D + 1.8, pale, 0, 1.6 + H, 0));
g.add(balustrade(W + 1.8, D + 1.8, 2.4, pale, 0, 3.6 + H, 0));
// top-lit gallery roofs
for (let i = 0; i < 5; i++) g.add(box(W - 30, 2.6, 8, glass, 0, 3.6 + H, -20 + i * 10));
// pilasters and windows on the flanks
for (let i = 0; i < 21; i++) {
  const x = -W / 2 + 4 + i * (W - 8) / 20;
  if (Math.abs(x) < 20) continue;
  g.add(box(2.2, H - 2, 1.3, pale, x, 1.6, D / 2 + 0.2));
  g.add(box(3.2, 5.0, 0.6, dark, x - 3.0, 5.0, D / 2 + 0.1));
}
for (const sx of [-1, 1]) for (let i = 0; i < 8; i++) {
  const z = -D / 2 + 5 + i * (D - 10) / 7;
  g.add(box(0.6, 5.0, 3.2, dark, sx * (W / 2 + 0.1), 5.0, z));
}
// end pavilions
for (const sx of [-1, 1]) {
  const px = sx * (W / 2 - 11);
  g.add(box(24, H + 4, D * 0.55, st, px, 1.6, 4));
  g.add(box(25.6, 1.8, D * 0.55 + 1.6, pale, px, 1.6 + H + 4, 4));
  g.add(balustrade(25.6, D * 0.55 + 1.6, 2.2, pale, px, 3.4 + H + 4, 4));
  for (let i = 0; i < 4; i++) g.add(column(0.95, 12.5, pale, px - 7.5 + i * 5, 2.6, D / 2 + 1.4, 10));
  g.add(box(24, 2.6, 3.6, pale, px, 15.1, D / 2 + 1.4));
}

// ---------------------------------------------------------------- PORTICO (+z)
{
  const PZ = D / 2 + 8.5;
  for (let i = 0; i < 6; i++) g.add(box(34 - i * 1.8, 0.5, 15 - i * 1.2, dk, 0, i * 0.5, PZ - 1.5));
  for (let i = 0; i < 6; i++) {
    const x = -12.5 + i * 5.0;
    g.add(column(1.3, 14.5, pale, x, 3.0, PZ, 12));
    g.add(column(1.3, 14.5, pale, x, 3.0, PZ - 6.0, 12));
  }
  g.add(box(31, 3.4, 14.5, pale, 0, 17.5, PZ - 3.0));
  g.add(pediment(31, 6.6, 14.5, pale, 0, 20.9, PZ - 3.0));
  g.add(box(26, 4.0, 0.7, dk, 0, 21.7, PZ + 4.0));
  g.add(box(24, 14.5, 1.2, dark, 0, 3.0, PZ - 8.4));
  // low dome over the octagon behind the portico
  g.add(cyl(13.5, 14.5, 8.0, st, 0, 3.6 + H, 2, 8));
  g.add(cyl(15.0, 15.0, 1.6, pale, 0, 11.6 + H, 2, 8));
  g.add(lathe([[13.2, 0], [12.6, 1.6], [11.0, 3.6], [8.6, 5.4], [5.4, 6.8], [2.4, 7.5], [0, 7.7]],
    lead, 0, 13.2 + H, 2, 16));
  g.add(cyl(1.6, 2.0, 2.4, pale, 0, 20.9 + H, 2, 10));
  g.add(cone(1.9, 2.6, lead, 0, 23.3 + H, 2, 10));
}

await exportGLB(g, OUT + 'tate_britain.glb');
