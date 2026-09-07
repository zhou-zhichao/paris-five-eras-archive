// Palace of Westminster (Barry & Pugin, 1840-1876).  Perpendicular Gothic, Anston stone.
// Orientation: long axis along X.  RIVER FRONT (265 m, Thames) faces +Z.
// North end = -X (Elizabeth Tower / Big Ben, 96 m), south end = +X (Victoria Tower, 98.5 m).
// Central Tower (octagonal spire) 91 m over the central lobby.  Westminster Hall on the west (-Z).
// Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, prism, gableRoof, THREE,
  P, M, pinnacle, balustrade, parapet, openWall, arcade, OUT } from './_lib_wren_edwardian.mjs';

const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate),
  lead = M(P.lead), gold = M(P.gold), iron = M(P.iron), dark = M(0x494236), glass = M(P.glass);
const g = new THREE.Group();

const L = 265;                 // river front length
const ZR = 46;                 // river front outer face
const ZW = -44;                // west range outer face

// ---------------------------------------------------------------- helpers
// slim octagonal turret with a spirelet, y = bottom
function turret(r, h, spire, x, y, z, m = pale, ms = lead) {
  const t = new THREE.Group();
  t.add(cyl(r, r * 1.08, h, m, 0, 0, 0, 8));
  t.add(cyl(r * 1.25, r * 1.25, 0.9, m, 0, h - 0.9, 0, 8));
  t.add(cone(r * 1.2, spire, ms, 0, h, 0, 8));
  t.position.set(x, y, z);
  return t;
}
// a row of pinnacles along x
function pinRow(n, x0, x1, y, z, r = 1.0, h = 4.5) {
  const grp = new THREE.Group();
  for (let i = 0; i < n; i++) grp.add(pinnacle(r, h, pale, x0 + (x1 - x0) * i / (n - 1), y, z, 6));
  return grp;
}
// band of pointed (dark) window openings on a +z / -z facade
function gothicWindows(n, x0, x1, w, h, y, z, t = 0.5) {
  const grp = new THREE.Group();
  for (let i = 0; i < n; i++) {
    const x = x0 + (x1 - x0) * i / (n - 1);
    grp.add(box(w, h, t, dark, x, y, z));
    grp.add(cone(w * 0.72, w * 0.75, dark, x, y + h, z, 6));
  }
  return grp;
}

// ---------------------------------------------------------------- terrace & plinth
g.add(box(L + 4, 3.0, 10, dk, 0, 0, ZR + 5));            // river terrace
g.add(box(L + 2, 4.0, ZR - ZW + 2, dk, 0, 0, (ZR + ZW) / 2));

// ---------------------------------------------------------------- river front range (265 m)
{
  const D = 22, zc = ZR - D / 2;
  g.add(box(L, 23, D, st, 0, 4, zc));                       // main wall 4 storeys -> 27 m
  g.add(box(L + 1.5, 1.8, D + 1.5, pale, 0, 27, zc));       // cornice
  g.add(box(L, 3.0, D, pale, 0, 28.8, zc));                 // pierced parapet
  g.add(gableRoof(L - 2, D - 3, 7.5, slate, 0, 31.8, zc, true, 0.4));
  // 3 tiers of pointed window bands
  for (const zz of [ZR + 0.1, ZR - D - 0.1]) {
    g.add(gothicWindows(34, -L / 2 + 6, L / 2 - 6, 3.2, 5.2, 7.5, zz));
    g.add(gothicWindows(34, -L / 2 + 6, L / 2 - 6, 3.2, 4.8, 15.5, zz));
    g.add(gothicWindows(34, -L / 2 + 6, L / 2 - 6, 3.0, 4.0, 22.0, zz));
  }
  // bay-division turrets along the river front
  for (let i = 0; i < 12; i++) {
    const x = -L / 2 + 4 + i * (L - 8) / 11;
    g.add(turret(2.0, 34, 7.0, x, 4, ZR + 1.0));
    g.add(turret(1.6, 32, 5.5, x, 4, ZR - D - 1.0));
  }
  // pinnacle rank on the parapet
  g.add(pinRow(23, -L / 2 + 6, L / 2 - 6, 31.8, ZR - 1.5, 0.9, 4.2));
  g.add(pinRow(23, -L / 2 + 6, L / 2 - 6, 31.8, ZR - D + 1.5, 0.9, 4.2));
  // three projecting pavilions
  for (const px of [-72, 0, 72]) {
    g.add(box(26, 25, 5, st, px, 4, ZR + 2.5));
    g.add(box(27, 1.8, 6, pale, px, 29, ZR + 2.5));
    g.add(gableRoof(24, 6, 5, slate, px, 30.8, ZR + 2.5, true, 0.3));
    g.add(turret(2.2, 38, 8, px - 13.5, 4, ZR + 2.5));
    g.add(turret(2.2, 38, 8, px + 13.5, 4, ZR + 2.5));
  }
}

