// The Imperial Institute, Thomas Edward Collcutt 1893 (demolished 1957 except the tower).
// Free Renaissance, Portland stone; a 210 m front with the copper-domed Queen's Tower (85 m)
// at its centre and two smaller towers flanking.
// Orientation: long axis along X, the FRONT faces +Z.  Ground y=0, centred on the origin.
// Also exports queens_tower.glb -- the surviving tower on its own, centred on the origin.
import { exportGLB, box, cyl, cone, lathe, gableRoof, hipRoof, THREE,
  P, M, column, ringColonnade, pediment, balustrade, pinnacle, OUT } from './_lib_wren_edwardian.mjs';

const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), cop = M(P.copper), gold = M(P.gold), dark = M(0x4a463d);

// ---------------------------------------------------------------- the Queen's Tower, 85 m
function queensTower() {
  const T = new THREE.Group();
  T.add(box(17, 2.0, 17, dk, 0, 0, 0));
  T.add(box(14.5, 40, 14.5, st, 0, 2.0, 0));                     // shaft
  for (let s = 0; s < 5; s++) {
    T.add(box(15.2, 0.9, 15.2, pale, 0, 8 + s * 7.5, 0));
    for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
      T.add(box(dx ? 0.6 : 3.0, 4.4, dz ? 0.6 : 3.0, dark, dx * 7.4, 10 + s * 7.5, dz * 7.4));
  }
  T.add(box(16.4, 1.6, 16.4, pale, 0, 42.0, 0));
  // the arcaded stage
  T.add(box(13.6, 10, 13.6, st, 0, 43.6, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.7 : 9.0, 7.0, dz ? 0.7 : 9.0, dark, dx * 6.9, 45.0, dz * 6.9));
  T.add(box(15.6, 1.8, 15.6, pale, 0, 53.6, 0));
  T.add(balustrade(15.6, 15.6, 2.0, pale, 0, 55.4, 0));
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    T.add(cyl(1.1, 1.3, 4.0, pale, dx * 6.6, 57.4, dz * 6.6, 8));
  // circular colonnaded drum
  T.add(cyl(5.4, 5.8, 8.5, st, 0, 57.4, 0, 16));
  T.add(ringColonnade(12, 6.8, 0.52, 8.5, pale, 0, 57.4, 0, 6));
  T.add(cyl(8.0, 8.0, 1.4, pale, 0, 65.9, 0, 16));
  T.add(cyl(7.6, 7.6, 1.2, pale, 0, 67.3, 0, 16));
  // copper dome + lantern + gold finial (85 m)
  T.add(lathe([[6.4, 0], [6.2, 1.2], [5.6, 2.8], [4.6, 4.4], [3.2, 5.8], [1.6, 6.7], [0, 7.0]],
    cop, 0, 68.5, 0, 16));
  T.add(cyl(1.8, 2.2, 3.0, pale, 0, 75.5, 0, 10));
  T.add(cyl(2.6, 2.6, 0.8, pale, 0, 78.5, 0, 10));
  T.add(lathe([[2.2, 0], [1.9, 1.0], [1.2, 2.0], [0.5, 2.7], [0, 3.0]], cop, 0, 79.3, 0, 10));
  T.add(cyl(0.85, 1.05, 1.2, gold, 0, 82.3, 0, 8));
  T.add(cone(0.9, 1.6, gold, 0, 83.5, 0, 8));
  return T;
}

