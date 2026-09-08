// BLACKFRIARS as rebuilt 2009-2012 (Pascall+Watson / Jacobs): the platforms were
// stretched the whole way across the Thames on the widened 1886 railway bridge and
// roofed with 4,400 photovoltaic panels, with new entrances on both banks and the
// stumps of the 1864 bridge left standing beside it.
// Orientation: platforms along x (the bridge runs along x), tracks leaving to -x, the
// City (north) entrance at +x, the concourse fronts facing +z.  ~300 x 30 m.
import {
  exportGLB, box, cyl, cone, THREE, P, M, platformsX, tracksX, winGridZ, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const L = 258, W = 28, DECK = 9.0;
const pv = M(0x2b3b52), pvd = M(0x22303f), alu = M(P.steelwhite), gl = M(P.glass),
  dgl = M(P.darkglass), ir = M(P.iron), st = M(P.dstone), bk = M(P.stock),
  rb = M(0x8a4436), conc = M(P.concrete), pf = M(P.platform), wat = M(0x4f7f8a);

// ---------------------------------------------------------------- river piers and the bridge deck
{
  const np = 6;
  for (let i = 0; i <= np; i++) {
    const x = -L / 2 + 30 + i * (L - 60) / np;
    g.add(box(7.0, DECK - 2.2, W + 5, st, x, 0, 0));
    g.add(cone(4.0, 3.0, st, x, DECK - 2.2, 0, 6));
    g.add(box(8.2, 1.0, W + 6.5, conc, x, DECK - 2.2, 0));
  }
  // the surviving red columns of the 1864 Blackfriars Bridge alongside (-z)
  for (let i = 0; i < 13; i++)
    g.add(cyl(1.5, 1.9, DECK - 1.0, rb, -L / 2 + 16 + i * 19, 0, -W / 2 - 13, 10));
  // the deck itself: box girders under the platforms
  g.add(box(L, 2.2, W, ir, 0, DECK - 2.2, 0));
  g.add(box(L + 2, 0.8, W + 3.5, conc, 0, DECK - 0.8, 0));
  for (const sz of [-1, 1]) g.add(box(L, 2.6, 1.2, M(0x4c4f54), 0, DECK - 2.8, sz * (W / 2 + 1.4)));
}

// ---------------------------------------------------------------- platforms and four tracks
g.add(platformsX(L - 20, W - 4, 2, 0, DECK, 0, { pw: 8 }));

// ---------------------------------------------------------------- the photovoltaic roof
{
  const RL = L - 30, EAVES = DECK + 7.5;
  for (const sz of [-1, 1]) for (let i = 0; i < 22; i++)
    g.add(cyl(0.32, 0.4, EAVES - DECK, alu, -RL / 2 + RL * (i + 0.5) / 22, DECK + 1.0, sz * (W / 2 - 2.0), 8));
  // gently cambered roof deck clad in dark blue PV panels
  for (let j = 0; j < 5; j++) {
    const cz = -W / 2 + W * (j + 0.5) / 5;
    const t = 1 - Math.abs(cz) / (W / 2);
    const yy = EAVES + 1.6 * Math.sin(t * Math.PI / 2);
    g.add(box(RL, 0.7, W / 5 + 0.2, j % 2 ? pv : pvd, 0, yy, cz));
    g.add(box(RL, 0.9, 0.35, alu, 0, yy - 0.9, cz - W / 10));
  }
  g.add(box(RL, 0.9, W + 1.0, alu, 0, EAVES - 0.9, 0));                  // soffit / fascia
  // glazed sides between the deck and the roof
  for (const sz of [-1, 1]) {
    g.add(box(RL, EAVES - DECK - 1.8, 0.5, gl, 0, DECK + 1.6, sz * (W / 2 + 0.4)));
    for (let i = 0; i <= 30; i++) g.add(box(0.5, EAVES - DECK - 1.8, 0.8, alu, -RL / 2 + RL * i / 30, DECK + 1.6, sz * (W / 2 + 0.4)));
  }
  // rows of PV panel frames visible on top
  for (let i = 0; i < 30; i++) g.add(box(0.6, 0.35, W, alu, -RL / 2 + RL * (i + 0.5) / 30, EAVES + 1.9, 0));
}

// ---------------------------------------------------------------- north (City) entrance at +x
{
  const EX = L / 2 + 14, EW = 30, ED = 34, EH = DECK + 8.0;
  g.add(box(EW, EH, ED, gl, EX, 0, 4));
  for (let i = 0; i <= 8; i++) g.add(box(0.7, EH, ED + 0.8, alu, EX - EW / 2 + EW * i / 8, 0, 4));
  for (let i = 0; i <= 9; i++) g.add(box(EW + 0.8, EH, 0.7, alu, EX, 0, 4 - ED / 2 + ED * i / 9));
  g.add(box(EW + 2.5, 1.4, ED + 2.5, alu, EX, EH, 4));
  g.add(box(EW - 6, 5.5, ED - 8, conc, EX, 0, 4));                       // ticket hall core
  g.add(box(EW + 10, 0.8, 12, alu, EX, 6.0, 4 + ED / 2 + 5));            // entrance canopy
  for (const sx of [-1, 1]) g.add(cyl(0.45, 0.5, 6.0, alu, EX + sx * 11, 0, 4 + ED / 2 + 8, 8));
  // the retained 1886 abutment in stock brick
  g.add(box(16, DECK + 1.5, W + 16, bk, L / 2 - 4, 0, 0));
  g.add(box(17.5, 1.0, W + 18, st, L / 2 - 4, DECK + 1.5, 0));
}

// ---------------------------------------------------------------- south bank entrance at -x
{
  const EX = -L / 2 - 9, EW = 20, ED = 26, EH = DECK + 4.0;
  g.add(box(16, DECK + 1.5, W + 12, bk, -L / 2 + 4, 0, 0));              // south abutment
  g.add(box(17.5, 1.0, W + 14, st, -L / 2 + 4, DECK + 1.5, 0));
  g.add(box(EW, EH, ED, gl, EX, 0, 6));
  for (let i = 0; i <= 6; i++) g.add(box(0.7, EH, ED + 0.8, alu, EX - EW / 2 + EW * i / 6, 0, 6));
  g.add(box(EW + 2.0, 1.2, ED + 2.0, alu, EX, EH, 6));
  g.add(box(EW - 4, 4.5, ED - 6, conc, EX, 0, 6));
}

await exportGLB(centreXZ(g), OUT + 'blackfriars_station.glb');
