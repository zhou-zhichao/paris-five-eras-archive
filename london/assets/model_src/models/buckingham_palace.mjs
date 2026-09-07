// Buckingham Palace as refaced by Aston Webb, 1913.  Portland stone.
// Orientation: the EAST FRONT (108 m, facing the Mall, with the balcony and central pediment)
// faces +Z.  Quadrangle 108 x 120 m, main cornice ~24 m.  Ground y=0, centred on the origin.
import { exportGLB, box, cyl, cone, dome, lathe, gableRoof, hipRoof, THREE,
  P, M, column, colonnade, pediment, balustrade, parapet, windowsZ, OUT } from './_lib_wren_edwardian.mjs';

const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), dark = M(0x4b4638), gold = M(P.gold), grav = M(0xa89b82);

const W = 108, D = 120, H = 24;
const CW = 62, CD = 60;              // inner quadrangle

// forecourt
g.add(box(W + 4, 0.5, 18, grav, 0, 0, D / 2 + 9));
g.add(box(W + 2, 1.5, D + 2, dk, 0, 0, 0));

// ---------------------------------------------------------------- the four ranges
function range(w, d, x, z, h = H) {
  g.add(box(w, h, d, st, x, 1.5, z));
  g.add(box(w + 1.4, 1.6, d + 1.4, pale, x, 1.5 + h, z));
  g.add(balustrade(w + 1.4, d + 1.4, 2.2, pale, x, 3.1 + h, z));
  g.add(box(w - 5, 1.2, d - 5, slate, x, 3.1 + h, z));
}
range(W, (D - CD) / 2, 0, (CD + D) / 4);                 // east (front) range
range(W, (D - CD) / 2, 0, -(CD + D) / 4);                // west (garden) range
range((W - CW) / 2, CD, (CW + W) / 4, 0);                // north wing
range((W - CW) / 2, CD, -(CW + W) / 4, 0);               // south wing

// ---------------------------------------------------------------- EAST FRONT (+z)
{
  const FZ = D / 2;
  // rusticated ground storey
  g.add(box(W, 7.5, 2.2, dk, 0, 1.5, FZ + 0.6));
  for (let i = 0; i < 19; i++) {
    const x = -W / 2 + 4 + i * (W - 8) / 18;
    g.add(box(2.6, 4.2, 0.6, dark, x, 3.5, FZ + 1.8));         // ground windows
    g.add(box(2.8, 5.6, 0.6, dark, x, 11.0, FZ + 1.0));        // piano nobile
    g.add(box(2.6, 4.2, 0.6, dark, x, 18.0, FZ + 1.0));        // second floor
  }
  // giant engaged order over the two upper storeys
  for (let i = 0; i < 20; i++) {
    const x = -W / 2 + 2.6 + i * (W - 5.2) / 19;
    if (Math.abs(x) < 15) continue;
    g.add(box(2.0, 13.5, 1.3, pale, x, 9.0, FZ + 1.0));
    g.add(box(2.6, 1.1, 1.8, pale, x, 22.5, FZ + 1.1));
  }
  // central pedimented centrepiece with the balcony
  g.add(box(30, H + 1.5, 3.2, st, 0, 1.5, FZ + 1.6));
  for (let i = 0; i < 6; i++) g.add(column(1.15, 13.6, pale, -9.5 + i * 3.8, 9.0, FZ + 3.6, 10));
  g.add(box(32, 2.8, 6.5, pale, 0, 22.6, FZ + 2.6));
  g.add(pediment(32, 6.6, 6.5, pale, 0, 25.4, FZ + 2.6));
  g.add(box(27, 4.2, 0.7, dk, 0, 26.2, FZ + 5.6));
  // THE BALCONY
  g.add(box(13.5, 0.8, 2.6, pale, 0, 8.2, FZ + 4.0));
  g.add(balustrade(13.5, 2.6, 1.6, pale, 0, 9.0, FZ + 4.0, 0.4));
  g.add(box(6.0, 6.0, 0.6, dark, 0, 10.4, FZ + 3.0));
  // corner pavilions
  for (const sx of [-1, 1]) {
    const px = sx * (W / 2 - 8);
    g.add(box(16, H + 4, 16, st, px, 1.5, FZ - 6));
    g.add(box(17.6, 1.8, 17.6, pale, px, 1.5 + H + 4, FZ - 6));
    g.add(balustrade(17.6, 17.6, 2.4, pale, px, 3.3 + H + 4, FZ - 6));
    g.add(hipRoof(15, 15, 4.5, slate, px, 5.7 + H + 4, FZ - 6, 0.2));
    for (let i = 0; i < 4; i++) g.add(column(1.0, 13.5, pale, px - 5.4 + i * 3.6, 9.0, FZ + 2.6, 10));
    g.add(box(16, 2.6, 3.4, pale, px, 22.5, FZ + 2.6));
  }
}

// ---------------------------------------------------------------- garden (west) front + wings
for (let i = 0; i < 18; i++) {
  const x = -W / 2 + 5 + i * (W - 10) / 17;
  g.add(box(2.6, 5.4, 0.6, dark, x, 10.5, -D / 2 - 0.1));
  g.add(box(2.4, 4.0, 0.6, dark, x, 18.0, -D / 2 - 0.1));
}
for (const sx of [-1, 1]) for (let i = 0; i < 18; i++) {
  const z = -D / 2 + 5 + i * (D - 10) / 17;
  g.add(box(0.6, 5.4, 2.6, dark, sx * (W / 2 + 0.1), 10.5, z));
}
// garden-front bow / centre feature
g.add(cyl(11, 11, H, st, 0, 1.5, -D / 2 + 2, 16));
g.add(cyl(12, 12, 1.6, pale, 0, 1.5 + H, -D / 2 + 2, 16));

await exportGLB(g, OUT + 'buckingham_palace.glb');
