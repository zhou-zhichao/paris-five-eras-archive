// The Mansion House, George Dance the Elder, 1739-52.  Portland stone.
// Orientation: long axis along X, ~60 x 40 m, ~25 m high; the six-column Corinthian
// PORTICO and pediment face +Z.  Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, hipRoof, THREE,
  P, M, column, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate), dark = M(0x4a463d);

const W = 60, D = 40, H = 21;

// rusticated base + main block
g.add(box(W + 3, 1.2, D + 3, dk, 0, 0, 0));
g.add(box(W, 7.5, D, dk, 0, 1.2, 0));                    // rusticated ground storey
g.add(box(W, H - 7.5, D, st, 0, 8.7, 0));
g.add(box(W + 1.6, 1.8, D + 1.6, pale, 0, 1.2 + H, 0));  // cornice
g.add(balustrade(W + 1.6, D + 1.6, 2.4, pale, 0, 3.0 + H, 0));
g.add(box(W - 5, 1.0, D - 5, slate, 0, 3.0 + H, 0));
// the "Egyptian Hall" attic behind the portico
g.add(box(30, 5.5, 24, st, 0, 3.0 + H, -2));
g.add(box(31.5, 1.2, 25.5, pale, 0, 8.5 + H, -2));
g.add(hipRoof(30, 24, 4.5, slate, 0, 9.7 + H, -2, 0.35));

// windows
for (const zs of [1, -1]) for (let i = 0; i < 11; i++) {
  const x = -W / 2 + 4 + i * (W - 8) / 10;
  if (zs > 0 && Math.abs(x) < 13) continue;
  g.add(box(2.4, 3.6, 0.6, dark, x, 3.4, zs * (D / 2 + 0.1)));
  g.add(box(2.6, 5.0, 0.6, dark, x, 10.5, zs * (D / 2 + 0.1)));
  g.add(box(2.2, 3.2, 0.6, dark, x, 17.0, zs * (D / 2 + 0.1)));
}
for (const sx of [-1, 1]) for (let i = 0; i < 7; i++) {
  const z = -D / 2 + 4 + i * (D - 8) / 6;
  g.add(box(0.6, 5.0, 2.6, dark, sx * (W / 2 + 0.1), 10.5, z));
  g.add(box(0.6, 3.2, 2.2, dark, sx * (W / 2 + 0.1), 17.0, z));
}

// ---------------------------------------------------------------- PORTICO (+z), 6 columns
{
  const PZ = D / 2 + 6.5;
  for (let i = 0; i < 8; i++) g.add(box(28 - i * 1.6, 0.55, 12 - i * 0.7, dk, 0, i * 0.55, PZ - 1.0));
  for (let i = 0; i < 6; i++) {
    const x = -10.5 + i * 4.2;
    g.add(column(1.15, 13.0, pale, x, 4.4, PZ, 12));
    if (i === 0 || i === 5) g.add(column(1.15, 13.0, pale, x, 4.4, PZ - 5.0, 12));
  }
  g.add(box(26.5, 3.0, 11.5, pale, 0, 17.4, PZ - 2.4));
  g.add(pediment(26.5, 5.8, 11.5, pale, 0, 20.4, PZ - 2.4));
  g.add(box(22, 3.6, 0.7, dk, 0, 21.2, PZ + 3.0));            // tympanum sculpture
  g.add(box(21, 13, 1.2, dark, 0, 4.4, PZ - 5.4));
}

await exportGLB(g, OUT + 'mansion_house.glb');
