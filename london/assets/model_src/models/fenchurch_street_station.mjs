// FENCHURCH STREET, George Berkeley for the London & Blackwall Railway, 1854.
// A modest two-storey stock-brick and stucco front whose big segmental (curved) gable
// echoes the arch of the single train shed behind it, with the station clock in the
// tympanum; four platforms under one arched iron-and-glass span.
// Orientation: platforms along x, tracks leaving to -x, buffer stops at +x, the curved
// gable front facing +z.  Shed ~100 x 60 m.
import {
  exportGLB, box, cyl, cone, hipRoof, THREE, P, M,
  shedX, platformsX, openWall, winGridZ, bufferStops, chimney, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const SL = 100, SW = 34, SCZ = -8, SPRING = 6.5, RISE = 12.5;
const bk = M(P.stock), bkd = M(0xa08e6f), st = M(P.stone), pale = M(P.pale),
  dst = M(P.dstone), gl = M(P.glassroof), ir = M(P.iron), sl = M(P.slate),
  dk = M(P.dark), dgl = M(P.darkglass), gold = M(P.gold);

// ---------------------------------------------------------------- platforms and the single shed
g.add(box(SL + 24, 0.5, SW + 2, M(P.ballast), -6, -0.5, SCZ));
g.add(platformsX(SL + 16, SW - 8, 2, -6, 0, SCZ, { pw: 9 }));
g.add(bufferStops(SW - 16, 4, SL / 2 - 3, 0, SCZ));

g.add(shedX(SL, SW - 6, RISE, 0, SPRING, SCZ, { segs: 14, ribs: 10, gableAMat: P.dark, gableBMat: P.glassroof }));
for (const sz of [-1, 1]) {
  const zz = SCZ + sz * (SW / 2 - 1.1);
  const ops = [];
  for (let i = 0; i < 10; i++) ops.push({ cx: -SL / 2 + SL * (i + 0.5) / 10, y0: 2.2, w: 3.2, h: 2.8, arch: true });
  g.add(openWall(SL, SPRING + 3.0, 2.2, bk, ops, 0, 0, zz, 8));
  for (let i = 0; i <= 10; i++) g.add(box(1.6, SPRING + 4.4, 3.0, bkd, -SL / 2 + SL * i / 10, 0, zz));
  g.add(box(SL, 0.6, 3.2, dst, 0, SPRING + 4.4, zz));
}

// ---------------------------------------------------------------- the street front (+z), curved gable
{
  const FZ = SCZ + SW / 2 + 6, FW = 46, FD = 12, FH = 12.0;
  g.add(box(FW, FH, FD, st, 0, 0, FZ));
  g.add(box(FW + 1.6, 1.2, FD + 1.6, pale, 0, FH, FZ));
  // the wide segmental gable over the centre, built from stacked arch rings
  const s = new THREE.Shape();
  s.moveTo(-19, 0);
  for (let i = 0; i <= 16; i++) { const t = -1 + 2 * i / 16; s.lineTo(t * 19, 7.4 * Math.sqrt(Math.max(0, 1 - t * t * 0.92))); }
  s.lineTo(19, 0); s.closePath();
  const gm = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: FD + 2.0, bevelEnabled: false }), st);
  gm.position.set(0, FH + 1.2, FZ - (FD + 2.0) / 2);
  g.add(gm);
  // the moulded band round the gable and the clock in the tympanum
  const s2 = new THREE.Shape();
  s2.moveTo(-20.4, 0);
  for (let i = 0; i <= 16; i++) { const t = -1 + 2 * i / 16; s2.lineTo(t * 20.4, 8.6 * Math.sqrt(Math.max(0, 1 - t * t * 0.92))); }
  s2.lineTo(20.4, 0); s2.closePath();
  const gm2 = new THREE.Mesh(new THREE.ExtrudeGeometry(s2, { depth: 1.4, bevelEnabled: false }), pale);
  gm2.position.set(0, FH + 1.2, FZ + FD / 2 + 0.4);
  g.add(gm2);
  const clk = new THREE.Mesh(new THREE.CylinderGeometry(2.6, 2.6, 0.8, 18), M(0xe8e4d8));
  clk.rotation.x = Math.PI / 2; clk.position.set(0, FH + 5.4, FZ + FD / 2 + 2.0);
  g.add(clk);
  g.add(cyl(0.5, 0.6, 1.6, gold, 0, FH + 9.6, FZ, 8));
  // two storeys of round-headed windows and the arcaded ground floor
  const ops = [];
  for (let i = 0; i < 7; i++) ops.push({ cx: -FW / 2 + FW * (i + 0.5) / 7, y0: 6.6, w: 3.0, h: 2.4, arch: true });
  g.add(openWall(FW, FH, 0.8, dgl, ops, 0, 0, FZ + FD / 2 + 0.2, 8));
  for (let i = 0; i < 5; i++) g.add(box(3.6, 4.6, 0.7, dk, -12 + i * 6, 0.3, FZ + FD / 2 + 0.4));
  for (let i = 0; i < 8; i++) g.add(box(1.4, FH + 1.2, FD + 1.2, pale, -FW / 2 + FW * i / 7, 0, FZ));
  // flanking two-storey wings, slate-roofed
  for (const sx of [-1, 1]) {
    g.add(box(20, 10.5, FD - 1, bk, sx * 33, 0, FZ));
    g.add(box(21, 0.9, FD, dst, sx * 33, 10.5, FZ));
    g.add(hipRoof(20, FD - 1, 3.0, sl, sx * 33, 11.4, FZ, 0.4));
    g.add(winGridZ(3, 2, 5.2, 4.2, 2.0, 2.6, P.darkglass, sx * 33, 2.6, FZ + FD / 2 - 0.4));
    g.add(chimney(1.8, 1.2, 2.4, P.stock, sx * 33, 12.4, FZ, 3));
  }
  g.add(box(96, 0.4, 0.9, dst, 0, 0, FZ + FD / 2 + 10));   // Fenchurch Street kerb
}

await exportGLB(centreXZ(g), OUT + 'fenchurch_street_station.glb');
