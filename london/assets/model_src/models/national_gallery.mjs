// The National Gallery, William Wilkins 1838.  Portland stone, ~140 m Trafalgar Square front.
// Orientation: long axis along X; the long FRONT with its central Corinthian portico,
// pediment, saucer dome and the two little "pepperpot" cupolas faces +Z.  Ground y=0.
import { exportGLB, box, cyl, cone, lathe, dome, hipRoof, THREE,
  P, M, column, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), dark = M(0x4a463d), glass = M(P.glassroof);

const W = 140, D = 56, H = 17;

// terrace and steps down to Trafalgar Square
g.add(box(W + 8, 2.4, D + 16, dk, 0, 0, -4));
for (let i = 0; i < 5; i++) g.add(box(W * 0.55 - i * 2, 0.48, 3 + i * 1.6, dk, 0, i * 0.48, D / 2 + 4));

// main range
g.add(box(W, H, D, st, 0, 2.4, 0));
g.add(box(W + 1.6, 1.8, D + 1.6, pale, 0, 2.4 + H, 0));
g.add(balustrade(W + 1.6, D + 1.6, 2.2, pale, 0, 4.2 + H, 0));
g.add(box(W - 6, 1.0, D - 6, slate, 0, 4.2 + H, 0));
// north-lit gallery roofs
for (let i = 0; i < 6; i++) g.add(box(W - 20, 2.2, 5, glass, 0, 5.2 + H, -18 + i * 7));

// pilasters + windows on the front
for (let i = 0; i < 25; i++) {
  const x = -W / 2 + 4 + i * (W - 8) / 24;
  if (Math.abs(x) < 17) continue;
  g.add(box(2.2, 12.5, 1.2, pale, x, 5.0, D / 2 + 0.2));
  g.add(box(3.0, 4.2, 0.6, dark, x - 2.8, 6.0, D / 2 + 0.1));
}
g.add(box(W, 1.2, 1.2, pale, 0, 17.5, D / 2 + 0.4));

// ---------------------------------------------------------------- central portico (+z)
{
  const PZ = D / 2 + 7.5;
  for (let i = 0; i < 4; i++) g.add(box(36 - i * 2, 0.6, 14 - i * 1.4, dk, 0, 2.4 - (4 - i) * 0.6, PZ - 1.5));
  for (let i = 0; i < 8; i++) {
    const x = -13.3 + i * 3.8;
    g.add(column(1.1, 13.0, pale, x, 2.4, PZ, 12));
    if (i === 0 || i === 7) g.add(column(1.1, 13.0, pale, x, 2.4, PZ - 5.4, 12));
  }
  g.add(box(31, 3.0, 12.5, pale, 0, 15.4, PZ - 2.6));
  g.add(pediment(31, 6.2, 12.5, pale, 0, 18.4, PZ - 2.6));
  g.add(box(26, 12, 1.2, dark, 0, 2.4, PZ - 5.8));
  // the saucer dome over the entrance hall
  g.add(box(24, 6.5, 24, st, 0, 21.4, D / 2 - 12));
  g.add(box(25.5, 1.4, 25.5, pale, 0, 27.9, D / 2 - 12));
  g.add(cyl(9.0, 9.6, 4.0, st, 0, 29.3, D / 2 - 12, 16));
  for (let i = 0; i < 12; i++) {
    const a = i / 12 * Math.PI * 2;
    g.add(column(0.5, 4.0, pale, Math.cos(a) * 9.9, 29.3, D / 2 - 12 + Math.sin(a) * 9.9, 6));
  }
  g.add(cyl(10.6, 10.6, 1.2, pale, 0, 33.3, D / 2 - 12, 16));
  g.add(lathe([[9.4, 0], [9.0, 1.2], [7.8, 2.8], [6.0, 4.2], [3.6, 5.2], [1.6, 5.7], [0, 5.9]],
    lead, 0, 34.5, D / 2 - 12, 16));
  g.add(cyl(1.3, 1.6, 2.0, pale, 0, 40.4, D / 2 - 12, 10));
  g.add(cone(1.5, 2.0, lead, 0, 42.4, D / 2 - 12, 10));
}

// ---------------------------------------------------------------- flanking pepperpot cupolas
for (const sx of [-1, 1]) {
  const px = sx * 41;
  g.add(box(20, H + 3.5, 20, st, px, 2.4, D / 2 - 10));
  g.add(box(21.6, 1.6, 21.6, pale, px, 2.4 + H + 3.5, D / 2 - 10));
  g.add(balustrade(21.6, 21.6, 2.0, pale, px, 4.0 + H + 3.5, D / 2 - 10));
  for (let i = 0; i < 4; i++) g.add(column(1.0, 12.5, pale, px - 6.6 + i * 4.4, 2.4, D / 2 + 3.0, 10));
  g.add(box(20, 2.6, 4.0, pale, px, 14.9, D / 2 + 3.0));
  // pepperpot
  g.add(cyl(3.2, 3.4, 5.0, st, px, 26.5, D / 2 - 10, 12));
  for (let i = 0; i < 8; i++) {
    const a = i / 8 * Math.PI * 2;
    g.add(column(0.42, 5.0, pale, px + Math.cos(a) * 3.9, 26.5, D / 2 - 10 + Math.sin(a) * 3.9, 6));
  }
  g.add(cyl(4.4, 4.4, 1.0, pale, px, 31.5, D / 2 - 10, 12));
  g.add(lathe([[3.6, 0], [3.2, 1.0], [2.2, 2.2], [1.0, 3.0], [0, 3.4]], lead, px, 32.5, D / 2 - 10, 12));
  g.add(cyl(0.35, 0.35, 1.6, lead, px, 35.9, D / 2 - 10, 6));
}

await exportGLB(g, OUT + 'national_gallery.glb');
