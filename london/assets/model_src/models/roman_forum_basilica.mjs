// Roman forum & basilica of Londinium (2nd c. AD, the "great forum" of c.120).
// FRONT = +z : the open south side of the forum courtyard (the main entrance
// range faces +z, towards the road / the river).  The great basilica runs along
// the NORTH side, i.e. at -z.  Long axis = x (east-west); the apse is at +x (east).
// Sizes: forum insula ~167 x 167 m, basilica ~167 x 52 m, nave ridge ~25 m,
// courtyard porticoes ~8 m to the eaves.
import { exportGLB, out, M, box, cyl, cone, gableRoof, group, colonnade, wall, archPath, THREE } from './_lib_london.mjs';

const S = 167;                 // forum square
const H = S / 2;               // 83.5
const stone = M.rag, plaster = M.whitewash, tile = M.tile, dark = M.dark, col = M.pale;

const g = new THREE.Group();

// ---------------------------------------------------------------- podium
g.add(box(S, 0.9, S, stone, 0, 0, 0));
const Y = 0.9;

// ---------------------------------------------------------------- basilica (north range)
const BD = 52, BZ = -H + BD / 2;          // depth and centre z  (= -57.5)
const naveD = 20, aisleD = (BD - naveD) / 2;  // 16 m each
const naveZ = BZ, aisleNZ = BZ - naveD / 2 - aisleD / 2, aisleSZ = BZ + naveD / 2 + aisleD / 2;

// aisles
for (const az of [aisleNZ, aisleSZ]) {
  g.add(box(S, 11, aisleD, plaster, 0, Y, az));
  // lean-to roof slab sloping down away from the nave
  const sign = az < naveZ ? -1 : 1;
  const slab = box(S, 0.8, aisleD * 1.06, tile, 0, 0, 0);
  slab.rotation.x = sign * 0.20;
  slab.position.set(0, Y + 11 + 1.6, az);
  g.add(slab);
  // clerestory of dark windows on the outer face
  g.add(box(S * 0.98, 2.2, 0.5, dark, 0, Y + 7, az + sign * (aisleD / 2 + 0.1)));
}
// nave block + big gable roof
g.add(box(S, 18, naveD, plaster, 0, Y, naveZ));
g.add(box(S * 0.99, 2.6, naveD + 0.4, dark, 0, Y + 13.5, naveZ));  // clerestory band
g.add(gableRoof(S, naveD, 7, tile, 0, Y + 18, naveZ, true, 0.8));

// apse at the east end
{
  const ap = new THREE.Mesh(new THREE.CylinderGeometry(13, 13, 16, 16, 1, false, -Math.PI / 2, Math.PI), plaster);
  ap.position.set(H, Y + 8, naveZ); ap.rotation.y = 0; g.add(ap);
  const cap = new THREE.Mesh(new THREE.SphereGeometry(13, 16, 8, -Math.PI / 2, Math.PI, 0, Math.PI / 2), tile);
  cap.position.set(H, Y + 16, naveZ); cap.scale.set(1, 0.55, 1); g.add(cap);
}
// basilica south wall facing the courtyard: arcaded, with a colonnaded front
g.add(colonnade(38, 4.3, 0.75, 8.5, col, 0, Y, BZ + BD / 2 + 1.6, true, 8));
g.add(box(S, 1.4, 4.2, plaster, 0, Y + 8.9, BZ + BD / 2 + 1.6));

// ---------------------------------------------------------------- courtyard ranges
const CZ0 = -H + BD;            // -31.5  north edge of courtyard
const CZ1 = H;                  //  83.5
const cLen = CZ1 - CZ0;         // 115
const RD = 12;                  // range depth
const rangeH = 8;

// east & west ranges (shops / offices) running north-south
for (const sx of [-1, 1]) {
  const rx = sx * (H - RD / 2);
  g.add(box(RD, rangeH, cLen, plaster, rx, Y, (CZ0 + CZ1) / 2));
  g.add(gableRoof(cLen, RD, 3.2, tile, rx, Y + rangeH, (CZ0 + CZ1) / 2, false, 0.7));
  // shop doorways on the courtyard side
  g.add(box(0.4, 4.2, cLen * 0.94, dark, rx - sx * (RD / 2 + 0.1), Y + 0.2, (CZ0 + CZ1) / 2));
}
// south (entrance) range
g.add(box(S - 2 * RD, rangeH, RD, plaster, 0, Y, H - RD / 2));
g.add(gableRoof(S - 2 * RD, RD, 3.2, tile, 0, Y + rangeH, H - RD / 2, true, 0.7));
// monumental entrance: a taller centre block with a triple arch facing +z
{
  const w = 26, h = 13;
  const holes = [archPath(0, 8, 0, 6, 4, 0, 8), archPath(-11, 5, 0, 4.5, 2.5, 0, 6), archPath(11, 5, 0, 4.5, 2.5, 0, 6)];
  g.add(wall(w, h, RD, plaster, holes, 0, Y, H - RD / 2));
  g.add(box(w + 2, 1.6, RD + 1.5, stone, 0, Y + h, H - RD / 2));
  g.add(colonnade(4, 6.5, 0.85, 9, col, 0, Y, H + 1.4, true, 8));
  g.add(box(w + 2, 1.6, 3.6, stone, 0, Y + 9, H + 1.4));
}

// ---------------------------------------------------------------- courtyard colonnade
const cIn = RD;   // colonnade stands just inside the ranges
g.add(colonnade(25, 4.4, 0.55, 6.4, col, 0, Y, H - cIn - 1.2, true, 8));                 // south
for (const sx of [-1, 1]) g.add(colonnade(24, 4.4, 0.55, 6.4, col, sx * (H - cIn - 1.2), Y, (CZ0 + CZ1) / 2 - 4, false, 8));  // east/west
// entablature over the courtyard colonnade
g.add(box(S - 2 * cIn - 2, 1.1, 2.4, plaster, 0, Y + 6.9, H - cIn - 1.2));
for (const sx of [-1, 1]) g.add(box(2.4, 1.1, cLen - 10, plaster, sx * (H - cIn - 1.2), Y + 6.9, (CZ0 + CZ1) / 2 - 4));

// small temple / shrine in the courtyard
g.add(box(14, 2, 20, stone, 0, Y, 18));
g.add(box(9, 8, 14, plaster, 0, Y + 2, 16));
g.add(colonnade(4, 3.0, 0.5, 8, col, 0, Y + 2, 24, true, 8));
g.add(gableRoof(9, 15, 3.2, tile, 0, Y + 10, 19, false, 0.8));

await exportGLB(g, out('roman_forum_basilica'));
