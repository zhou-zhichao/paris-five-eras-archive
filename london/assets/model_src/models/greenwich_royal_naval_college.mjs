// The Royal Hospital for Seamen at Greenwich (Wren, Hawksmoor, Vanbrugh, 1696-1751),
// later the Royal Naval College.  Portland stone.
// Orientation: the RIVER (Thames) front faces +Z; the twin colonnaded domed blocks
// (King William and Queen Mary, domes ~40 m) flank the vista running away to -Z towards
// the Queen's House.  Whole composition ~300 x 200 m.  Ground y=0, centred on the origin.
import { exportGLB, box, cyl, cone, lathe, hipRoof, gableRoof, THREE,
  P, M, column, colonnade, colonnadeZ, ringColonnade, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), gold = M(P.gold), dark = M(0x4a463d), grass = M(P.grass), grav = M(0xa89b82);

const AX = 58;          // half-width of the central vista
const ZR = 88;          // river frontage line

// ground: gravel court and the grass vista to the Queen's House
g.add(box(300, 0.4, 200, grav, 0, 0, 0));
g.add(box(2 * AX - 14, 0.5, 210, grass, 0, 0.4, -10));

// ---------------------------------------------------------------- the four ranges
// each side of the vista has a river-side block (with the dome) and a landward block
function block(sx, z, w, d, h) {
  const x = sx * (AX + w / 2);
  g.add(box(w, h, d, st, x, 0.4, z));
  g.add(box(w + 1.6, 1.6, d + 1.6, pale, x, 0.4 + h, z));
  g.add(balustrade(w + 1.6, d + 1.6, 2.0, pale, x, 2.0 + h, z));
  g.add(hipRoof(w - 4, d - 4, 5.0, slate, x, 2.0 + h, z, 0.5));
  // windows, two main storeys
  for (const zs of [1, -1]) for (let i = 0; i < Math.round(w / 5); i++) {
    const xx = x - w / 2 + 3 + i * (w - 6) / (Math.round(w / 5) - 1);
    g.add(box(2.2, 3.6, 0.6, dark, xx, 3.4, z + zs * (d / 2 + 0.1)));
    g.add(box(2.0, 3.0, 0.6, dark, xx, 9.4, z + zs * (d / 2 + 0.1)));
  }
  for (const s2 of [-1, 1]) for (let i = 0; i < Math.round(d / 5); i++) {
    const zz = z - d / 2 + 3 + i * (d - 6) / (Math.round(d / 5) - 1);
    g.add(box(0.6, 3.6, 2.2, dark, x + s2 * (w / 2 + 0.1), 3.4, zz));
    g.add(box(0.6, 3.0, 2.0, dark, x + s2 * (w / 2 + 0.1), 9.4, zz));
  }
  return x;
}
for (const sx of [-1, 1]) {
  block(sx, ZR - 22, 62, 44, 16);            // river-side ranges (King Charles / Queen Anne)
  block(sx, -8, 58, 62, 16);                 // landward ranges (King William / Queen Mary)
  block(sx, -78, 46, 34, 14);                // southern wings
}

// ---------------------------------------------------------------- the two great domes
for (const sx of [-1, 1]) {
  const cx = sx * (AX + 14), cz = 12;
  // domed vestibule block
  g.add(box(26, 22, 26, st, cx, 0.4, cz));
  g.add(box(27.6, 1.8, 27.6, pale, cx, 22.4, cz));
  g.add(balustrade(27.6, 27.6, 2.2, pale, cx, 24.2, cz));
  // drum with a ring of coupled columns
  g.add(cyl(8.4, 9.0, 4.0, st, cx, 26.4, cz, 16));
  g.add(cyl(7.2, 7.2, 7.5, st, cx, 30.4, cz, 16));
  g.add(ringColonnade(12, 8.4, 0.55, 7.5, pale, cx, 30.4, cz, 6));
  g.add(cyl(9.4, 9.4, 1.4, pale, cx, 37.9, cz, 16));
  // dome + lantern, apex ~40 m
  g.add(lathe([[7.0, 0], [6.7, 1.2], [5.9, 2.6], [4.6, 3.9], [2.8, 4.9], [1.2, 5.4], [0, 5.6]],
    lead, cx, 39.3, cz, 16));
  g.add(cyl(1.6, 2.0, 2.6, pale, cx, 44.9, cz, 10));
  g.add(cone(1.8, 2.2, lead, cx, 47.5, cz, 10));
  g.add(cyl(0.2, 0.2, 1.2, gold, cx, 49.7, cz, 6));
  // the famous colonnades of coupled Doric columns facing the vista
  for (let i = 0; i < 16; i++) {
    const z = cz - 34 + i * 4.6;
    g.add(column(0.85, 8.5, pale, sx * AX, 0.4, z, 10));
    g.add(column(0.85, 8.5, pale, sx * (AX + 2.6), 0.4, z, 10));
  }
  g.add(box(6.4, 2.4, 78, pale, sx * (AX + 1.3), 8.9, cz - 32));
  g.add(balustrade(6.4, 78, 1.8, pale, sx * (AX + 1.3), 11.3, cz - 32));
}

// ---------------------------------------------------------------- river-front pedimented centres
for (const sx of [-1, 1]) {
  const px = sx * (AX + 31);
  for (let i = 0; i < 4; i++) g.add(column(1.0, 13.0, pale, px - 6.6 + i * 4.4, 0.4, ZR + 2.0, 10));
  g.add(box(22, 2.6, 4.5, pale, px, 13.4, ZR + 2.0));
  g.add(pediment(22, 4.4, 4.5, pale, px, 16.0, ZR + 2.0));
}

// ---------------------------------------------------------------- the Queen's House, closing the vista
{
  const qz = -128;
  g.add(box(36, 14, 24, pale, 0, 0.4, qz));
  g.add(box(37.4, 1.4, 25.4, pale, 0, 14.4, qz));
  g.add(balustrade(37.4, 25.4, 1.8, pale, 0, 15.8, qz));
  g.add(box(12, 15.5, 3.0, pale, 0, 0.4, qz + 13));
  for (let i = 0; i < 4; i++) g.add(column(0.7, 7.0, pale, -4.2 + i * 2.8, 8.4, qz + 15.5, 8));
  g.add(box(12, 1.4, 3.0, pale, 0, 15.4, qz + 15.5));
  // the flanking colonnades to the east and west
  for (const sx of [-1, 1]) for (let i = 0; i < 10; i++)
    g.add(column(0.6, 6.0, pale, sx * (20 + i * 4.2), 0.4, qz, 8));
  for (const sx of [-1, 1]) g.add(box(42, 1.6, 3.4, pale, sx * 39, 6.4, qz));
  for (const zs of [1, -1]) for (let i = 0; i < 7; i++)
    g.add(box(2.2, 3.4, 0.6, dark, -14 + i * 4.7, 3.0, qz + zs * 12.1));
}

await exportGLB(g, OUT + 'greenwich_royal_naval_college.glb');
