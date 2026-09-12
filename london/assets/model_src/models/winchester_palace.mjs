// Winchester Palace, Southwark - the London house of the bishops of Winchester,
// begun c.1144, rebuilt in the 14th century.  Its great hall survives as the
// west gable with a spectacular rose window.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x (the rose-window gable is at -x, the service end at +x).  "Front" = +z
// is the RIVER (Thames) side, with the water stairs.
//
// True dimensions: great hall 44 x 11 m internally, gable ~18 m to the apex with
// a rose window ~4 m across over three service doorways.
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, hipRoof, group, THREE,
  crenel, crenelRing, pinnacle, turret, profileWall, rose, wall, archPath,
} from './_lib_london.mjs';

const g = new THREE.Group();
const rag = M.rag, med = M.medieval, pale = M.pale, dark = M.dark, lead = M.lead, tile = M.tile;
const W = 44, D = 13, EAVES = 12.5, RIDGE = 18.5;

// ---- the great hall, over a vaulted undercroft
g.add(box(W + 1.0, 2.2, D + 1.0, med, 0, 0, 0));
for (let i = 0; i < 9; i++) for (const s of [-1, 1])
  g.add(box(1.6, 1.2, 0.4, dark, -W / 2 + (i + 0.5) * W / 9, 0.5, s * (D / 2 + 0.5)));
g.add(box(W, EAVES - 2.2, D, rag, 0, 2.2, 0));
g.add(box(W + 0.8, 0.7, D + 0.8, med, 0, EAVES - 0.7, 0));
g.add(gableRoof(W, D, RIDGE - EAVES, tile, 0, EAVES, 0, true, 0.6));
// two-light traceried hall windows between buttresses
for (let i = 0; i < 6; i++) {
  const bx = -W / 2 + (i + 0.5) * W / 6;
  for (const s of [-1, 1]) {
    g.add(box(2.4, 5.6, 0.45, dark, bx, 4.6, s * D / 2));
    g.add(box(0.3, 5.6, 0.55, med, bx, 4.6, s * (D / 2 + 0.05)));
  }
}
for (let i = 0; i <= 6; i++) {
  const bx = -W / 2 + i * W / 6;
  for (const s of [-1, 1]) g.add(box(1.3, EAVES + 0.6, 1.8, med, bx, 0, s * (D / 2 + 0.7)));
}

// ---- the famous west gable: rose window over three service doorways
{
  const gx = -W / 2;
  g.add(profileWall([[-D / 2, 0], [D / 2, 0], [0, RIDGE - EAVES]], 1.4, rag, gx, EAVES, 0, Math.PI / 2));
  g.add(rose(2.15, 0.9, pale, dark, gx - 0.4, 14.3, 0, Math.PI / 2, 6));
  for (let i = 0; i < 6; i++) {                        // the hexagonal tracery spokes
    const a = i * Math.PI / 3;
    const b = box(0.35, 0.35, 2.0, pale, gx - 0.5, 14.3 + 1.05 * Math.sin(a), 1.05 * Math.cos(a));
    b.rotation.x = -a; g.add(b);
  }
  for (const bz of [-3.6, 0, 3.6]) {
    g.add(box(0.6, 4.6, 2.0, dark, gx - 0.2, 2.4, bz));
    g.add(box(0.7, 0.5, 2.6, med, gx - 0.25, 7.0, bz));
  }
  g.add(box(0.6, 3.2, 9.5, dark, gx - 0.2, 8.4, 0));   // the window band under the rose
  for (const s of [-1, 1]) g.add(turret(1.7, RIDGE + 2, med, lead, gx + 0.4, 0, s * (D / 2 - 0.5), 8, 4.0));
}

// ---- east (service) end and the chamber block beyond
g.add(box(14, 11.5, 15, med, W / 2 + 7, 0, 1));
g.add(hipRoof(14, 15, 5.0, tile, W / 2 + 7, 11.5, 1, 0.5));
for (const s of [-1, 1]) for (const bz of [-4, 4])
  g.add(box(1.8, 1.8, 0.4, dark, W / 2 + 7, 5.0, 1 + s * 7.5));
g.add(cyl(2.2, 2.4, 20, med, W / 2 + 1.5, 0, -D / 2 - 1.2, 8));       // stair turret
g.add(cone(2.7, 4.5, lead, W / 2 + 1.5, 20, -D / 2 - 1.2, 8));

// ---- courtyard ranges to the south (-z) and the chapel
g.add(box(38, 9.5, 11, med, -6, 0, -D / 2 - 12));
g.add(gableRoof(38, 11, 4.6, tile, -6, 9.5, -D / 2 - 12, true, 0.5));
for (let i = 0; i < 7; i++) g.add(box(1.8, 1.8, 0.4, dark, -23 + i * 5.6, 4.8, -D / 2 - 6.6));
g.add(box(11, 9.5, 26, med, -28, 0, -D / 2 - 10));
g.add(hipRoof(11, 26, 4.4, tile, -28, 9.5, -D / 2 - 10, 0.5));
// gatehouse into the courtyard
g.add(wall(9, 12, 11, med, [archPath(0, 4.2, 0, 3.6, 2.6, 1, 8)], -34, 0, -D / 2 - 30, Math.PI / 2));
g.add(crenelRing(9.6, 11.6, 0.7, med, -34, 12, -D / 2 - 30, 1.2, 1.2, 1.1));
for (const s of [-1, 1]) g.add(turret(1.9, 15, med, lead, -34, 0, -D / 2 - 30 + s * 5.0, 8, 3.5));
// chapel
g.add(box(20, 10, 9, rag, 22, 0, -D / 2 - 13));
g.add(gableRoof(20, 9, 5.0, lead, 22, 10, -D / 2 - 13, true, 0.5));
for (let i = 0; i < 4; i++) for (const s of [-1, 1])
  g.add(box(1.8, 4.6, 0.45, dark, 15 + i * 4.6, 3.6, -D / 2 - 13 + s * 4.5));
g.add(cyl(1.2, 1.4, 14, med, 32.5, 0, -D / 2 - 13, 8));
g.add(cone(1.6, 4.0, lead, 32.5, 14, -D / 2 - 13, 8));

// ---- river frontage (+z): a low range, the garden wall and the water stairs
g.add(box(52, 9, 10, med, 4, 0, D / 2 + 12));
g.add(hipRoof(52, 10, 4.2, tile, 4, 9, D / 2 + 12, 0.75));
for (let i = 0; i < 9; i++) g.add(box(1.8, 1.8, 0.4, dark, -18 + i * 5.5, 4.4, D / 2 + 17));
g.add(box(80, 2.4, 1.2, med, 0, 0, D / 2 + 26));
g.add(box(16, 2.6, 10, med, 4, -0.6, D / 2 + 31));
g.add(box(12, 1.0, 7, med, 4, 2.0, D / 2 + 33));
for (const s of [-1, 1]) {
  g.add(cyl(1.0, 1.2, 4.0, pale, 4 + s * 5.0, 2.0, D / 2 + 28.5, 8));
  g.add(cone(1.2, 1.8, pale, 4 + s * 5.0, 6.0, D / 2 + 28.5, 6));
}
g.add(box(70, 0.3, 22, M.grass, -4, 0, D / 2 + 22));

g.position.z = -14;
await exportGLB(g, out('winchester_palace'));
