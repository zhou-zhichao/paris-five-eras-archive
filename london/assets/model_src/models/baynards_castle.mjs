// Baynard's Castle, Blackfriars - Henry VII's riverside palace-castle of 1501 on
// the site of the Norman castle; the Yorkist and early Tudor seat in the City,
// burnt in the Great Fire of 1666.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x.  "Front" = +z is the RIVER (Thames) side, where the polygonal towers
// rise straight out of the water.
//
// True dimensions: about 100 x 60 m; six polygonal towers ~20 m along the river
// front, a courtyard and hall behind, an embattled landward gatehouse.
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, hipRoof, lathe, group, THREE,
  wall, archPath, crenel, crenelRing, turret, pinnacle, profileWall,
} from './_lib_london.mjs';

const g = new THREE.Group();
const rag = M.rag, med = M.medieval, port = M.portland, brick = M.tudor;
const lead = M.lead, dark = M.dark, tile = M.tile, stone = M.pale;

// ---------------------------------------------------------------- river range (+z)
{
  const z = 22, h = 17;
  g.add(box(100, h, 14, rag, 0, -1.5, z));
  g.add(box(101, 1.0, 15, med, 0, h - 2.5, z));
  g.add(crenelRing(101, 15, 0.9, med, 0, h - 1.5, z, 1.5, 1.6, 1.4));
  g.add(hipRoof(96, 12, 4.5, lead, 0, h - 1.5, z, 0.85));
  for (let i = 0; i < 14; i++) for (const f of [0.30, 0.58, 0.80])
    g.add(box(2.4, 2.6, 0.4, dark, -46 + i * 7.1, h * f - 1.5, z + 7.1));
  // the polygonal towers standing in the water
  for (const tx of [-46, -27.6, -9.2, 9.2, 27.6, 46]) {
    g.add(cyl(5.2, 5.6, 20, rag, tx, -2.5, z + 9.0, 8));
    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4 + Math.PI / 8;
      for (const f of [0.34, 0.62]) {
        const b = box(1.6, 2.4, 0.35, dark, tx + 5.3 * Math.cos(a), 17.5 * f - 2.5, z + 9.0 + 5.3 * Math.sin(a));
        b.rotation.y = Math.PI / 2 - a; g.add(b);
      }
    }
    g.add(cyl(6.0, 6.0, 1.0, med, tx, 17.5, z + 9.0, 8));
    const n = 10;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      const b = box(1.5, 1.5, 0.8, med, tx + 5.7 * Math.cos(a), 18.5, z + 9.0 + 5.7 * Math.sin(a));
      b.rotation.y = Math.PI / 2 - a; g.add(b);
    }
    g.add(cone(5.6, 5.5, lead, tx, 18.5, z + 9.0, 8));
    g.add(box(0.12, 2.0, 0.12, M.gold, tx, 24.0, z + 9.0));
    g.add(box(1.1, 0.5, 0.08, M.gold, tx + 0.55, 25.4, z + 9.0));
  }
  // the water gate between the two centre towers
  g.add(wall(14, 8, 12, rag, [archPath(0, 6.0, 0, 2.8, 3.6, 1, 8)], 0, -2.5, z + 9.0));
  g.add(box(7.0, 3.0, 12, M.water, 0, -2.5, z + 9.0));
}

// ---------------------------------------------------------------- side ranges and courtyard
for (const s of [-1, 1]) {
  g.add(box(13, 14, 40, rag, s * 43.5, 0, -4));
  g.add(crenelRing(14, 41, 0.9, med, s * 43.5, 14, -4, 1.4, 1.5, 1.3));
  g.add(hipRoof(11, 37, 4.0, tile, s * 43.5, 14, -4, 0.7));
  for (let i = 0; i < 5; i++) for (const f of [0.32, 0.66])
    g.add(box(0.4, 2.4, 2.2, dark, s * 37, 14 * f, -20 + i * 8));
  // corner towers on the landward side
  g.add(cyl(5.0, 5.4, 19, rag, s * 44, 0, -26, 8));
  g.add(cyl(5.8, 5.8, 1.0, med, s * 44, 19, -26, 8));
  g.add(crenel(9.0, 0.9, med, s * 44, 20, -26, true, 1.4, 1.4, 1.2));
  g.add(crenel(9.0, 0.9, med, s * 44, 20, -26, false, 1.4, 1.4, 1.2));
  g.add(cone(5.4, 5.0, lead, s * 44, 20, -26, 8));
}
// great hall along the west side of the court
{
  const cx = -22, cz = 0, w = 30, d = 13, eaves = 14, ridge = 21;
  g.add(box(w, eaves, d, stone, cx, 0, cz));
  g.add(gableRoof(w, d, ridge - eaves, lead, cx, eaves, cz, true, 0.6));
  for (let i = 0; i < 5; i++) for (const s of [-1, 1])
    g.add(box(2.6, 6.5, 0.45, dark, cx - 11 + i * 5.5, 4.4, cz + s * d / 2));
  for (let i = 0; i <= 5; i++) for (const s of [-1, 1])
    g.add(box(1.2, eaves + 0.6, 1.6, med, cx - 13.5 + i * 5.5, 0, cz + s * (d / 2 + 0.6)));
  g.add(box(3.2, 2.4, 3.2, med, cx + 2, ridge - 1.0, cz));
  g.add(cone(2.6, 4.0, lead, cx + 2, ridge + 1.4, cz, 8));
}
// chapel and lodgings on the east
g.add(box(22, 12, 11, med, 24, 0, 2));
g.add(gableRoof(22, 11, 5.0, lead, 24, 12, 2, true, 0.5));
for (let i = 0; i < 4; i++) for (const s of [-1, 1])
  g.add(box(1.8, 5.0, 0.45, dark, 17 + i * 4.6, 4.0, 2 + s * 5.5));
g.add(box(28, 0.3, 26, mat(0x968f7d), 2, 0, -6));            // courtyard

// ---------------------------------------------------------------- landward gatehouse (-z)
{
  const gz = -32;
  g.add(wall(12, 15, 11, rag, [archPath(0, 4.6, 0, 4.0, 3.0, 1, 8)], 0, 0, gz));
  g.add(box(12.8, 1.0, 11.8, med, 0, 15, gz));
  g.add(crenelRing(12.8, 11.8, 0.9, med, 0, 16, gz, 1.5, 1.5, 1.3));
  for (const s of [-1, 1]) {
    g.add(cyl(3.4, 3.6, 19, rag, s * 7.6, 0, gz, 8));
    g.add(cyl(4.0, 4.0, 0.9, med, s * 7.6, 19, gz, 8));
    g.add(crenel(6.2, 0.8, med, s * 7.6, 19.9, gz, true, 1.3, 1.2, 1.0));
    g.add(cone(3.9, 4.4, lead, s * 7.6, 19.9, gz, 8));
  }
  // curtain wall closing the landward side
  for (const s of [-1, 1]) {
    g.add(box(28, 10, 3.0, rag, s * 26, 0, gz));
    g.add(crenel(28, 1.5, med, s * 26, 10, gz, true, 1.3, 1.4, 1.2));
  }
}

g.position.z = -3;
await exportGLB(g, out('baynards_castle'));