// ---------------------------------------------------------------- west range (-z front)
{
  const D = 18, zc = ZW + D / 2;
  g.add(box(210, 21, D, st, -6, 4, zc));
  g.add(box(211, 1.6, D + 1.4, pale, -6, 25, zc));
  g.add(box(210, 2.6, D, pale, -6, 26.6, zc));
  g.add(gableRoof(208, D - 3, 6.5, slate, -6, 29.2, zc, true, 0.4));
  g.add(gothicWindows(26, -105, 96, 3.0, 5.0, 7.5, ZW - 0.1));
  g.add(gothicWindows(26, -105, 96, 3.0, 4.6, 15.5, ZW - 0.1));
  for (let i = 0; i < 8; i++) g.add(turret(1.8, 31, 6, -105 + i * 29, 4, ZW - 1.0));
  g.add(pinRow(18, -104, 95, 29.2, ZW + 1.5, 0.85, 4.0));
}

// ---------------------------------------------------------------- cross ranges / courts
for (const cx of [-95, -50, 45, 92]) {
  g.add(box(15, 20, ZR - ZW - 30, st, cx, 4, (ZR + ZW) / 2));
  g.add(gableRoof(13, ZR - ZW - 32, 5.5, slate, cx, 24, (ZR + ZW) / 2, true, 0.3));
}
// central spine to the central lobby
g.add(box(70, 20, 16, st, 0, 4, 0));
g.add(gableRoof(68, 15, 5.5, slate, 0, 24, 0, true, 0.3));
g.add(box(16, 20, 70, st, 0, 4, 4));
g.add(gableRoof(15, 68, 5.5, slate, 0, 24, 4, false, 0.3));

// ---------------------------------------------------------------- WESTMINSTER HALL (west side, north)
{
  const hx = -52, hz = -22;
  g.add(box(73, 20, 21, dk, hx, 3, hz));                    // 73.2 x 20.7 m
  g.add(box(74, 1.4, 22, pale, hx, 23, hz));
  g.add(gableRoof(73, 21, 9.5, lead, hx, 24.4, hz, true, 0.6));   // ridge ~34 m
  for (let i = 0; i < 8; i++) {                              // buttresses
    const x = hx - 31.5 + i * 9;
    g.add(box(2.2, 21, 2.4, pale, x, 3, hz + 11.2));
    g.add(box(2.2, 21, 2.4, pale, x, 3, hz - 11.2));
    g.add(box(3.4, 9, 0.6, dark, x + 4.5, 9, hz + 10.6));
    g.add(box(3.4, 9, 0.6, dark, x + 4.5, 9, hz - 10.6));
  }
  // north porch of the hall
  g.add(box(18, 26, 6, pale, hx - 36 + 3, 3, hz));
  g.add(turret(2.4, 34, 7, hx - 36, 3, hz + 10));
  g.add(turret(2.4, 34, 7, hx - 36, 3, hz - 10));
  g.add(cyl(0.9, 0.9, 3.5, lead, hx, 33.9, hz, 8));          // louvre on the ridge
}

// ---------------------------------------------------------------- CENTRAL TOWER (91 m)
{
  g.add(box(30, 26, 30, st, 0, 4, 0));
  g.add(box(31.5, 1.8, 31.5, pale, 0, 30, 0));
  g.add(cyl(13.5, 14.5, 16, st, 0, 31.8, 0, 8));             // octagonal lantern
  for (let i = 0; i < 8; i++) {
    const a = (i + 0.5) / 8 * Math.PI * 2;
    g.add(box(3.4, 9, 0.7, dark, Math.cos(a) * 13.2, 35, Math.sin(a) * 13.2));
  }
  g.add(cyl(15.5, 15.5, 2.0, pale, 0, 47.8, 0, 8));
  g.add(cyl(11.5, 12.5, 8, st, 0, 49.8, 0, 8));
  g.add(cyl(13.0, 13.0, 1.6, pale, 0, 57.8, 0, 8));
  for (let i = 0; i < 8; i++) {
    const a = i / 8 * Math.PI * 2;
    g.add(pinnacle(1.3, 6.5, pale, Math.cos(a) * 12.4, 57.8, Math.sin(a) * 12.4, 6));
  }
  g.add(cone(11.5, 29, lead, 0, 58.5, 0, 8));                // spire to ~88
  g.add(cyl(0.5, 0.7, 3.0, gold, 0, 87.5, 0, 6));
  g.add(cone(1.0, 1.5, gold, 0, 90.0, 0, 6));
}

