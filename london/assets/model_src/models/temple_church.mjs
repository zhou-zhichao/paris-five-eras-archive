// The Temple Church (Knights Templar): the Round Church of 1185 with the
// rectangular "Oblong" chancel added in 1240.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x (round nave at -x, chancel east end at +x).  "Front" = +z is the south
// side, towards the Inner Temple cloisters.
//
// True dimensions: round nave 17 m external diameter, chancel ~25 x 12 m,
// chancel ridge ~16 m, round-nave clerestory drum with a conical lead roof.
import {
  exportGLB, out, M, box, cyl, cone, gableRoof, hipRoof, group, THREE,
  crenel, crenelRing, pinnacle, turret, lancets, profileWall,
} from './_lib_london.mjs';

const g = new THREE.Group();
const stone = M.pale, trim = M.medieval, lead = M.lead, dark = M.dark;

// ---- the Round Church: aisle drum + taller clerestory drum + conical roof
const RX = -13;
g.add(cyl(8.5, 8.8, 8.5, stone, RX, 0, 0, 16));                 // aisle wall
g.add(cone(9.4, 2.2, lead, RX, 8.5, 0, 16));                    // lean-to aisle roof
g.add(cyl(5.2, 5.2, 15.5, stone, RX, 0, 0, 16));                // clerestory drum
g.add(cyl(5.7, 5.7, 0.8, trim, RX, 15.5, 0, 16));
g.add(cone(5.9, 6.5, lead, RX, 16.3, 0, 16));                   // conical roof
g.add(cone(0.7, 2.4, M.gold, RX, 22.8, 0, 6));
for (let i = 0; i < 12; i++) {                                   // round-headed windows
  const a = i * Math.PI / 6;
  const b = box(1.5, 3.0, 0.4, dark, RX + 8.7 * Math.cos(a), 3.4, 8.7 * Math.sin(a));
  b.rotation.y = Math.PI / 2 - a; g.add(b);
}
for (let i = 0; i < 8; i++) {
  const a = i * Math.PI / 4 + Math.PI / 8;
  const b = box(1.4, 3.4, 0.4, dark, RX + 5.1 * Math.cos(a), 10.4, 5.1 * Math.sin(a));
  b.rotation.y = Math.PI / 2 - a; g.add(b);
  g.add(box(1.2, 8.6, 1.6, trim, RX + 8.9 * Math.cos(a), 0, 8.9 * Math.sin(a)).rotateY(Math.PI / 2 - a));
}
// west porch of the Round
g.add(box(5.0, 7.0, 6.5, trim, RX - 10.0, 0, 0));
g.add(gableRoof(6.5, 5.0, 3.0, lead, RX - 10.0, 7.0, 0, false, 0.4));
g.add(box(0.6, 5.0, 3.0, dark, RX - 12.4, 0, 0));

// ---- the Oblong chancel: three vessels of equal height ("hall church")
{
  const x0 = RX + 7.0, x1 = 22, len = x1 - x0, cx = (x0 + x1) / 2;
  const HW = 11.5, H = 12.5, RIDGE = 16.5;
  g.add(box(len, H, HW * 2, stone, cx, 0, 0));
  g.add(box(len + 0.6, 0.9, HW * 2 + 1.0, trim, cx, H - 0.9, 0));
  g.add(gableRoof(len, HW * 2, RIDGE - H, lead, cx, H, 0, true, 0.6));
  for (const s of [-1, 1]) {
    g.add(lancets(5, len / 5, 2.2, 6.0, 0.45, dark, cx, 3.5, s * HW, true));
    for (let i = 0; i <= 5; i++) {
      const bx = x0 + i * len / 5;
      g.add(box(1.3, H + 1.4, 2.2, trim, bx, 0, s * (HW + 0.9)));
      g.add(cone(1.0, 2.0, trim, bx, H + 1.4, s * (HW + 0.9), 4));
    }
  }
  // east end: triple lancets in a gable
  g.add(profileWall([[-HW, 0], [HW, 0], [0, RIDGE - H]], 2.0, stone, x1, H, 0, Math.PI / 2));
  for (const bz of [-4.5, 0, 4.5]) g.add(box(0.6, 8.0, 2.4, dark, x1 + 0.2, 3.0, bz));
  for (const s of [-1, 1]) g.add(turret(1.5, H + 6, trim, lead, x1 + 0.4, 0, s * (HW - 1.2), 8, 3.5));
}

await exportGLB(g, out('temple_church'));
