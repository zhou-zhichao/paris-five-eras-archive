// Lambeth Palace, the London house of the archbishops of Canterbury: Morton's
// red-brick gatehouse of 1490, the Great Hall, the 13th-century chapel and the
// Lollards' Tower on the riverside.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x.  "Front" = +z is the RIVER (Thames) side; Morton's Tower faces the
// road at -z.
//
// True dimensions: precinct about 110 x 80 m; Morton's Tower twin towers ~22 m;
// Great Hall ~30 x 12 m; Lollards' Tower ~18 m.
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, hipRoof, lathe, group, THREE,
  wall, archPath, crenel, crenelRing, turret, pinnacle, profileWall,
} from './_lib_london.mjs';

const g = new THREE.Group();
const brick = M.brick, brick2 = M.tudor, rag = M.rag, med = M.medieval, pale = M.pale;
const lead = M.lead, dark = M.dark, tile = M.tile, port = M.portland;

// ---------------------------------------------------------------- Morton's Tower (1490)
{
  const gx = -30, gz = -34;
  g.add(wall(11, 15, 9, brick, [archPath(0, 4.4, 0, 4.0, 3.0, 1, 8)], gx, 0, gz));
  g.add(box(11.6, 1.0, 9.6, port, gx, 15, gz));
  g.add(crenelRing(11.6, 9.6, 0.8, port, gx, 16, gz, 1.3, 1.3, 1.1));
  for (const s of [-1, 1]) {
    const tx = gx + s * 7.5;
    g.add(box(9.0, 21, 10.5, brick, tx, 0, gz));
    // diaper pattern of darker headers
    for (let i = 0; i < 7; i++) for (let j = 0; j < 4; j++) {
      if ((i + j) % 2) continue;
      g.add(box(0.9, 0.9, 0.25, brick2, tx - 3.2 + j * 2.1, 2.0 + i * 2.4, gz - 5.35));
    }
    for (const f of [0.22, 0.42, 0.62, 0.82]) {
      g.add(box(3.0, 2.0, 0.4, dark, tx, 21 * f, gz - 5.3));
      g.add(box(3.0, 2.0, 0.4, dark, tx, 21 * f, gz + 5.3));
      g.add(box(0.4, 2.0, 3.0, dark, tx + s * 4.5, 21 * f, gz));
    }
    g.add(box(9.8, 1.0, 11.3, port, tx, 21, gz));
    g.add(crenelRing(9.8, 11.3, 0.8, port, tx, 22, gz, 1.4, 1.4, 1.2));
    for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
      g.add(cyl(1.1, 1.2, 3.0, brick, tx + a[0] * 4.4, 22, gz + a[1] * 5.2, 8));
  }
  // flanking walls with the outer court
  for (const s of [-1, 1]) {
    g.add(box(26, 8.5, 3.0, brick, gx + s * 25, 0, gz));
    g.add(crenel(26, 1.4, port, gx + s * 25, 8.5, gz, true, 1.2, 1.3, 1.1));
  }
}

// ---------------------------------------------------------------- Great Hall
{
  const cx = -18, cz = 2, w = 32, d = 13, eaves = 12, ridge = 19;
  g.add(box(w, eaves, d, rag, cx, 0, cz));
  g.add(box(w + 0.8, 0.8, d + 0.8, med, cx, eaves - 0.8, cz));
  g.add(gableRoof(w, d, ridge - eaves, lead, cx, eaves, cz, true, 0.6));
  for (let i = 0; i < 5; i++) for (const s of [-1, 1]) {
    g.add(box(2.8, 6.5, 0.45, dark, cx - 12 + i * 6, 4.2, cz + s * d / 2));
    g.add(box(0.3, 6.5, 0.55, med, cx - 12 + i * 6, 4.2, cz + s * (d / 2 + 0.05)));
  }
  for (let i = 0; i <= 5; i++) for (const s of [-1, 1])
    g.add(box(1.2, eaves + 0.8, 1.6, med, cx - 15 + i * 6, 0, cz + s * (d / 2 + 0.6)));
  // the louvre over the hearth and the gable ends
  g.add(box(3.4, 2.6, 3.4, med, cx + 2, ridge - 1.0, cz));
  g.add(lathe([[2.4, 0], [2.6, 0.8], [1.6, 2.6], [0.6, 4.2], [0.18, 5.2]], lead, cx + 2, ridge + 1.6, cz, 8));
  for (const s of [-1, 1]) {
    g.add(profileWall([[-d / 2, 0], [d / 2, 0], [0, ridge - eaves]], 1.0, rag, cx + s * w / 2, eaves, cz, Math.PI / 2));
    g.add(box(0.5, 6.0, 6.0, dark, cx + s * (w / 2 + 0.15), 4.0, cz));
  }
  // the porch, on to the outer court
  g.add(box(5.0, 8.0, 4.0, med, cx - 4, 0, cz - d / 2 - 2.0));
  g.add(gableRoof(5.0, 4.0, 2.6, lead, cx - 4, 8.0, cz - d / 2 - 2.0, true, 0.4));
  g.add(box(2.4, 4.4, 0.5, dark, cx - 4, 0, cz - d / 2 - 3.9));
}

