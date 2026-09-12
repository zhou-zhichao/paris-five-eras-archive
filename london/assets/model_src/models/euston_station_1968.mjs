// EUSTON as rebuilt for the West Coast electrification and opened in 1968
// (British Rail LMR architects with R. L. Moorcroft): a single long low concourse box
// with a continuous glazed wall, a flat roof, low canopies over the eighteen platforms,
// and the three matching curtain-walled office blocks on the piazza.
// Orientation: platforms along x, tracks leaving to -x, the concourse and its glazed
// front facing +z.  Concourse block ~200 x 120 m.
import {
  exportGLB, box, cyl, THREE, P, M, platformsX, tracksX, winGridZ, bufferStops, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const X0 = -100, X1 = 100, L = 200;
const PZ = -35, PW = 110;                 // platform area
const conc = M(P.concrete), dconc = M(P.dconcrete), st = M(P.steelwhite),
  gl = M(P.glass), dgl = M(P.darkglass), ir = M(P.iron), pf = M(P.platform),
  bk = M(P.stock), dst = M(P.dstone), blk = M(0x4a4d51);

// ---------------------------------------------------------------- platforms under low flat canopies
g.add(box(L + 40, 0.6, PW + 6, M(P.ballast), -10, -0.6, PZ));
g.add(platformsX(L + 20, PW - 4, 9, -10, 0, PZ, { pw: 8.5 }));
g.add(bufferStops(PW - 20, 9, X1 - 22, 0, PZ));
{
  const CL = 150, CX = -20;
  for (let c = 0; c < 10; c++) {
    const cz = PZ - PW / 2 + PW * (c + 0.5) / 10;
    for (let i = 0; i < 11; i++) g.add(cyl(0.35, 0.4, 6.0, conc, CX - CL / 2 + CL * (i + 0.5) / 11, 1.0, cz, 8));
  }
  g.add(box(CL, 0.9, PW, conc, CX, 7.0, PZ));               // flat platform canopy slab
  g.add(box(CL + 1.5, 0.4, PW + 1.5, st, CX, 6.6, PZ));
  for (let i = 0; i < 8; i++) g.add(box(CL - 6, 0.5, 2.4, M(P.glassroof), CX, 7.9, PZ - PW / 2 + PW * (i + 0.5) / 8));
}

// ---------------------------------------------------------------- the 1968 concourse block (+z)
{
  const CZ = 40, CD = 62, CH = 15.5;
  g.add(box(L, 1.0, CD, dconc, 0, 0, CZ));                              // podium slab
  // the great glazed wall on +z, in a fine mullion grid
  g.add(box(L, CH, CD, gl, 0, 1.0, CZ));
  g.add(box(L - 34, CH - 1.0, CD - 18, dconc, 0, 1.0, CZ - 6));         // solid core / retail behind
  for (let i = 0; i <= 40; i++) g.add(box(0.7, CH, CD + 0.8, st, -L / 2 + L * i / 40, 1.0, CZ));
  for (const yy of [1.0, 6.0, 11.0]) g.add(box(L, 0.9, CD + 0.8, st, 0, yy, CZ));
  for (const sx of [-1, 1]) g.add(box(1.0, CH, CD, dconc, sx * L / 2, 1.0, CZ));
  // deep flat roof: a pale fascia band and a dark asphalt deck with rooflights
  g.add(box(L + 4, 1.6, CD + 4, st, 0, 1.0 + CH, CZ));
  g.add(box(L + 1, 0.5, CD + 1, blk, 0, 1.0 + CH + 1.6, CZ));
  for (let i = 0; i < 9; i++) for (let j = 0; j < 3; j++)
    g.add(box(14, 0.7, 9, M(P.glassroof), -L / 2 + 12 + i * 22, 1.0 + CH + 2.1, CZ - 18 + j * 18));
  for (let i = 0; i < 5; i++) g.add(box(6, 2.2, 5, M(0x5a5e63), -L / 2 + 26 + i * 38, 1.0 + CH + 2.1, CZ + 26));
  // the dark stone-faced end blocks and the taxi ramp
  for (const sx of [-1, 1]) {
    g.add(box(24, CH + 3.0, CD, dst, sx * (L / 2 - 12), 0, CZ));
    g.add(winGridZ(3, 3, 6.0, 4.4, 4.0, 2.6, P.darkglass, sx * (L / 2 - 12), 3.0, CZ + CD / 2));
  }
  // the low entrance canopy over the piazza
  g.add(box(L - 40, 0.8, 12, conc, 0, 6.2, CZ + CD / 2 + 6));
  for (let i = 0; i < 10; i++) g.add(cyl(0.4, 0.45, 6.2, st, -70 + i * 15.5, 1.0, CZ + CD / 2 + 10, 8));
}

// ---------------------------------------------------------------- three office blocks on the piazza
for (let i = 0; i < 3; i++) {
  const bx = -56 + i * 56, bz = 98, BW = 32, BD = 19, BH = 38;
  const B = new THREE.Group();
  B.add(box(BW, 4.5, BD + 4, dconc, 0, 0, 0));                          // podium
  B.add(box(BW, BH, BD, dgl, 0, 4.5, 0));
  for (let f = 0; f < 10; f++) {                                        // banded curtain wall
    const y = 4.5 + f * (BH / 10);
    B.add(box(BW + 0.5, 1.0, BD + 0.5, st, 0, y, 0));
  }
  for (let m = 0; m <= 8; m++) B.add(box(0.5, BH, BD + 0.5, st, -BW / 2 + BW * m / 8, 4.5, 0));
  for (const sx of [-1, 1]) B.add(box(2.5, BH + 2.0, BD + 1.0, conc, sx * (BW / 2 + 0.5), 4.5, 0));
  B.add(box(BW + 3, 1.4, BD + 3, conc, 0, 4.5 + BH, 0));
  B.add(box(BW - 12, 3.0, BD - 8, blk, 0, 4.5 + BH + 1.4, 0));          // plant room
  B.position.set(bx, 0, bz);
  g.add(B);
}

// piazza paving edge
g.add(box(220, 0.35, 1.0, conc, 0, 0, 118));

await exportGLB(centreXZ(g), OUT + 'euston_station_1968.glb');
