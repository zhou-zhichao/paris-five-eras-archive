// VICTORIA: the two stations in one — the LB&SCR "Brighton" side (rebuilt 1908, wide
// ridge-and-furrow roof) and the LC&DR "Chatham" side (1862, three arched iron spans),
// divided by a long brick wall; the 1909 Portland-stone front and the French-roofed
// Grosvenor Hotel (1861) look out over the forecourt.
// Orientation: platforms along x, tracks leaving to -x, buffer stops at +x, the stone
// front facing +z.  ~200 x 220 m.
import {
  exportGLB, box, cyl, cone, dome, lathe, hipRoof, gableRoof, THREE, P, M,
  shedX, ridgeFurrowX, platformsX, openWall, column, colonnade, pediment,
  balustrade, winGridZ, winGridX, bufferStops, chimney, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const SX0 = -95, SX1 = 65, SL = SX1 - SX0, SCX = (SX0 + SX1) / 2;
const BZ = -55, BW = 70;      // Brighton side shed
const CZ = 18, CW = 66;       // Chatham side shed

const bk = M(P.stock), bkd = M(0xa08e6f), rb = M(P.red), st = M(P.stone),
  pale = M(P.pale), dst = M(P.dstone), gl = M(P.glassroof), ir = M(P.iron),
  sl = M(P.slate), dk = M(P.dark), dgl = M(P.darkglass), conc = M(P.concrete);

// ---------------------------------------------------------------- ground / platforms
g.add(box(SL + 30, 0.5, BW + CW + 14, M(P.ballast), SCX + 5, -0.5, (BZ + CZ) / 2));
g.add(platformsX(SL + 20, BW - 8, 5, SCX + 5, 0, BZ, { pw: 8 }));
g.add(platformsX(SL + 20, CW - 8, 4, SCX + 5, 0, CZ, { pw: 8 }));
g.add(bufferStops(BW - 16, 9, SX1 + 2, 0, BZ));
g.add(bufferStops(CW - 16, 8, SX1 + 2, 0, CZ));

// ---------------------------------------------------------------- BRIGHTON side (1908) shed
{
  const EAVES = 17.0;
  for (const sz of [-1, 1]) {
    g.add(box(SL, EAVES - 2, 2.4, bk, SCX, 0, BZ + sz * (BW / 2 - 1.2)));
    for (let i = 0; i < 14; i++)
      g.add(box(2.2, EAVES + 1.5, 3.2, bkd, SX0 + SL * (i + 0.5) / 14, 0, BZ + sz * (BW / 2 - 1.2)));
  }
  for (let c = 0; c < 3; c++) {
    const cz = BZ - BW / 2 + BW * (c + 1) / 4;
    for (let i = 0; i < 12; i++) g.add(cyl(0.55, 0.7, EAVES, ir, SX0 + SL * (i + 0.5) / 12, 0, cz, 8));
  }
  g.add(ridgeFurrowX(SL, BW, 6, 3.6, SCX, EAVES, BZ, { camber: 2.2, fascia: 0x6f7378 }));
  g.add(box(1.4, EAVES + 4, BW, dk, SX0, 0, BZ));                 // country-end screen
  g.add(box(1.4, EAVES + 4, BW, gl, SX1, 0, BZ));                 // buffer-end glazed gable
  for (let i = 0; i < 10; i++) g.add(box(2.2, EAVES + 4, 0.7, ir, SX1, 0, BZ - BW / 2 + BW * (i + 0.5) / 10));
}

// ---------------------------------------------------------------- CHATHAM side: three arched spans
{
  const SPRING = 8.5;
  for (const [cz, span, rise] of [[CZ - 22, 21, 11], [CZ, 22, 12.5], [CZ + 22, 21, 11]]) {
    g.add(shedX(SL, span, rise, SCX, SPRING, cz, {
      segs: 12, ribs: 13, gableAMat: P.dark, gableBMat: P.glassroof,
    }));
  }
  // iron column lines between the spans, and the outer brick walls
  for (const cz of [CZ - 11, CZ + 11]) for (let i = 0; i < 14; i++)
    g.add(cyl(0.5, 0.65, SPRING, ir, SX0 + SL * (i + 0.5) / 14, 0, cz, 8));
  for (const sz of [-1, 1]) {
    g.add(box(SL, SPRING + 4, 2.4, bk, SCX, 0, CZ + sz * (CW / 2 - 1.2)));
    for (let i = 0; i < 14; i++)
      g.add(box(2.2, SPRING + 6, 3.2, bkd, SX0 + SL * (i + 0.5) / 14, 0, CZ + sz * (CW / 2 - 1.2)));
  }
}
// the long dividing wall between the two stations
g.add(box(SL, 14.0, 4.0, bk, SCX, 0, (BZ + BW / 2 + CZ - CW / 2) / 2));

// ---------------------------------------------------------------- 1909 Portland stone front (+z)
{
  const FZ = 62, FD = 22, FH = 24, FW = 130, FX = -20;
  g.add(box(FW, FH, FD, st, FX, 0, FZ));
  g.add(box(FW + 2.0, 1.6, FD + 2.4, pale, FX, FH, FZ));
  g.add(box(FW - 4, 5.5, FD - 3, sl, FX, FH + 1.6, FZ));               // attic / mansard
  g.add(box(FW - 40, 1.2, FD - 6, M(P.lead), FX, FH + 7.1, FZ));
  // giant order of attached columns across the front
  for (let i = 0; i < 13; i++) {
    const x = FX - FW / 2 + FW * (i + 0.5) / 13;
    g.add(box(3.0, FH - 5, 2.2, pale, x, 5.0, FZ + FD / 2 + 0.6));
    g.add(box(3.8, 1.0, 3.0, pale, x, FH - 0.6, FZ + FD / 2 + 0.6));
  }
  g.add(winGridZ(12, 4, 10.0, 4.3, 3.0, 3.0, P.darkglass, FX, 6.0, FZ + FD / 2));
  g.add(box(FW - 8, 5.2, 1.0, dgl, FX, 0.4, FZ + FD / 2 + 0.2));       // ground floor / entrances
  // three tall centre bays with a pediment and the station name
  g.add(box(34, FH + 5.0, FD + 3.5, pale, FX, 0, FZ));
  g.add(pediment(36, 6.0, FD + 3.5, st, FX, FH + 5.0, FZ));
  g.add(box(36, 1.2, FD + 4.5, st, FX, FH + 4.4, FZ));
  // end pavilions
  for (const sx of [-1, 1]) {
    g.add(box(18, FH + 2.5, FD + 3.0, st, FX + sx * (FW / 2 - 9), 0, FZ));
    g.add(hipRoof(18, FD + 3.0, 7.0, sl, FX + sx * (FW / 2 - 9), FH + 2.5, FZ, 0.25));
  }
  // glazed cab-road canopy in front
  for (let i = 0; i < 14; i++) g.add(cyl(0.28, 0.32, 6.5, ir, FX - FW / 2 + FW * (i + 0.5) / 14, 0, FZ + FD / 2 + 8));
  g.add(box(FW, 0.5, 9.0, gl, FX, 6.5, FZ + FD / 2 + 5.0));
}

// ---------------------------------------------------------------- Grosvenor Hotel (1861), +x end
{
  const HX = 88, HZ = 20, HW = 30, HD = 92, HH = 32;
  g.add(box(HW, HH, HD, st, HX, 0, HZ));
  g.add(box(HW + 2.0, 1.6, HD + 2.0, pale, HX, HH, HZ));
  g.add(box(HW - 2, 9.0, HD - 3, sl, HX, HH + 1.6, HZ));               // steep French roof
  g.add(box(HW - 10, 1.2, HD - 12, M(P.lead), HX, HH + 10.6, HZ));
  // dormers in the mansard
  for (let i = 0; i < 11; i++) {
    const z = HZ - HD / 2 + HD * (i + 0.5) / 11;
    g.add(box(3.0, 3.6, 2.8, sl, HX + HW / 2 - 1.5, HH + 2.4, z));
    g.add(box(0.5, 2.4, 2.0, dgl, HX + HW / 2 + 0.2, HH + 3.0, z));
  }
  // seven storeys of windows on the long faces
  g.add(winGridX(13, 6, 7.0, 4.4, 2.6, 3.0, P.darkglass, HX + HW / 2, 3.0, HZ));
  g.add(winGridX(13, 6, 7.0, 4.4, 2.6, 3.0, P.darkglass, HX - HW / 2, 3.0, HZ));
  g.add(winGridZ(4, 6, 6.5, 4.4, 2.6, 3.0, P.darkglass, HX, 3.0, HZ + HD / 2));
  // corner pavilions with taller roofs
  for (const sz of [-1, 1]) {
    g.add(box(HW + 3.5, HH + 3.0, 15, pale, HX, 0, HZ + sz * (HD / 2 - 7.5)));
    g.add(hipRoof(HW + 3.5, 15, 11.0, sl, HX, HH + 3.0, HZ + sz * (HD / 2 - 7.5), 0.2));
    g.add(cyl(0.5, 0.6, 3.0, ir, HX, HH + 14.0, HZ + sz * (HD / 2 - 7.5), 6));
  }
  for (const sz of [-1, 1]) g.add(chimney(3.0, 2.0, 4.0, P.red, HX, HH + 6.0, HZ + sz * 22, 4));
}

// forecourt kerb
g.add(box(200, 0.5, 1.0, dst, -10, 0, 105));

await exportGLB(centreXZ(g), OUT + 'victoria_station.glb');