// ---------------------------------------------------------------- ELIZABETH TOWER (Big Ben) 96 m
{
  const tx = -L / 2 + 7, tz = ZR - 7;
  const T = new THREE.Group();
  T.add(box(14.5, 6, 14.5, dk, 0, 0, 0));
  T.add(box(12.6, 42, 12.6, st, 0, 6, 0));                   // shaft
  for (let s = 0; s < 5; s++) for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 3.2, 5.0, dz ? 0.6 : 3.2, dark, dx * 6.4, 9 + s * 7.5, dz * 6.4));
  T.add(box(13.6, 1.5, 13.6, pale, 0, 48, 0));
  // clock stage with four 7 m dials
  T.add(box(13.2, 10, 13.2, pale, 0, 49.5, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const d = new THREE.Mesh(new THREE.CylinderGeometry(3.5, 3.5, 0.9, 20), M(0xe8e4d8));
    if (dz) d.rotation.x = Math.PI / 2; else d.rotation.z = Math.PI / 2;
    d.position.set(dx * 6.9, 54.5, dz * 6.9); T.add(d);
    const r2 = new THREE.Mesh(new THREE.CylinderGeometry(4.0, 4.0, 0.7, 20), gold);
    if (dz) r2.rotation.x = Math.PI / 2; else r2.rotation.z = Math.PI / 2;
    r2.position.set(dx * 6.7, 54.5, dz * 6.7); T.add(r2);
  }
  T.add(box(14.4, 1.6, 14.4, pale, 0, 59.5, 0));
  // belfry
  T.add(box(12.0, 10, 12.0, st, 0, 61.1, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 6.0, 8.0, dz ? 0.6 : 6.0, dark, dx * 6.1, 62, dz * 6.1));
  T.add(box(13.4, 1.4, 13.4, pale, 0, 71.1, 0));
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    T.add(pinnacle(1.5, 9.0, pale, dx * 5.6, 71.1, dz * 5.6, 6));
  // cast-iron spire to 96 m
  T.add(cyl(4.6, 5.8, 5.0, lead, 0, 72.5, 0, 8));
  T.add(cone(5.2, 13.5, lead, 0, 77.5, 0, 8));
  T.add(cyl(1.4, 1.8, 2.4, gold, 0, 91.0, 0, 8));
  T.add(cone(1.4, 2.6, gold, 0, 93.4, 0, 8));
  T.position.set(tx, 0, tz);
  g.add(T);
}

// ---------------------------------------------------------------- VICTORIA TOWER 98.5 m
{
  const tx = L / 2 - 14, tz = 6;
  const T = new THREE.Group();
  T.add(box(26, 5, 26, dk, 0, 0, 0));
  T.add(box(22.6, 70, 22.6, st, 0, 5, 0));
  // 5 tiers of tall pointed windows on each face
  for (let s = 0; s < 6; s++) {
    const yy = 10 + s * 11;
    for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
      for (const o of [-6, 0, 6]) {
        T.add(box(dx ? 0.6 : 3.6, 7.0, dz ? 0.6 : 3.6, dark, dx * 11.4 + (dx ? 0 : o), yy, dz * 11.4 + (dz ? 0 : o)));
      }
    }
  }
  // corner turrets running the full height
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    T.add(turret(2.6, 82, 12, dx * 11.6, 5, dz * 11.6));
  T.add(box(24.5, 2.0, 24.5, pale, 0, 75, 0));
  // arcaded crown stage
  T.add(box(21.0, 9, 21.0, pale, 0, 77, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 15, 7.0, dz ? 0.6 : 15, dark, dx * 10.6, 78, dz * 10.6));
  T.add(box(23.0, 2.0, 23.0, pale, 0, 86, 0));
  // cast-iron pyramid roof + flagstaff to 98.5 m
  T.add(cone(15.0, 8.5, iron, 0, 88, 0, 4));
  T.add(cyl(0.45, 0.45, 5.0, iron, 0, 93.5, 0, 6));
  T.add(box(4.5, 2.6, 0.25, M(0xc23b3b), 2.4, 95.5, 0));
  T.position.set(tx, 0, tz);
  g.add(T);
}

// ---------------------------------------------------------------- St Stephen's porch / lower blocks
g.add(box(24, 22, 20, st, -52, 4, -40));
g.add(gableRoof(22, 18, 6, slate, -52, 26, -40, true, 0.4));

await exportGLB(g, OUT + 'palace_of_westminster.glb');
