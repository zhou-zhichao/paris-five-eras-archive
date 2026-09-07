// Somerset House, Sir William Chambers, from 1776.  Portland stone.
// Orientation: the 150 m RIVER FRONT, standing on its great rusticated arcaded terrace,
// faces +Z (the Thames); the Strand block with its little dome closes the quadrangle at -Z.
// Quadrangle ~100 x 90 m, 4 storeys ~22 m.  Ground y=0 = the old foreshore.
import { exportGLB, box, cyl, cone, lathe, hipRoof, THREE,
  P, M, column, pediment, balustrade, openWall, arcade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), dark = M(0x4a463d), water = M(P.water);

const W = 150, D = 100, TH = 8.5, H = 22;    // terrace height, range height

// ---------------------------------------------------------------- river terrace + arcade (+z)
{
  const TZ = D / 2 + 6;
  const ops = [];
  for (let i = 0; i < 15; i++) ops.push({ cx: -70 + i * 10, y0: 0, w: 5.4, h: 3.6, arch: true });
  g.add(openWall(W, TH, 3.0, dk, ops, 0, 0, TZ + 4.5, 10));
  g.add(box(W, TH, 12, dk, 0, 0, TZ - 3.0));
  g.add(box(W + 2, 1.2, 15, pale, 0, TH, TZ + 1.5));
  // the great central water-gate arch
  g.add(box(22, TH + 2.5, 8, dk, 0, 0, TZ + 5.5));
  g.add(cyl(6.5, 6.5, 8.5, dark, 0, 0, TZ + 5.5, 12));
}

// ---------------------------------------------------------------- ranges round the quadrangle
function range(w, d, x, z, h = H, y0 = 0) {
  g.add(box(w, 6.5, d, dk, x, y0, z));                         // rusticated ground storey
  g.add(box(w, h - 6.5, d, st, x, y0 + 6.5, z));
  g.add(box(w + 1.6, 1.6, d + 1.6, pale, x, y0 + h, z));
  g.add(balustrade(w + 1.6, d + 1.6, 2.0, pale, x, y0 + h + 1.6, z));
  g.add(hipRoof(w - 4, d - 4, 4.0, slate, x, y0 + h + 1.6, z, 0.5));
}
range(W, 22, 0, D / 2 - 5, H, TH);                              // river range on the terrace
range(46, 20, 0, -D / 2 + 10);                                  // Strand block
range(24, D - 30, -W / 2 + 12, 0);                              // west wing
range(24, D - 30, W / 2 - 12, 0);                               // east wing
range(30, 18, -46, -D / 2 + 10);                                // Strand wings
range(30, 18, 46, -D / 2 + 10);

// window bands
for (let i = 0; i < 27; i++) {
  const x = -W / 2 + 4 + i * (W - 8) / 26;
  g.add(box(2.4, 4.2, 0.6, dark, x, TH + 9.0, D / 2 + 6.1));
  g.add(box(2.2, 3.2, 0.6, dark, x, TH + 15.5, D / 2 + 6.1));
  if (Math.abs(x) > 26) g.add(box(1.6, H - 6.5, 1.1, pale, x + 2.8, TH + 6.5, D / 2 + 6.2));
}
for (const sx of [-1, 1]) for (let i = 0; i < 12; i++) {
  const z = -D / 2 + 6 + i * (D - 12) / 11;
  g.add(box(0.6, 4.2, 2.4, dark, sx * (W / 2 + 0.1), 9.0, z));
  g.add(box(0.6, 3.2, 2.2, dark, sx * (W / 2 + 0.1), 15.5, z));
}

// ---------------------------------------------------------------- river-front centrepiece & pavilions
{
  const FZ = D / 2 + 7;
  g.add(box(34, H + 2, 5.0, st, 0, TH, FZ));
  for (let i = 0; i < 6; i++) g.add(column(1.0, 12.0, pale, -10.5 + i * 4.2, TH + 8.0, FZ + 2.8, 10));
  g.add(box(32, 2.6, 5.0, pale, 0, TH + 20.0, FZ + 2.0));
  g.add(pediment(32, 6.0, 5.0, pale, 0, TH + 22.6, FZ + 2.0));
  // domed end pavilions
  for (const sx of [-1, 1]) {
    const px = sx * 58;
    g.add(box(24, H + 3, 24, st, px, TH, D / 2 - 6));
    g.add(box(25.6, 1.6, 25.6, pale, px, TH + H + 3, D / 2 - 6));
    g.add(balustrade(25.6, 25.6, 2.0, pale, px, TH + H + 4.6, D / 2 - 6));
    for (let i = 0; i < 4; i++) g.add(column(0.9, 11.5, pale, px - 6.3 + i * 4.2, TH + 8.0, D / 2 + 7.0, 10));
    g.add(box(22, 2.4, 3.2, pale, px, TH + 19.5, D / 2 + 7.0));
    g.add(cyl(4.6, 5.0, 3.6, st, px, TH + H + 6.6, D / 2 - 6, 12));
    g.add(lathe([[4.4, 0], [4.0, 1.2], [3.0, 2.4], [1.6, 3.3], [0, 3.7]], lead, px, TH + H + 10.2, D / 2 - 6, 12));
    g.add(cyl(0.35, 0.35, 1.6, lead, px, TH + H + 13.9, D / 2 - 6, 6));
  }
}

// ---------------------------------------------------------------- Strand block with its dome
{
  const SZ = -D / 2 + 10;
  for (let i = 0; i < 3; i++) g.add(column(1.05, 12.5, pale, -8 + i * 8, 6.5, SZ - 11.5, 10));
  g.add(box(30, 2.6, 4.0, pale, 0, 19.0, SZ - 11.0));
  g.add(pediment(30, 5.4, 4.0, pale, 0, 21.6, SZ - 11.0));
  g.add(cyl(7.6, 8.2, 5.0, st, 0, H + 3.6, SZ, 16));
  for (let i = 0; i < 10; i++) {
    const a = i / 10 * Math.PI * 2;
    g.add(column(0.5, 5.0, pale, Math.cos(a) * 8.6, H + 3.6, SZ + Math.sin(a) * 8.6, 6));
  }
  g.add(cyl(9.4, 9.4, 1.2, pale, 0, H + 8.6, SZ, 16));
  g.add(lathe([[7.8, 0], [7.4, 1.2], [6.4, 2.8], [4.8, 4.2], [2.8, 5.2], [0, 5.7]], lead, 0, H + 9.8, SZ, 16));
  g.add(cyl(1.1, 1.4, 1.8, pale, 0, H + 15.5, SZ, 10));
  g.add(cone(1.3, 1.8, lead, 0, H + 17.3, SZ, 10));
}

await exportGLB(g, OUT + 'somerset_house.glb');
