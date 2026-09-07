// Crosby Hall, Bishopsgate - the great hall of Sir John Crosby's mansion, 1466,
// the finest surviving medieval merchant's hall in London.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x (the hall's ridge).  "Front" = +z is the courtyard side, with the
// projecting oriel bay.
//
// True dimensions: hall 21 x 12 m over the walls, ridge ~16 m, a two-storey
// oriel bay, embattled parapet and an octagonal stair turret.
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, hipRoof, lathe, group, THREE,
  crenel, crenelRing, pinnacle, turret, profileWall,
} from './_lib_london.mjs';

const g = new THREE.Group();
const stone = M.pale, trim = M.rag, brick = M.brick, lead = M.lead, dark = M.dark, tile = M.tile;
const W = 21, D = 12, EAVES = 11.5, RIDGE = 16.0;

// ---- the hall
g.add(box(W, EAVES, D, stone, 0, 0, 0));
g.add(box(W + 1.0, 0.9, D + 1.0, trim, 0, EAVES - 0.9, 0));
g.add(crenelRing(W + 1.0, D + 1.0, 0.7, trim, 0, EAVES, 0, 1.2, 1.2, 1.0));
g.add(gableRoof(W, D, RIDGE - EAVES, lead, 0, EAVES, 0, true, 0.35));

// tall four-light Perpendicular windows between shallow buttresses
for (let i = 0; i < 4; i++) {
  const bx = -W / 2 + (i + 0.75) * W / 4;
  for (const s of [-1, 1]) {
    g.add(box(3.0, 6.4, 0.45, dark, bx, 3.8, s * D / 2));
    g.add(box(0.35, 6.4, 0.55, trim, bx, 3.8, s * (D / 2 + 0.05)));
    g.add(box(3.4, 0.4, 0.6, trim, bx, 10.3, s * (D / 2 + 0.05)));
  }
}
for (let i = 0; i <= 4; i++) {
  const bx = -W / 2 + i * W / 4;
  for (const s of [-1, 1]) g.add(box(1.1, EAVES, 1.4, trim, bx, 0, s * (D / 2 + 0.5)));
}
// end gables with big windows
for (const s of [-1, 1]) {
  g.add(profileWall([[-D / 2, 0], [D / 2, 0], [0, RIDGE - EAVES]], 1.2, stone, s * W / 2, EAVES, 0, Math.PI / 2));
  g.add(box(0.5, 6.0, 5.5, dark, s * (W / 2 + 0.15), 4.0, 0));
}

// ---- the oriel bay on the +z front (at the dais end)
{
  const ox = 6.2, oz = D / 2 + 2.0;
  for (let i = 0; i < 5; i++) {
    const a = -Math.PI / 2 + (i + 0.5) * Math.PI / 5;
    const px = ox + 3.4 * Math.sin(a), pz = D / 2 + 3.4 * Math.cos(a) - 0.6;
    const p = box(2.3, 10.5, 0.5, stone, px, 0.9, pz);
    p.rotation.y = -a; g.add(p);
    const w = box(1.7, 5.4, 0.4, dark, px, 4.2, pz + 0.1);
    w.rotation.y = -a; g.add(w);
  }
  g.add(cyl(3.6, 3.9, 1.0, trim, ox, 0, D / 2 - 0.6, 10));            // corbelled base
  g.add(cyl(3.9, 3.9, 0.8, trim, ox, 11.4, D / 2 - 0.6, 10));
  g.add(cone(4.1, 2.6, lead, ox, 12.2, D / 2 - 0.6, 10));
  for (let i = 0; i < 5; i++) {
    const a = -Math.PI / 2 + (i + 0.5) * Math.PI / 5;
    g.add(pinnacle(0.5, 2.2, trim, ox + 3.7 * Math.sin(a), 12.2, D / 2 + 3.7 * Math.cos(a) - 0.6));
  }
}

// ---- octagonal stair turret and the porch
g.add(cyl(2.0, 2.2, 19.5, stone, -W / 2 + 2.5, 0, -D / 2 - 1.6, 8));
g.add(crenel(2.0 * 2 * 0.9, 0.5, trim, -W / 2 + 2.5, 19.5, -D / 2 - 1.6, true, 1.0, 0.8, 0.7));
g.add(cone(2.4, 4.2, lead, -W / 2 + 2.5, 19.5, -D / 2 - 1.6, 8));
for (const f of [0.35, 0.65, 0.88]) g.add(box(0.9, 1.4, 0.4, dark, -W / 2 + 2.5, 19.5 * f, -D / 2 - 3.7));
g.add(box(4.4, 8.0, 3.6, stone, -5.5, 0, D / 2 + 1.8));
g.add(crenelRing(4.8, 4.0, 0.6, trim, -5.5, 8.0, D / 2 + 1.8, 1.0, 1.0, 0.9));
g.add(box(2.2, 4.2, 0.5, dark, -5.5, 0, D / 2 + 3.6));

// ---- the lower ranges of the courtyard house behind (-z)
g.add(box(24, 8.5, 9, brick, -3, 0, -D / 2 - 7.5));
g.add(gableRoof(24, 9, 4.5, tile, -3, 8.5, -D / 2 - 7.5, true, 0.5));
for (let i = 0; i < 5; i++) g.add(box(1.8, 1.8, 0.4, dark, -13 + i * 5, 4.5, -D / 2 - 3.05));
for (const o of [-8, 0, 8]) {
  g.add(box(1.5, 1.2, 1.5, M.brick, -3 + o, 12.4, -D / 2 - 7.5));
  g.add(cyl(0.45, 0.5, 3.6, M.brick, -3 + o, 13.6, -D / 2 - 7.5, 8));
}
g.add(box(9, 8.0, 12, brick, 15, 0, -D / 2 - 6));
g.add(hipRoof(9, 12, 4.0, tile, 15, 8.0, -D / 2 - 6, 0.5));

g.position.z = 4;
await exportGLB(g, out('crosby_hall'));
