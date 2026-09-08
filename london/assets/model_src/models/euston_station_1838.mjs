// EUSTON as first built for the London & Birmingham Railway: Philip Hardwick's Doric
// propylaeum of 1837 (the "Euston Arch", 22 m high), the Great Hall of 1849 behind it,
// and the original iron-and-glass train shed.
// Orientation: platforms along x, tracks leaving to -x, the Great Hall and the Arch
// facing +z.  Shed ~120 x 60 m.
import {
  exportGLB, box, cyl, cone, hipRoof, gableRoof, THREE, P, M,
  shedX, platformsX, openWall, column, colonnade, pediment, balustrade,
  winGridZ, bufferStops, chimney, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const SX0 = -60, SX1 = 60, SL = 120, SW = 60, SCZ = -12;
const SPRING = 7.0;

const bk = M(P.stock), bkd = M(0xa08e6f), st = M(P.stone), pale = M(P.pale),
  dst = M(P.dstone), gl = M(P.glassroof), ir = M(P.iron), sl = M(P.slate),
  dk = M(P.dark), dgl = M(P.darkglass), tim = M(P.timber);

// ---------------------------------------------------------------- platforms and the twin iron shed
g.add(box(SL + 30, 0.5, SW + 4, M(P.ballast), -5, -0.5, SCZ));
g.add(platformsX(SL + 20, SW - 12, 3, -5, 0, SCZ, { pw: 8 }));
g.add(bufferStops(SW - 24, 4, SX1 - 4, 0, SCZ));

for (const dz of [-13, 13]) {
  g.add(shedX(SL, 24, 8.5, 0, SPRING, SCZ + dz, {
    segs: 12, ribs: 11, gableAMat: P.dark, gableBMat: P.glassroof,
  }));
}
// the central row of iron columns and the outer walls
for (let i = 0; i < 12; i++) {
  g.add(cyl(0.4, 0.55, SPRING, ir, SX0 + SL * (i + 0.5) / 12, 0, SCZ, 8));
  g.add(box(1.2, 0.8, 1.2, ir, SX0 + SL * (i + 0.5) / 12, SPRING - 0.8, SCZ));
}
g.add(box(SL, 0.9, 1.2, ir, 0, SPRING, SCZ));
for (const sz of [-1, 1]) {
  const zz = SCZ + sz * (SW / 2 - 1.2);
  const ops = [];
  for (let i = 0; i < 12; i++) ops.push({ cx: -SL / 2 + SL * (i + 0.5) / 12, y0: 2.4, w: 3.0, h: 3.0, arch: true });
  g.add(openWall(SL, SPRING + 4.0, 2.4, bk, ops, 0, 0, zz, 8));
  for (let i = 0; i <= 12; i++) g.add(box(1.6, SPRING + 5.6, 3.2, bkd, SX0 + SL * i / 12, 0, zz));
  g.add(box(SL, 0.7, 3.4, dst, 0, SPRING + 5.6, zz));
}

// ---------------------------------------------------------------- the GREAT HALL (1849), 40 x 20 x 20 m
{
  const HZ = 30, HW = 40, HD = 20, HH = 20;
  g.add(box(HW, HH, HD, st, 0, 0, HZ));
  g.add(box(HW + 2.4, 1.8, HD + 2.4, pale, 0, HH, HZ));                 // heavy cornice
  g.add(box(HW - 3, 3.0, HD - 3, sl, 0, HH + 1.8, HZ));                 // shallow coffered roof
  g.add(box(HW - 14, 1.4, HD - 9, gl, 0, HH + 4.8, HZ));                // roof light
  // giant pilasters and the tall round-headed windows on the long sides
  for (let i = 0; i < 7; i++) {
    const x = -HW / 2 + HW * (i + 0.5) / 7;
    g.add(box(2.6, HH - 1.5, HD + 2.0, pale, x, 0, HZ));
  }
  for (const sz of [-1, 1]) {
    const ops = [];
    for (let i = 0; i < 6; i++) ops.push({ cx: -HW / 2 + HW * (i + 1) / 7, y0: 7.5, w: 3.4, h: 4.5, arch: true });
    g.add(openWall(HW, HH - 1.0, 1.0, dgl, ops, 0, 0, HZ + sz * (HD / 2 + 0.2), 8));
  }
  // the entrance front towards +z with its portico
  g.add(box(16, HH + 2.0, HD + 4.0, st, 0, 0, HZ));
  g.add(pediment(18, 4.4, HD + 4.0, pale, 0, HH + 2.0, HZ));
  g.add(colonnade(4, 4.0, 0.85, 10.0, pale, 0, 0.8, HZ + HD / 2 + 3.0, 10));
  g.add(box(17, 1.6, 5.0, pale, 0, 10.8, HZ + HD / 2 + 3.0));
  for (let i = 0; i < 4; i++) g.add(box(19 + i * 1.6, 0.4, 1.2, dst, 0, i * 0.4, HZ + HD / 2 + 5.4 + (3 - i) * 1.2));
  // flanking wings (the shareholders' room and booking offices)
  for (const sx of [-1, 1]) {
    g.add(box(26, 11.0, HD - 2, st, sx * 33, 0, HZ));
    g.add(box(27, 1.0, HD - 1, pale, sx * 33, 11.0, HZ));
    g.add(hipRoof(26, HD - 2, 3.2, sl, sx * 33, 12.0, HZ, 0.4));
    g.add(winGridZ(4, 2, 5.5, 4.4, 2.0, 2.8, P.darkglass, sx * 33, 2.6, HZ + HD / 2 - 1));
    g.add(chimney(2.0, 1.4, 2.4, P.stock, sx * 33, 13.0, HZ, 3));
  }
}

// ---------------------------------------------------------------- the EUSTON ARCH (1837), 22 m
{
  const AZ = 68, AH = 22.0;
  const A = new THREE.Group();
  // stylobate
  for (let i = 0; i < 3; i++) A.add(box(30 - i * 1.6, 0.6, 16 - i * 1.4, dst, 0, i * 0.6, 0));
  // four fluted Greek Doric columns, 2.6 m diameter, ~ 13.7 m tall
  for (let i = 0; i < 4; i++) {
    const x = (i - 1.5) * 6.6;
    A.add(cyl(1.15, 1.35, 13.4, pale, x, 1.8, 0, 14));
    A.add(box(3.2, 0.9, 3.2, pale, x, 15.2, 0));                        // Doric capital
    A.add(box(3.4, 0.45, 3.4, pale, x, 16.1, 0));
  }
  // antae / side walls
  for (const sx of [-1, 1]) A.add(box(2.6, 14.9, 11.0, st, sx * 12.6, 1.8, 0));
  // entablature: architrave, triglyph frieze, cornice
  A.add(box(28, 1.6, 12.0, pale, 0, 16.55, 0));
  A.add(box(28.4, 2.2, 12.4, st, 0, 18.15, 0));
  for (let i = 0; i < 13; i++) for (const sz of [-1, 1])
    A.add(box(0.8, 2.2, 0.5, pale, -12 + i * 2.0, 18.15, sz * 6.3));    // triglyphs
  A.add(box(30, 1.6, 14.0, pale, 0, 20.35, 0));
  A.add(box(28, 0.9, 12.5, dst, 0, 21.95, 0));                          // blocking course
  A.position.set(0, 0, AZ);
  g.add(A);
}
// the two flanking lodges of the Euston Grove entrance
for (const sx of [-1, 1]) {
  g.add(box(11, 8.0, 11, st, sx * 34, 0, 68));
  g.add(box(12, 1.0, 12, pale, sx * 34, 8.0, 68));
  g.add(hipRoof(11, 11, 2.4, sl, sx * 34, 9.0, 68, 0.2));
}
g.add(box(120, 0.5, 1.0, dst, 0, 0, 82));   // Euston Square railings line

await exportGLB(centreXZ(g), OUT + 'euston_station_1838.glb');
