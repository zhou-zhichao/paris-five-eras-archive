// BROAD STREET, the North London Railway terminus of 1865 (William Baker), demolished
// 1986 for Broadgate.  A twin-span iron train shed on a brick viaduct beside Liverpool
// Street, with an exuberant Italianate stuccoed front, twin external staircases and a
// clock tower over the centre.
// Orientation: platforms along x, tracks leaving to -x, buffer stops at +x, the
// Italianate front and clock tower facing +z.  Shed ~200 x 90 m.
import {
  exportGLB, box, cyl, cone, lathe, hipRoof, THREE, P, M,
  shedX, platformsX, openWall, pediment, balustrade, column, colonnade,
  winGridZ, bufferStops, chimney, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const SL = 200, SW = 62, SCZ = -32, DECK = 6.5, SPRING = DECK + 8.0;
const bk = M(P.stock), bkd = M(0xa08e6f), st = M(P.stone), pale = M(P.pale),
  dst = M(P.dstone), gl = M(P.glassroof), ir = M(P.iron), sl = M(P.slate),
  dgl = M(P.darkglass), dk = M(P.dark), gold = M(P.gold);

// ---------------------------------------------------------------- brick viaduct under the platforms
{
  const n = 18, bay = SL / n;
  g.add(box(SL, DECK - 1.0, SW - 3, bkd, 0, 0, SCZ));
  for (const sz of [-1, 1]) {
    const ops = [];
    for (let i = 0; i < n; i++) ops.push({ cx: -SL / 2 + bay * (i + 0.5), y0: 0, w: bay - 3.2, h: 1.0, arch: true });
    g.add(openWall(SL, DECK, 1.5, bk, ops, 0, 0, SCZ + sz * (SW / 2 - 0.8), 8));
  }
  for (let i = 0; i <= n; i++) g.add(box(3.2, DECK - 1.0, SW - 3, bkd, -SL / 2 + bay * i, 0, SCZ));
  g.add(box(SL + 1.5, 1.0, SW + 1.5, dst, 0, DECK - 1.0, SCZ));
}

// ---------------------------------------------------------------- platforms and the twin arched spans
g.add(platformsX(SL - 10, SW - 12, 4, 0, DECK, SCZ, { pw: 8 }));
g.add(bufferStops(SW - 24, 6, SL / 2 - 6, DECK, SCZ));
for (const dz of [-14, 14]) {
  g.add(shedX(SL - 20, 26, 12.5, 0, SPRING, SCZ + dz, { segs: 12, ribs: 14, gableAMat: P.dark, gableBMat: P.glassroof }));
}
for (let i = 0; i < 15; i++) {
  const x = -SL / 2 + 10 + (SL - 20) * (i + 0.5) / 15;
  g.add(cyl(0.45, 0.6, SPRING - DECK, ir, x, DECK, SCZ, 8));
  g.add(box(1.2, 0.8, 1.2, ir, x, SPRING - 0.8, SCZ));
}
g.add(box(SL - 20, 0.9, 1.2, ir, 0, SPRING, SCZ));
for (const sz of [-1, 1]) {
  const zz = SCZ + sz * (SW / 2 - 1.2);
  const ops = [];
  for (let i = 0; i < 15; i++) ops.push({ cx: -(SL - 20) / 2 + (SL - 20) * (i + 0.5) / 15, y0: 2.4, w: 3.2, h: 2.6, arch: true });
  g.add(openWall(SL - 20, SPRING - DECK + 3.5, 2.4, bk, ops, 0, DECK, zz, 8));
  for (let i = 0; i <= 15; i++) g.add(box(1.8, SPRING - DECK + 5.0, 3.2, bkd, -(SL - 20) / 2 + (SL - 20) * i / 15, DECK, zz));
  g.add(box(SL - 20, 0.7, 3.4, dst, 0, SPRING + 5.0 - DECK + DECK, zz));
}

// ---------------------------------------------------------------- the Italianate front (+z)
{
  const FZ = SCZ + SW / 2 + 11, FD = 20, FW = 96, FH = 22.0;
  g.add(box(FW, FH, FD, st, 0, 0, FZ));
  g.add(box(FW + 2.0, 1.6, FD + 2.4, pale, 0, FH, FZ));
  g.add(hipRoof(FW, FD + 2.4, 5.5, sl, 0, FH + 1.6, FZ, 0.6));
  // three storeys of round-headed windows in shallow arcades
  for (let s = 0; s < 3; s++) {
    const ops = [];
    for (let i = 0; i < 13; i++) ops.push({ cx: -FW / 2 + FW * (i + 0.5) / 13, y0: 0.6, w: 3.4, h: 2.8, arch: true });
    g.add(openWall(FW, 6.6, 0.7, dgl, ops, 0, 1.2 + s * 6.8, FZ + FD / 2 + 0.25, 8));
    g.add(box(FW + 0.8, 0.7, FD + 1.0, pale, 0, 0.5 + s * 6.8, FZ));
  }
  for (let i = 0; i <= 13; i++) g.add(box(1.6, FH, FD + 1.4, pale, -FW / 2 + FW * i / 13, 0, FZ));
  // projecting end pavilions
  for (const sx of [-1, 1]) {
    g.add(box(16, FH + 3.0, FD + 4.0, st, sx * (FW / 2 - 8), 0, FZ));
    g.add(box(17.4, 1.4, FD + 5.4, pale, sx * (FW / 2 - 8), FH + 3.0, FZ));
    g.add(hipRoof(16, FD + 4.0, 6.5, sl, sx * (FW / 2 - 8), FH + 4.4, FZ, 0.2));
    g.add(chimney(2.4, 1.6, 3.0, P.stock, sx * (FW / 2 - 8), FH + 8.0, FZ, 3));
  }

  // ------------------------------------------------------------ clock tower over the centre
  const T = new THREE.Group();
  T.add(box(15, FH + 6.0, 17, st, 0, 0, 0));
  T.add(box(16.5, 1.4, 18.5, pale, 0, FH + 6.0, 0));
  T.add(box(12.5, 8.0, 14.5, st, 0, FH + 7.4, 0));
  // round-headed belfry openings
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 7.0, 5.4, dz ? 0.6 : 7.0, dk, dx * 6.3, FH + 8.4, dz * 7.3));
  T.add(box(14.5, 1.4, 16.5, pale, 0, FH + 15.4, 0));
  T.add(box(11.0, 5.5, 13.0, st, 0, FH + 16.8, 0));                 // clock stage
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const d = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.4, 0.8, 16), M(0xe8e4d8));
    if (dz) d.rotation.x = Math.PI / 2; else d.rotation.z = Math.PI / 2;
    d.position.set(dx * 5.7, FH + 19.6, dz * 6.7); T.add(d);
  }
  T.add(box(12.6, 1.4, 14.6, pale, 0, FH + 22.3, 0));
  T.add(hipRoof(12.0, 14.0, 6.5, sl, 0, FH + 23.7, 0, 0.15));       // Italianate pyramid roof
  T.add(cyl(0.9, 1.1, 2.0, pale, 0, FH + 30.2, 0, 8));
  T.add(cone(1.0, 2.2, sl, 0, FH + 32.2, 0, 8));
  T.add(cyl(0.2, 0.24, 2.0, gold, 0, FH + 34.4, 0, 6));
  T.position.set(0, 0, FZ);
  g.add(T);

  // the twin external staircases from Liverpool Street up to the platform deck
  for (const sx of [-1, 1]) {
    const S = new THREE.Group();
    for (let i = 0; i < 10; i++) S.add(box(3.6, 0.7, 2.2, dst, 0, i * 0.7, -i * 2.2));
    S.add(box(5.0, 1.2, 24, bk, 0, 0, -11));
    S.position.set(sx * 30, 0, FZ + FD / 2 + 24);
    g.add(S);
  }
  g.add(box(150, 0.5, 1.0, dst, 0, 0, FZ + FD / 2 + 28));
}

await exportGLB(centreXZ(g), OUT + 'broad_street_station.glb');
