// The Guildhall of the City of London, John Croxton's great hall of 1411-30.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x (the hall's ridge).  "Front" = +z is the SOUTH front on to Guildhall
// Yard, with the great porch.
//
// True dimensions: hall 46 x 15 m internally (about 50 x 21 m over the walls),
// ridge ~27 m, tall Perpendicular windows between deep buttresses, roof lantern.
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, hipRoof, lathe, group, THREE,
  crenel, crenelRing, pinnacle, turret, profileWall, wall, archPath,
} from './_lib_london.mjs';

const g = new THREE.Group();
const stone = M.rag, trim = M.pale, port = M.portland, lead = M.lead, dark = M.dark, tile = M.tile;
const W = 50, D = 21, EAVES = 18, RIDGE = 27;

// crypt plinth
g.add(box(W + 2, 2.0, D + 2, M.medieval, 0, 0, 0));
for (let i = 0; i < 10; i++) for (const s of [-1, 1])
  g.add(box(2.2, 1.2, 0.4, dark, -W / 2 + (i + 0.5) * W / 10, 0.5, s * (D / 2 + 1.0)));

// the hall
g.add(box(W, EAVES, D, stone, 0, 2.0, 0));
g.add(box(W + 1.4, 1.2, D + 1.4, trim, 0, EAVES + 0.8, 0));
g.add(crenelRing(W + 1.4, D + 1.4, 0.9, trim, 0, EAVES + 2.0, 0, 1.4, 1.5, 1.3));
g.add(gableRoof(W, D, RIDGE - EAVES - 2, lead, 0, EAVES + 2.0, 0, true, 0.4));

// buttresses and the tall Perpendicular windows
for (let i = 0; i <= 8; i++) {
  const bx = -W / 2 + i * W / 8;
  for (const s of [-1, 1]) {
    g.add(box(1.9, EAVES + 1.5, 3.2, trim, bx, 2.0, s * (D / 2 + 1.4)));
    g.add(pinnacle(1.4, 5.5, trim, bx, EAVES + 3.5, s * (D / 2 + 1.4)));
  }
}
for (let i = 0; i < 8; i++) {
  const bx = -W / 2 + (i + 0.5) * W / 8;
  for (const s of [-1, 1]) {
    g.add(box(3.6, 10.0, 0.5, dark, bx, 6.5, s * D / 2));
    g.add(box(0.5, 10.0, 0.6, trim, bx, 6.5, s * (D / 2 + 0.1)));   // mullion
  }
}
// end gables with great windows
for (const s of [-1, 1]) {
  g.add(profileWall([[-D / 2, 0], [D / 2, 0], [0, RIDGE - EAVES - 2]], 2.0, stone, s * W / 2, EAVES + 2.0, 0, Math.PI / 2));
  g.add(box(0.6, 11.0, 9.0, dark, s * (W / 2 + 0.2), 6.0, 0));
  for (const t of [-1, 1]) {
    g.add(cyl(1.9, 2.1, EAVES + 8, trim, s * (W / 2 + 0.6), 2.0, t * (D / 2 - 1.0), 8));
    g.add(cone(2.3, 4.5, lead, s * (W / 2 + 0.6), EAVES + 10, t * (D / 2 - 1.0), 8));
  }
}

// the great south porch (+z)
{
  const pz = D / 2 + 5.5;
  g.add(wall(13, 15, 11, trim, [archPath(0, 5.2, 0, 4.6, 3.2, 1, 8)], 0, 2.0, pz, Math.PI / 2));
  g.add(box(14.0, 1.2, 12.0, port, 0, 17.0, pz));
  g.add(crenelRing(14.0, 12.0, 0.8, port, 0, 18.2, pz, 1.3, 1.3, 1.1));
  for (const s of [-1, 1]) {
    g.add(cyl(1.9, 2.1, 24, trim, s * 7.0, 2.0, pz, 8));
    g.add(lathe([[2.2, 0], [2.4, 1.0], [1.5, 3.0], [0.6, 4.6], [0.18, 5.6]], lead, s * 7.0, 26, pz, 8));
  }
  // statue niches over the arch
  for (const o of [-3.2, 0, 3.2]) g.add(box(1.6, 3.0, 0.5, M.medieval, o, 11.0, pz + 5.6));
}

// roof lantern / louvre
g.add(box(5.0, 3.6, 5.0, trim, 0, RIDGE - 0.6, 0));
for (const s of [-1, 1]) {
  g.add(box(3.2, 2.2, 0.4, dark, 0, RIDGE + 0.2, s * 2.5));
  g.add(box(0.4, 2.2, 3.2, dark, s * 2.5, RIDGE + 0.2, 0));
}
g.add(box(5.8, 0.6, 5.8, port, 0, RIDGE + 3.0, 0));
g.add(lathe([[3.2, 0], [3.4, 1.0], [2.2, 3.2], [0.9, 5.2], [0.2, 6.4]], lead, 0, RIDGE + 3.6, 0, 10));
g.add(box(0.12, 2.2, 0.12, M.gold, 0, RIDGE + 10.0, 0));
g.add(box(1.4, 0.5, 0.08, M.gold, 0.7, RIDGE + 11.6, 0));

// lower ranges of the Guildhall precinct (chapel, library, offices) at -z
g.add(box(24, 11, 12, M.medieval, -20, 0, -D / 2 - 8));
g.add(gableRoof(24, 12, 5.0, tile, -20, 11, -D / 2 - 8, true, 0.5));
g.add(box(18, 10, 11, M.medieval, 18, 0, -D / 2 - 7.5));
g.add(gableRoof(18, 11, 4.5, tile, 18, 10, -D / 2 - 7.5, true, 0.5));
g.add(box(34, 0.3, 16, mat(0x968f7d), 0, 0, D / 2 + 16));      // Guildhall Yard

await exportGLB(g, out('guildhall'));
