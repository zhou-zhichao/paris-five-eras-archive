// A late Anglo-Saxon minster church of the kind rebuilt across London c.900-1050:
// tall narrow rubble-stone nave, small square-ended chancel, a square west tower
// with double belfry openings and long-and-short quoins.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x (west tower at -x, chancel at +x).  "Front" = +z is the south side,
// with the porch.
//
// True dimensions: nave + chancel about 25 x 9 m, west tower 18 m high.
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, hipRoof, group, THREE,
  profileWall, crenelRing,
} from './_lib_london.mjs';

const g = new THREE.Group();
const rubble = mat(0xc2b9a3), quoin = M.pale, dark = M.dark, thatch = M.thatch;
const shingle = mat(0x6b5a44), trim = M.medieval;

// ---- west tower
{
  const w = 6.4, h = 18;
  g.add(box(w, h, w, rubble, -9.3, 0, 0));
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])          // long-and-short quoins
    for (let i = 0; i < 9; i++)
      g.add(box(i % 2 ? 0.5 : 1.0, 1.9, i % 2 ? 1.0 : 0.5, quoin,
        -9.3 + a[0] * (w / 2 - 0.2), i * 2.0, a[1] * (w / 2 - 0.2)));
  // pilaster strips
  for (const s of [-1, 1]) {
    g.add(box(0.45, h, 0.35, quoin, -9.3 + s * 1.5, 0, w / 2));
    g.add(box(0.35, h, 0.45, quoin, -9.3 + s * w / 2, 0, s * 1.5));
  }
  // double belfry openings with a mid-wall baluster shaft
  for (const s of [-1, 1]) {
    g.add(box(2.4, 2.0, 0.4, dark, -9.3, 13.8, s * w / 2));
    g.add(box(0.4, 2.0, 2.4, dark, -9.3 + s * w / 2, 13.8, 0));
    g.add(cyl(0.2, 0.22, 2.0, quoin, -9.3, 13.8, s * (w / 2 + 0.05), 8));
    g.add(cyl(0.2, 0.22, 2.0, quoin, -9.3 + s * (w / 2 + 0.05), 13.8, 0, 8));
    g.add(box(1.0, 1.4, 0.4, dark, -9.3, 7.5, s * w / 2));
  }
  g.add(box(w + 0.9, 0.5, w + 0.9, quoin, -9.3, h, 0));
  g.add(hipRoof(w + 0.6, w + 0.6, 3.6, shingle, -9.3, h + 0.5, 0, 0.12));
  g.add(box(0.12, 1.8, 0.12, M.gold, -9.3, h + 4.1, 0));
  g.add(box(0.9, 0.12, 0.12, M.gold, -9.3, h + 5.4, 0));
}

// ---- nave
{
  const w = 14, d = 9, eaves = 8.5, ridge = 13.5;
  g.add(box(w, eaves, d, rubble, 0.5, 0, 0));
  g.add(gableRoof(w, d, ridge - eaves, shingle, 0.5, eaves, 0, true, 0.5));
  for (const s of [-1, 1]) for (const bx of [-4.5, 0, 4.5]) {
    g.add(box(1.1, 2.2, 0.4, dark, 0.5 + bx, 5.0, s * d / 2));      // small round-headed lights
    g.add(box(1.6, 0.5, 0.5, quoin, 0.5 + bx, 7.2, s * d / 2));
  }
  for (const s of [-1, 1]) for (const bx of [-6.8, -2.2, 2.2, 6.8])
    g.add(box(0.4, eaves, 0.3, quoin, 0.5 + bx, 0, s * d / 2));      // pilaster strips
}

// ---- chancel
{
  const w = 7.5, d = 6.5, eaves = 6.0, ridge = 9.6;
  g.add(box(w, eaves, d, rubble, 11.3, 0, 0));
  g.add(gableRoof(w, d, ridge - eaves, shingle, 11.3, eaves, 0, true, 0.45));
  g.add(profileWall([[-d / 2, 0], [d / 2, 0], [0, ridge - eaves]], 0.6, rubble, 15.05, eaves, 0, Math.PI / 2));
  g.add(box(0.4, 2.6, 1.2, dark, 15.15, 2.6, 0));                    // east window
  for (const s of [-1, 1]) g.add(box(1.0, 2.0, 0.4, dark, 11.3, 2.8, s * d / 2));
}

// ---- south porch (+z) and a small porticus on the north
g.add(box(4.0, 5.0, 3.4, rubble, -1.5, 0, 6.2));
g.add(gableRoof(4.0, 3.4, 2.2, shingle, -1.5, 5.0, 6.2, true, 0.35));
g.add(box(1.5, 3.2, 0.5, dark, -1.5, 0, 7.9));
g.add(box(4.6, 5.0, 3.6, rubble, 4.5, 0, -6.3));
g.add(gableRoof(4.6, 3.6, 2.3, shingle, 4.5, 5.0, -6.3, true, 0.35));

await exportGLB(g, out('saxon_church'));
