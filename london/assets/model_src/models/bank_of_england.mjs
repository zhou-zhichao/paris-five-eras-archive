// The Bank of England, Threadneedle Street: Sir John Soane's windowless screen wall
// (1788-1833) enclosing the whole ~100 x 90 m island site, with Sir Herbert Baker's
// seven-storey rebuilding of 1925-39 and its dome rising behind it.
// Orientation: long axis along X; the main Threadneedle Street front faces +Z.
// Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, prism, hipRoof, THREE,
  P, M, column, ringColonnade, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), dark = M(0x4a463d), gran = M(0x7d7367);

const W = 100, D = 90, SH = 10.5;      // screen wall height

// ---------------------------------------------------------------- Soane's screen wall
function screen(w, d, x, z) {
  g.add(box(w, 1.2, d, dk, x, 0, z));
  g.add(box(w, SH - 2.4, d, st, x, 1.2, z));
  g.add(box(w + 1.4, 1.4, d + 1.4, pale, x, SH - 1.2, z));   // heavy cornice
  g.add(box(w, 1.6, d, st, x, SH + 0.2, z));                 // attic
}
screen(W, 5.0, 0, D / 2 - 2.5);
screen(W, 5.0, 0, -D / 2 + 2.5);
screen(5.0, D - 10, W / 2 - 2.5, 0);
screen(5.0, D - 10, -W / 2 + 2.5, 0);
// blind Corinthian order + recessed niches around the screen (Soane's "Tivoli" order)
for (let i = 0; i < 26; i++) {
  const x = -W / 2 + 3 + i * (W - 6) / 25;
  for (const zs of [1, -1]) {
    g.add(column(0.72, 7.6, pale, x, 1.2, zs * (D / 2 + 0.4), 8));
    g.add(box(2.6, 5.0, 0.5, dk, x + 1.9, 2.4, zs * (D / 2 + 0.15)));
  }
}
for (let i = 0; i < 22; i++) {
  const z = -D / 2 + 3 + i * (D - 6) / 21;
  for (const sx of [-1, 1]) {
    const c = column(0.72, 7.6, pale, sx * (W / 2 + 0.4), 1.2, z, 8);
    g.add(c);
    g.add(box(0.5, 5.0, 2.6, dk, sx * (W / 2 + 0.15), 2.4, z + 1.9));
  }
}
// the Tivoli Corner rotunda (north-west corner)
{
  const cx = -W / 2 + 6, cz = -D / 2 + 6;
  g.add(cyl(9.0, 9.4, SH, st, cx, 0, cz, 16));
  g.add(ringColonnade(10, 9.9, 0.75, 8.0, pale, cx, 1.2, cz, 8));
  g.add(cyl(10.6, 10.6, 1.6, pale, cx, SH, cz, 16));
  g.add(lathe([[8.6, 0], [8.0, 1.6], [6.4, 3.2], [4.0, 4.4], [1.6, 5.0], [0, 5.2]], lead, cx, SH + 1.6, cz, 16));
}
// the main gateway on the +z front
g.add(box(20, SH + 3.5, 6.5, st, 0, 0, D / 2 - 2.5));
g.add(box(21.6, 1.6, 8.0, pale, 0, SH + 3.5, D / 2 - 2.5));
for (let i = 0; i < 4; i++) g.add(column(1.0, 10.5, pale, -6.6 + i * 4.4, 1.2, D / 2 + 2.2, 10));
g.add(box(19, 2.4, 4.2, pale, 0, 11.7, D / 2 + 2.2));
g.add(pediment(19, 3.6, 4.2, pale, 0, 14.1, D / 2 + 2.2));
g.add(box(6.5, 8.0, 0.6, dark, 0, 1.2, D / 2 + 0.9));

// ---------------------------------------------------------------- Baker's 7-storey block
{
  const BW = 62, BD = 54, BH = 30;
  g.add(box(BW, BH, BD, st, 0, 0, -4));
  g.add(box(BW + 1.8, 1.8, BD + 1.8, pale, 0, BH, -4));
  g.add(balustrade(BW + 1.8, BD + 1.8, 2.2, pale, 0, BH + 1.8, -4));
  g.add(hipRoof(BW - 6, BD - 6, 8.0, slate, 0, BH + 1.8, -4, 0.45));
  // seven storeys of window bands
  for (let s = 0; s < 7; s++) {
    const y = 3.0 + s * 3.7;
    g.add(box(BW - 6, 2.4, BD + 0.6, dark, 0, y, -4));
    g.add(box(BW + 0.6, 2.4, BD - 6, dark, 0, y, -4));
  }
  // vertical piers
  for (let i = 0; i < 15; i++) {
    const x = -BW / 2 + 2 + i * (BW - 4) / 14;
    g.add(box(2.0, BH, 1.0, st, x, 0, -4 + BD / 2 + 0.3));
    g.add(box(2.0, BH, 1.0, st, x, 0, -4 - BD / 2 - 0.3));
  }
  // set-back upper stages and the dome
  g.add(box(30, 7.0, 30, st, 0, BH + 4.0, -6));
  g.add(box(31.5, 1.6, 31.5, pale, 0, BH + 11.0, -6));
  g.add(cyl(9.6, 10.2, 6.5, st, 0, BH + 12.6, -6, 16));
  g.add(ringColonnade(16, 10.6, 0.6, 6.5, pale, 0, BH + 12.6, -6, 6));
  g.add(cyl(11.4, 11.4, 1.4, pale, 0, BH + 19.1, -6, 16));
  g.add(lathe([[9.4, 0], [9.0, 1.6], [7.8, 3.6], [6.0, 5.4], [3.6, 6.8], [1.4, 7.5], [0, 7.7]],
    lead, 0, BH + 20.5, -6, 16));
  g.add(cyl(1.8, 2.2, 2.4, pale, 0, BH + 28.2, -6, 10));
  g.add(cone(2.0, 2.6, lead, 0, BH + 30.6, -6, 10));
}

await exportGLB(g, OUT + 'bank_of_england.glb');
