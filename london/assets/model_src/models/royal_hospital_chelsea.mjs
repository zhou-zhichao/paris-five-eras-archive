// The Royal Hospital, Chelsea, Sir Christopher Wren 1682-92.  Red brick with Portland dressings.
// Orientation: the great three-sided FIGURE COURT opens to the river (+Z); the central range
// with its Doric portico, pediment and octagonal lantern closes it at -Z.
// Overall ~ 210 x 130 m.  Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, hipRoof, THREE,
  P, M, column, colonnade, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const bk = M(0x9a5a48), pale = M(P.pale), st = M(P.stone), dk = M(P.dstone),
  slate = M(P.slate), lead = M(P.lead), dark = M(0x40382e), grav = M(0xa89b82), grass = M(P.grass);

const H = 15;                 // three storeys to the cornice
g.add(box(214, 0.4, 140, grav, 0, 0, 0));
g.add(box(140, 0.5, 90, grass, 0, 0.4, 30));

// ---------------------------------------------------------------- the three ranges of the Figure Court
function range(w, d, x, z) {
  g.add(box(w, H, d, bk, x, 0.4, z));
  g.add(box(w + 1.4, 1.4, d + 1.4, pale, x, 0.4 + H, z));
  g.add(hipRoof(w - 2, d - 2, 5.5, slate, x, 1.8 + H, z, 0.55));
  // dormer row
  const n = Math.max(3, Math.round(w / 7));
  for (let i = 0; i < n; i++) {
    const xx = x - w / 2 + 4 + i * (w - 8) / (n - 1);
    g.add(box(2.4, 2.8, 3.0, slate, xx, 1.8 + H, z + d / 2 - 3.2));
    g.add(box(2.4, 2.8, 3.0, slate, xx, 1.8 + H, z - d / 2 + 3.2));
  }
  // windows
  for (const zs of [1, -1]) for (let i = 0; i < n * 2; i++) {
    const xx = x - w / 2 + 3 + i * (w - 6) / (n * 2 - 1);
    for (const y of [2.6, 7.6, 12.0]) g.add(box(1.8, 2.8, 0.6, dark, xx, y, z + zs * (d / 2 + 0.1)));
  }
  for (const sx of [-1, 1]) {
    const m = Math.max(2, Math.round(d / 5));
    for (let i = 0; i < m; i++) {
      const zz = z - d / 2 + 3 + i * (d - 6) / (m - 1);
      for (const y of [2.6, 7.6, 12.0]) g.add(box(0.6, 2.8, 1.8, dark, x + sx * (w / 2 + 0.1), y, zz));
    }
  }
}
range(112, 22, 0, -46);                        // central range (chapel + hall), closes the court
range(22, 84, -45, 7);                          // west wing
range(22, 84, 45, 7);                           // east wing

// ---------------------------------------------------------------- central portico + lantern
{
  const CZ = -46;
  g.add(box(26, H + 3, 26, bk, 0, 0.4, CZ));
  g.add(box(27.4, 1.6, 27.4, pale, 0, 0.4 + H + 3, CZ));
  for (let i = 0; i < 4; i++) g.add(column(1.1, 12.0, pale, -7.2 + i * 4.8, 0.4, CZ + 14.5, 10));
  g.add(box(24, 2.6, 4.4, pale, 0, 12.4, CZ + 14.5));
  g.add(pediment(24, 4.6, 4.4, pale, 0, 15.0, CZ + 14.5));
  // octagonal lantern with a lead cupola
  g.add(box(15, 3.0, 15, pale, 0, 20.0, CZ));
  g.add(cyl(5.2, 5.6, 6.5, pale, 0, 23.0, CZ, 8));
  for (let i = 0; i < 8; i++) {
    const a = (i + 0.5) / 8 * Math.PI * 2;
    g.add(box(2.0, 4.2, 0.6, dark, Math.cos(a) * 5.3, 24.2, CZ + Math.sin(a) * 5.3));
  }
  g.add(cyl(6.6, 6.6, 1.0, pale, 0, 29.5, CZ, 8));
  g.add(lathe([[5.2, 0], [4.9, 1.2], [3.9, 2.6], [2.4, 3.8], [1.0, 4.5], [0, 4.8]], lead, 0, 30.5, CZ, 8));
  g.add(cyl(0.9, 1.2, 1.6, pale, 0, 35.3, CZ, 8));
  g.add(cone(1.0, 1.8, lead, 0, 36.9, CZ, 8));
  g.add(cyl(0.18, 0.18, 1.6, M(P.gold), 0, 38.7, CZ, 6));
}

// ---------------------------------------------------------------- colonnade round the inner court
for (let i = 0; i < 22; i++) {
  const x = -52 + i * 4.95;
  g.add(column(0.7, 5.0, pale, x, 0.4, -34.5, 8));
}
g.add(box(108, 1.4, 3.2, pale, 0, 5.4, -34.5));

// ---------------------------------------------------------------- pavilions at the river ends
for (const sx of [-1, 1]) {
  const px = sx * 45;
  g.add(box(26, H + 4, 26, bk, px, 0.4, 44));
  g.add(box(27.4, 1.6, 27.4, pale, px, 0.4 + H + 4, 44));
  g.add(hipRoof(26, 26, 6.0, slate, px, 2.0 + H + 4, 44, 0.25));
  for (let i = 0; i < 4; i++) g.add(column(0.95, 11.0, pale, px - 6.3 + i * 4.2, 0.4, 57.5, 10));
  g.add(box(23, 2.2, 4.0, pale, px, 11.4, 57.5));
  g.add(pediment(23, 4.0, 4.0, pale, px, 13.6, 57.5));
}

await exportGLB(g, OUT + 'royal_hospital_chelsea.glb');
