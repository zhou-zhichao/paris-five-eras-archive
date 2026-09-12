// The British Museum, Sir Robert Smirke 1823-52, with Sydney Smirke's Reading Room (1857).
// Orientation: the GREAT SOUTH FRONT (Ionic colonnade of 44 columns, ~110 m, with an
// 8-column pediment portico) faces +Z.  Quadrangle ~130 x 100 m.  Ground y=0.
// Reading Room drum in the courtyard: 42.6 m diameter dome, crown ~ 32 m.
import { exportGLB, box, cyl, cone, dome, lathe, gableRoof, THREE,
  P, M, column, colonnade, colonnadeZ, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';

const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), dark = M(0x4a463d), glass = M(P.glassroof);

const W = 130, D = 100;             // outer quadrangle
const CW = 92, CD = 60;             // courtyard
const H = 18;                       // main cornice
const COLH = 13.7;                  // Ionic columns 45 ft

// ---------------------------------------------------------------- podium
g.add(box(W + 6, 1.8, D + 6, dk, 0, 0, 0));

// ---------------------------------------------------------------- the four ranges
function range(w, d, x, z) {
  g.add(box(w, H, d, st, x, 1.8, z));
  g.add(box(w + 1.6, 1.8, d + 1.6, pale, x, 1.8 + H, z));      // cornice
  g.add(box(w, 3.4, d, st, x, 3.6 + H, z));                    // attic
  g.add(box(w - 4, 1.0, d - 4, lead, x, 7.0 + H, z));
}
range(W, (D - CD) / 2, 0, (CD + D) / 4);                       // south range
range(W, (D - CD) / 2, 0, -(CD + D) / 4);                      // north range
range((W - CW) / 2, CD, (CW + W) / 4, 0);                      // east range
range((W - CW) / 2, CD, -(CW + W) / 4, 0);                     // west range

// window bands on the outer faces
for (let i = 0; i < 24; i++) {
  const x = -W / 2 + 5 + i * (W - 10) / 23;
  g.add(box(2.6, 6.0, 0.6, dark, x, 8.5, -D / 2 - 0.1));
}
for (let i = 0; i < 16; i++) {
  const z = -D / 2 + 5 + i * (D - 10) / 15;
  g.add(box(0.6, 6.0, 2.6, dark, W / 2 + 0.1, 8.5, z));
  g.add(box(0.6, 6.0, 2.6, dark, -W / 2 - 0.1, 8.5, z));
}

// ---------------------------------------------------------------- SOUTH FRONT colonnade (+z)
{
  const FZ = D / 2;                       // front wall plane
  const CZ = FZ + 4.2;                    // colonnade axis
  g.add(box(W, 3.0, 9, dk, 0, 0, FZ + 2.5));       // stylobate / steps
  for (let i = 0; i < 4; i++) g.add(box(W - i * 2, 0.55, 9 + i * 1.6, dk, 0, 1.1 + i * 0.55, FZ + 3));
  // recessed dark wall behind the columns
  g.add(box(W - 26, 15, 1.0, dark, 0, 3.0, FZ + 0.6));
  // 44 Ionic columns along the front, broken by the projecting portico
  const N = 44, sp = (W - 8) / (N - 1);
  for (let i = 0; i < N; i++) {
    const x = -(W - 8) / 2 + i * sp;
    if (Math.abs(x) < 13.5) continue;              // portico zone
    g.add(column(0.85, COLH, pale, x, 3.0, CZ, 10));
  }
  // entablature over the wings
  for (const sx of [-1, 1]) {
    g.add(box(W / 2 - 13, 3.2, 7.0, pale, sx * (W / 4 + 6.5), 3.0 + COLH, CZ - 1.0));
    g.add(balustrade(W / 2 - 13, 7.0, 2.0, pale, sx * (W / 4 + 6.5), 6.2 + COLH, CZ - 1.0));
  }
  // ---- central portico: 8 columns in two rows + pediment
  const PZ = FZ + 9.5;
  for (let i = 0; i < 8; i++) {
    const x = -13.3 + i * 3.8;
    g.add(column(0.95, COLH, pale, x, 3.0, PZ, 10));
    if (i === 0 || i === 7) g.add(column(0.95, COLH, pale, x, 3.0, PZ - 5.2, 10));
  }
  g.add(box(34, 3.4, 12.5, pale, 0, 3.0 + COLH, PZ - 2.6));
  g.add(pediment(34, 7.4, 12.5, pale, 0, 6.4 + COLH, PZ - 2.6));
  g.add(box(30, 4.6, 0.7, dk, 0, 7.4 + COLH, PZ - 2.6 + 6.0));   // tympanum sculpture band
  // projecting end pavilions with columns
  for (const sx of [-1, 1]) {
    const px = sx * (W / 2 - 9);
    g.add(box(18, H + 2, 12, st, px, 1.8, FZ + 3));
    g.add(box(19.6, 1.8, 13.6, pale, px, 1.8 + H + 2, FZ + 3));
    g.add(balustrade(19.6, 13.6, 2.2, pale, px, 3.6 + H + 2, FZ + 3));
    for (let i = 0; i < 4; i++) g.add(column(0.9, COLH, pale, px - 6.6 + i * 4.4, 3.0, FZ + 9.2, 10));
    g.add(box(19, 3.2, 3.0, pale, px, 3.0 + COLH, FZ + 9.2));
  }
}

// ---------------------------------------------------------------- READING ROOM (courtyard)
{
  const R = 21.3;
  g.add(box(CW - 8, 6, CD - 6, pale, 0, 1.8, 0));               // courtyard infill block
  g.add(cyl(R + 2.4, R + 3.0, 4.0, pale, 0, 7.8, 0, 24));
  g.add(cyl(R, R, 10.0, st, 0, 11.8, 0, 24));                   // drum
  for (let i = 0; i < 20; i++) {
    const a = i / 20 * Math.PI * 2;
    g.add(box(2.4, 6.0, 1.0, dark, Math.cos(a) * R, 13.5, Math.sin(a) * R).rotateY(0));
    g.children[g.children.length - 1].rotation.y = -a;
    g.children[g.children.length - 1].position.set(Math.cos(a) * R, 13.5 + 3.0, Math.sin(a) * R);
  }
  g.add(cyl(R + 1.4, R + 1.4, 1.6, pale, 0, 21.8, 0, 24));
  g.add(lathe([[R, 0], [R - 0.6, 1.6], [R - 2.4, 4.2], [R - 5.0, 6.8], [R - 8.6, 9.0],
    [R - 12.6, 10.6], [R - 16.4, 11.6], [R - 19.0, 12.1]], lead, 0, 23.4, 0, 24));
  g.add(cyl(2.6, 3.0, 2.6, pale, 0, 35.5, 0, 12));              // lantern
  g.add(cone(2.8, 2.4, lead, 0, 38.1, 0, 12));
}

await exportGLB(g, OUT + 'british_museum.glb');