// ---------------------------------------------------------------- chapel + Lollards' Tower (river end)
{
  const cx = 26, cz = 6, w = 24, d = 9, eaves = 11.5, ridge = 16.5;
  g.add(box(w, eaves, d, rag, cx, 0, cz));
  g.add(gableRoof(w, d, ridge - eaves, lead, cx, eaves, cz, true, 0.5));
  for (let i = 0; i < 5; i++) for (const s of [-1, 1])
    g.add(box(1.8, 6.0, 0.45, dark, cx - 9 + i * 4.5, 3.6, cz + s * d / 2));
  for (let i = 0; i <= 5; i++) for (const s of [-1, 1])
    g.add(box(1.0, eaves, 1.4, med, cx - 11.2 + i * 4.5, 0, cz + s * (d / 2 + 0.5)));
  g.add(box(0.5, 7.0, 6.0, dark, cx + w / 2 + 0.15, 4.0, cz));
  // Lollards' Tower: a square stone tower at the north-west corner of the chapel
  const tx = cx - w / 2 - 4.5, tz = cz - 1.0;
  g.add(box(9.5, 18, 11, pale, tx, 0, tz));
  for (const f of [0.24, 0.46, 0.68, 0.88]) for (const s of [-1, 1]) {
    g.add(box(1.6, 1.9, 0.4, dark, tx, 18 * f, tz + s * 5.5));
    g.add(box(0.4, 1.9, 1.6, dark, tx + s * 4.75, 18 * f, tz));
  }
  g.add(box(10.2, 1.0, 11.7, med, tx, 18, tz));
  g.add(crenelRing(10.2, 11.7, 0.8, med, tx, 19, tz, 1.4, 1.4, 1.2));
  g.add(cyl(1.9, 2.1, 23, pale, tx - 4.0, 0, tz + 6.5, 8));
  g.add(cone(2.3, 4.0, lead, tx - 4.0, 23, tz + 6.5, 8));
}

// ---------------------------------------------------------------- lodgings, cloister and river wall
g.add(box(30, 11, 12, brick, 34, 0, -20));
g.add(hipRoof(30, 12, 5.0, tile, 34, 11, -20, 0.6));
for (const o of [-9, 0, 9]) {
  g.add(box(1.8, 1.4, 1.8, brick2, 34 + o, 16.0, -20));
  g.add(cyl(0.5, 0.55, 4.4, brick2, 34 + o, 17.4, -20, 8));
}
g.add(box(12, 10, 26, brick, -48, 0, 6));
g.add(hipRoof(12, 26, 5.0, tile, -48, 10, 6, 0.5));
g.add(box(26, 9, 11, med, 4, 0, -26));
g.add(gableRoof(26, 11, 4.6, tile, 4, 9, -26, true, 0.5));
// river frontage wall and stairs (+z)
g.add(box(104, 3.4, 1.6, med, 0, 0, 36));
g.add(crenel(104, 1.6, med, 0, 3.4, 36, true, 1.0, 1.2, 1.1));
g.add(box(14, 2.4, 8, med, 8, -0.6, 41));
g.add(box(10, 1.0, 5, med, 8, 1.8, 43));
for (const s of [-1, 1]) g.add(cyl(0.9, 1.1, 3.4, port, 8 + s * 4.5, 1.8, 39.5, 8));
// gardens and courts
g.add(box(44, 0.3, 24, M.grass, 24, 0, 22));
g.add(box(52, 0.3, 20, mat(0x968f7d), -26, 0, -20));

await exportGLB(g, out('lambeth_palace'));