// =========================================================== the whole Institute
{
  const g = new THREE.Group();
  const W = 210, FD = 22, H = 22, FZ = 34;
  g.add(box(W + 4, 1.4, FD + 4, dk, 0, 0, FZ - FD / 2));
  g.add(box(W, H, FD, st, 0, 1.4, FZ - FD / 2));
  g.add(box(W + 1.6, 1.6, FD + 1.6, pale, 0, 1.4 + H, FZ - FD / 2));
  g.add(box(W - 2, 6.5, FD - 3, slate, 0, 3.0 + H, FZ - FD / 2));       // mansard attic
  g.add(box(W - 8, 1.0, FD - 8, lead, 0, 9.5 + H, FZ - FD / 2));
  // window tiers and pilaster strips
  for (const zz of [FZ + 0.1, FZ - FD - 0.1]) for (let i = 0; i < 42; i++) {
    const x = -W / 2 + 4 + i * (W - 8) / 41;
    if (Math.abs(x) < 15) continue;
    g.add(box(2.2, 4.2, 0.6, dark, x, 4.0, zz));
    g.add(box(2.2, 3.8, 0.6, dark, x, 11.0, zz));
    g.add(box(2.0, 3.0, 0.6, dark, x, 17.5, zz));
    g.add(box(1.3, H - 1, 0.9, pale, x + (W - 8) / 82, 1.4, zz));
  }
  for (let i = 0; i < 11; i++) {                        // dormers in the mansard
    const x = -W / 2 + 12 + i * (W - 24) / 10;
    g.add(box(3.0, 3.4, 3.0, slate, x, 3.0 + H, FZ - 4));
    g.add(box(2.2, 2.2, 0.5, dark, x, 3.8 + H, FZ - 2.6));
  }
  // wings running back
  for (const sx of [-1, 1]) {
    g.add(box(22, 20, 54, st, sx * 78, 1.4, FZ - FD - 27));
    g.add(gableRoof(22, 54, 7.0, slate, sx * 78, 21.4, FZ - FD - 27, false, 0.4));
  }
  g.add(box(60, 20, 46, st, 0, 1.4, FZ - FD - 23));
  g.add(gableRoof(60, 46, 8.0, slate, 0, 21.4, FZ - FD - 23, true, 0.4));

  // central pavilion under the tower
  g.add(box(34, H + 6, FD + 8, st, 0, 1.4, FZ - FD / 2 + 2));
  g.add(box(35.6, 1.8, FD + 9.6, pale, 0, 1.4 + H + 6, FZ - FD / 2 + 2));
  for (let i = 0; i < 4; i++) g.add(column(1.0, 12.0, pale, -6.6 + i * 4.4, 1.4, FZ + 4.0, 10));
  g.add(box(22, 2.4, 4.0, pale, 0, 13.4, FZ + 4.0));
  g.add(pediment(22, 4.0, 4.0, pale, 0, 15.8, FZ + 4.0));

  // the Queen's Tower rising over the centre
  const T = queensTower(); T.position.set(0, 0, FZ - 12); g.add(T);

  // the two smaller flanking towers (~55 m)
  for (const sx of [-1, 1]) {
    const t = new THREE.Group();
    t.add(box(12, 34, 12, st, 0, 1.4, 0));
    for (let s = 0; s < 4; s++) for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
      t.add(box(dx ? 0.6 : 2.6, 4.0, dz ? 0.6 : 2.6, dark, dx * 6.1, 7 + s * 7.5, dz * 6.1));
    t.add(box(13.4, 1.4, 13.4, pale, 0, 35.4, 0));
    t.add(box(11.0, 6.5, 11.0, st, 0, 36.8, 0));
    t.add(box(12.6, 1.4, 12.6, pale, 0, 43.3, 0));
    t.add(cyl(4.2, 4.6, 3.0, st, 0, 44.7, 0, 12));
    t.add(cyl(5.4, 5.4, 1.0, pale, 0, 47.7, 0, 12));
    t.add(lathe([[4.4, 0], [4.1, 1.2], [3.2, 2.6], [1.9, 3.8], [0, 4.4]], cop, 0, 48.7, 0, 12));
    t.add(cyl(0.35, 0.35, 2.0, gold, 0, 53.1, 0, 6));
    t.position.set(sx * 74, 0, FZ - 11);
    g.add(t);
  }
  await exportGLB(g, OUT + 'imperial_institute.glb');
}

// =========================================================== the tower on its own
{
  const g = new THREE.Group();
  g.add(queensTower());
  await exportGLB(g, OUT + 'queens_tower.glb');
}
