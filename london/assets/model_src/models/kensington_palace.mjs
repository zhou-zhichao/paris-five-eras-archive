// Kensington Palace: the Jacobean house remodelled by Wren from 1689 and extended by
// Colen Campbell / William Kent in the 1720s.  Plain red brick with stone dressings,
// low ranges around Clock Court and Princesses Court; ~120 x 100 m.
// Orientation: long axis along X; the east front (to the gardens) faces +Z, the clock
// tower rising over the archway into the courts.  Ground y=0, centred on the origin.
import { exportGLB, box, cyl, cone, lathe, hipRoof, THREE,
  P, M, column, pediment, balustrade, openWall, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const bk = M(0x9a5a48), bkd = M(0x86493a), pale = M(P.pale), dk = M(P.dstone),
  slate = M(P.slate), lead = M(P.lead), dark = M(0x40382e), grav = M(0xa89b82), gold = M(P.gold);

const H = 13;
g.add(box(126, 0.4, 106, grav, 0, 0, 0));

function range(w, d, x, z, h = H, dorm = true) {
  g.add(box(w, h, d, bk, x, 0.4, z));
  g.add(box(w + 1.2, 1.2, d + 1.2, pale, x, 0.4 + h, z));
  g.add(hipRoof(w - 2, d - 2, 4.8, slate, x, 1.6 + h, z, 0.55));
  const n = Math.max(3, Math.round(w / 6));
  if (dorm) for (let i = 0; i < n; i++) {
    const xx = x - w / 2 + 3.5 + i * (w - 7) / (n - 1);
    g.add(box(2.0, 2.4, 2.6, slate, xx, 1.6 + h, z + d / 2 - 2.8));
    g.add(box(2.0, 2.4, 2.6, slate, xx, 1.6 + h, z - d / 2 + 2.8));
  }
  for (const zs of [1, -1]) for (let i = 0; i < n * 2; i++) {
    const xx = x - w / 2 + 2.5 + i * (w - 5) / (n * 2 - 1);
    for (const y of [2.4, 7.2]) g.add(box(1.7, 2.8, 0.6, dark, xx, y, z + zs * (d / 2 + 0.1)));
    if (h > 12) g.add(box(1.5, 2.2, 0.6, dark, xx, 11.0, z + zs * (d / 2 + 0.1)));
  }
  for (const sx of [-1, 1]) {
    const m = Math.max(2, Math.round(d / 6));
    for (let i = 0; i < m; i++) {
      const zz = z - d / 2 + 3 + i * (d - 6) / (m - 1);
      for (const y of [2.4, 7.2]) g.add(box(0.6, 2.8, 1.7, dark, x + sx * (w / 2 + 0.1), y, zz));
    }
  }
}

// ---------------------------------------------------------------- the ranges round two courts
range(120, 20, 0, 40);                  // east (garden) front
range(120, 18, 0, -41);                 // west front
range(18, 62, -51, 0);                  // north range
range(18, 62, 51, 0);                   // south range
range(16, 62, 0, 0);                    // spine between Clock Court and Princesses Court

// the King's Gallery / Kent's south-east block, a taller pedimented pavilion
{
  const px = 40, pz = 40;
  g.add(box(28, H + 4, 24, bk, px, 0.4, pz));
  g.add(box(29.4, 1.4, 25.4, pale, px, 0.4 + H + 4, pz));
  g.add(hipRoof(28, 24, 5.5, slate, px, 1.8 + H + 4, pz, 0.35));
  for (let i = 0; i < 6; i++) g.add(box(1.6, H + 2, 1.0, pale, px - 10 + i * 4, 0.4, pz + 12.2));
  g.add(box(20, 1.4, 2.2, pale, px, 0.4 + H + 4, pz + 12.2));
  g.add(pediment(20, 3.8, 2.2, pale, px, 1.8 + H + 4, pz + 12.2));
}

// ---------------------------------------------------------------- the clock tower over the archway
{
  const tx = -14, tz = 0;
  g.add(openWall(14, H, 16, bk, [{ cx: 0, y0: 0, w: 4.2, h: 4.0, arch: true }], tx, 0.4, tz, 10));
  const T = new THREE.Group();
  T.add(box(13, H + 4, 15, bk, 0, 0.4, 0));
  T.add(box(14.2, 1.2, 16.2, pale, 0, 0.4 + H + 4, 0));
  T.add(box(10.5, 5.5, 10.5, bk, 0, 1.6 + H + 4, 0));          // clock stage
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const d = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 2.0, 0.7, 16), M(0xe8e4d8));
    if (dz) d.rotation.x = Math.PI / 2; else d.rotation.z = Math.PI / 2;
    d.position.set(dx * 5.4, 4.4 + H + 4, dz * 5.4); T.add(d);
  }
  T.add(box(11.8, 1.2, 11.8, pale, 0, 7.1 + H + 4, 0));
  T.add(cyl(3.6, 4.0, 4.5, pale, 0, 8.3 + H + 4, 0, 8));       // open lantern
  for (let i = 0; i < 8; i++) {
    const a = (i + 0.5) / 8 * Math.PI * 2;
    T.add(box(1.5, 3.0, 0.6, dark, Math.cos(a) * 3.8, 9.1 + H + 4, Math.sin(a) * 3.8));
  }
  T.add(cyl(4.8, 4.8, 0.9, pale, 0, 12.8 + H + 4, 0, 8));
  T.add(lathe([[3.8, 0], [3.5, 1.0], [2.6, 2.2], [1.4, 3.1], [0, 3.5]], lead, 0, 13.7 + H + 4, 0, 8));
  T.add(cyl(0.18, 0.18, 2.0, gold, 0, 17.2 + H + 4, 0, 6));
  T.position.set(tx, 0, tz);
  g.add(T);
}

await exportGLB(g, OUT + 'kensington_palace.glb');
