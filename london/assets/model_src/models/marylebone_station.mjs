// MARYLEBONE, the Great Central Railway's London terminus, H. W. Braddock 1899.
// A low red-brick and terracotta front with the famous glazed iron porte-cochere, a
// four-platform ridge-and-furrow glazed shed behind, and Colonel Edis's Great Central
// Hotel (1899, red brick with a tall central tower) across Marylebone Road.
// Orientation: platforms along x, tracks leaving to -x, buffer stops at +x, the station
// front facing +z.  Shed ~150 x 80 m.
import {
  exportGLB, box, cyl, cone, lathe, hipRoof, gableRoof, THREE, P, M,
  shedX, ridgeFurrowX, platformsX, openWall, pediment, winGridZ, winGridX,
  bufferStops, chimney, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const SL = 150, SW = 62, SCZ = -18, SPRING = 7.0;
const bk = M(P.stock), rb = M(P.red), rbd = M(P.reddark), tc = M(P.terracotta),
  st = M(P.stone), pale = M(P.pale), dst = M(P.dstone), gl = M(P.glassroof),
  ir = M(P.iron), sl = M(P.slate), dgl = M(P.darkglass), dk = M(P.dark);

// ---------------------------------------------------------------- platforms and the twin-span shed
g.add(box(SL + 30, 0.5, SW + 6, M(P.ballast), -10, -0.5, SCZ));
g.add(platformsX(SL + 20, SW - 10, 2, -10, 0, SCZ, { pw: 11 }));
g.add(bufferStops(SW - 22, 4, SL / 2 - 4, 0, SCZ));

for (const dz of [-14, 14]) {
  g.add(shedX(SL, 26, 11.5, 0, SPRING, SCZ + dz, { segs: 12, ribs: 13, gableAMat: P.dark, gableBMat: P.glassroof }));
}
for (let i = 0; i < 14; i++) {
  const x = -SL / 2 + SL * (i + 0.5) / 14;
  g.add(cyl(0.45, 0.6, SPRING, ir, x, 0, SCZ, 8));
  g.add(box(1.2, 0.8, 1.2, ir, x, SPRING - 0.8, SCZ));
}
g.add(box(SL, 0.9, 1.2, ir, 0, SPRING, SCZ));
for (const sz of [-1, 1]) {
  const zz = SCZ + sz * (SW / 2 - 1.2);
  const ops = [];
  for (let i = 0; i < 14; i++) ops.push({ cx: -SL / 2 + SL * (i + 0.5) / 14, y0: 2.4, w: 3.2, h: 2.6, arch: true });
  g.add(openWall(SL, SPRING + 3.5, 2.4, rb, ops, 0, 0, zz, 8));
  for (let i = 0; i <= 14; i++) g.add(box(1.8, SPRING + 5.0, 3.2, rbd, -SL / 2 + SL * i / 14, 0, zz));
  g.add(box(SL, 0.7, 3.4, dst, 0, SPRING + 5.0, zz));
}

// ---------------------------------------------------------------- red-brick front and porte-cochere (+z)
{
  const FZ = SCZ + SW / 2 + 8, FD = 15, FW = 70, FH = 11.0;
  g.add(box(FW, FH, FD, rb, 0, 0, FZ));
  g.add(box(FW + 1.6, 1.2, FD + 1.8, dst, 0, FH, FZ));
  g.add(box(FW - 3, 4.0, FD - 3, sl, 0, FH + 1.2, FZ));
  // three shaped Dutch gables over the entrances
  for (const dx of [-22, 0, 22]) {
    g.add(box(16, FH + 3.5, FD + 1.5, rb, dx, 0, FZ));
    g.add(box(17, 1.0, FD + 2.4, dst, dx, FH + 3.5, FZ));
    g.add(pediment(16, 4.2, FD + 2.4, tc, dx, FH + 4.5, FZ));
    g.add(cyl(0.4, 0.5, 2.0, ir, dx, FH + 8.7, FZ, 6));
  }
  // round-headed windows and the arcaded ground floor
  const ops = [];
  for (let i = 0; i < 11; i++) ops.push({ cx: -FW / 2 + FW * (i + 0.5) / 11, y0: 5.5, w: 3.0, h: 2.6, arch: true });
  g.add(openWall(FW, FH, 0.8, dgl, ops, 0, 0, FZ + FD / 2 + 0.3, 8));
  for (let i = 0; i < 7; i++) g.add(box(3.6, 4.6, 0.8, dk, -FW / 2 + FW * (i + 0.5) / 7, 0.2, FZ + FD / 2 + 0.5));
  // the great glazed iron porte-cochere out to the street
  const PZ = FZ + FD / 2 + 11, PW = 62, PD = 21;
  for (const sz of [-1, 1]) for (let i = 0; i < 8; i++)
    g.add(cyl(0.3, 0.36, 7.5, ir, -PW / 2 + PW * (i + 0.5) / 8, 0, PZ + sz * (PD / 2 - 1.5), 8));
  g.add(box(PW, 0.6, PD, ir, 0, 7.5, PZ));
  g.add(gableRoof(PW, PD, 3.4, gl, 0, 8.1, PZ, true, 0.6));
  g.add(box(PW + 1.4, 1.0, 0.4, tc, 0, 7.1, PZ + PD / 2 + 0.6));      // ornamental valance
  g.add(box(PW + 1.4, 1.0, 0.4, tc, 0, 7.1, PZ - PD / 2 - 0.6));
}

// ---------------------------------------------------------------- Great Central Hotel across the road
{
  const HZ = 86, HW = 110, HD = 30, HH = 32, HX = 4;
  g.add(box(HW, HH, HD, rb, HX, 0, HZ));
  g.add(box(HW + 1.8, 1.4, HD + 2.0, dst, HX, HH, HZ));
  g.add(box(HW - 3, 8.0, HD - 3, sl, HX, HH + 1.4, HZ));               // steep roof
  g.add(box(HW - 30, 1.2, HD - 12, M(P.lead), HX, HH + 9.4, HZ));
  for (let i = 0; i < 13; i++) {
    const x = HX - HW / 2 + HW * (i + 0.5) / 13;
    g.add(box(3.0, 3.6, 2.6, sl, x, HH + 2.2, HZ - HD / 2 + 1.4));
    g.add(box(2.2, 2.4, 0.5, dgl, x, HH + 2.8, HZ - HD / 2 - 0.1));
  }
  g.add(winGridZ(15, 5, 7.0, 5.0, 2.8, 3.2, P.darkglass, HX, 5.5, HZ - HD / 2));
  g.add(winGridZ(15, 5, 7.0, 5.0, 2.8, 3.2, P.darkglass, HX, 5.5, HZ + HD / 2));
  g.add(box(HW - 2, 4.6, HD + 1.2, dst, HX, 0.3, HZ));                 // stone ground storey
  // the tall central tower with its ogee-capped turret
  g.add(box(20, HH + 9, 22, rb, HX, 0, HZ));
  g.add(box(21.6, 1.4, 23.6, dst, HX, HH + 9, HZ));
  g.add(box(16, 4.5, 18, rb, HX, HH + 10.4, HZ));
  g.add(box(17.4, 1.2, 19.4, dst, HX, HH + 14.9, HZ));
  g.add(hipRoof(16, 18, 5.5, sl, HX, HH + 16.1, HZ, 0.2));
  g.add(lathe([[2.2, 0], [2.0, 1.0], [1.4, 2.2], [0.6, 3.0], [0, 3.6]], sl, HX, HH + 21.6, HZ, 10));
  g.add(cyl(0.28, 0.32, 2.0, M(P.gold), HX, HH + 25.2, HZ, 6));
  // end pavilions with turrets
  for (const sx of [-1, 1]) {
    g.add(box(16, HH + 5.0, HD + 3.0, rbd, HX + sx * (HW / 2 - 8), 0, HZ));
    g.add(hipRoof(16, HD + 3.0, 9.0, sl, HX + sx * (HW / 2 - 8), HH + 5.0, HZ, 0.2));
    g.add(chimney(3.0, 2.0, 3.6, P.reddark, HX + sx * (HW / 2 - 22), HH + 6.0, HZ, 4));
  }
}

await exportGLB(centreXZ(g), OUT + 'marylebone_station.glb');
