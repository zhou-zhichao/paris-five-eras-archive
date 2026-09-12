// HOLBORN VIADUCT, the London Chatham & Dover Railway's City terminus of 1874,
// closed 1990 and swept away for Thameslink.  Six short platforms on a viaduct above
// Farringdon Street under a single ridged iron-and-glass roof, fronted by the
// five-storey Holborn Viaduct Hotel (Lewis Isaacs, 1877) with its French mansard.
// Orientation: platforms along x, tracks leaving to -x, buffer stops at +x, the hotel
// front facing +z.  Shed ~100 x 60 m.
import {
  exportGLB, box, cyl, cone, hipRoof, gableRoof, THREE, P, M,
  shedX, ridgeFurrowX, platformsX, openWall, pediment, winGridZ,
  bufferStops, chimney, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const SL = 100, SW = 36, SCZ = -14, DECK = 6.0, SPRING = DECK + 6.5;
const bk = M(P.stock), bkd = M(0xa08e6f), st = M(P.stone), pale = M(P.pale),
  dst = M(P.dstone), gl = M(P.glassroof), ir = M(P.iron), sl = M(P.slate),
  dgl = M(P.darkglass), dk = M(P.dark), rb = M(P.red);

// ---------------------------------------------------------------- the viaduct
{
  const n = 10, bay = SL / n;
  g.add(box(SL, DECK - 1.0, SW - 3, bkd, 0, 0, SCZ));
  for (const sz of [-1, 1]) {
    const ops = [];
    for (let i = 0; i < n; i++) ops.push({ cx: -SL / 2 + bay * (i + 0.5), y0: 0, w: bay - 3.2, h: 1.0, arch: true });
    g.add(openWall(SL, DECK, 1.4, bk, ops, 0, 0, SCZ + sz * (SW / 2 - 0.7), 8));
  }
  for (let i = 0; i <= n; i++) g.add(box(3.2, DECK - 1.0, SW - 3, bkd, -SL / 2 + bay * i, 0, SCZ));
  g.add(box(SL + 1.5, 1.0, SW + 1.5, dst, 0, DECK - 1.0, SCZ));
}

// ---------------------------------------------------------------- platforms and the ridged shed
g.add(platformsX(SL - 6, SW - 10, 3, 0, DECK, SCZ, { pw: 7.5 }));
g.add(bufferStops(SW - 18, 5, SL / 2 - 4, DECK, SCZ));
for (const sz of [-1, 1]) {
  const zz = SCZ + sz * (SW / 2 - 1.2);
  const ops = [];
  for (let i = 0; i < 10; i++) ops.push({ cx: -SL / 2 + SL * (i + 0.5) / 10, y0: 2.2, w: 3.0, h: 2.4, arch: true });
  g.add(openWall(SL, SPRING - DECK + 2.0, 2.4, bk, ops, 0, DECK, zz, 8));
  for (let i = 0; i <= 10; i++) g.add(box(1.6, SPRING - DECK + 3.4, 3.2, bkd, -SL / 2 + SL * i / 10, DECK, zz));
  g.add(box(SL, 0.7, 3.4, dst, 0, SPRING + 3.4 - 6.5 + 6.5 - 6.5 + 6.5, zz));
}
for (let i = 0; i < 10; i++) {
  const x = -SL / 2 + SL * (i + 0.5) / 10;
  for (const cz of [SCZ - 9, SCZ + 9]) g.add(cyl(0.4, 0.55, SPRING - DECK, ir, x, DECK, cz, 8));
}
g.add(ridgeFurrowX(SL, SW - 4, 4, 3.4, 0, SPRING, SCZ, { camber: 1.4, fascia: 0x6f7378 }));
g.add(box(1.2, SPRING - DECK + 5, SW - 4, dk, -SL / 2, DECK, SCZ));         // country end
g.add(box(1.2, SPRING - DECK + 5, SW - 4, gl, SL / 2, DECK, SCZ));          // buffer end gable

// ---------------------------------------------------------------- Holborn Viaduct Hotel (+z)
{
  const FZ = SCZ + SW / 2 + 17, FD = 20, FW = 68, FH = 21.0;
  g.add(box(FW, FH, FD, st, 0, 0, FZ));
  g.add(box(FW + 2.0, 1.5, FD + 2.4, pale, 0, FH, FZ));
  g.add(box(FW - 3, 8.0, FD - 3, sl, 0, FH + 1.5, FZ));                     // steep mansard
  g.add(box(FW - 26, 1.2, FD - 10, M(P.lead), 0, FH + 9.5, FZ));
  for (let i = 0; i < 11; i++) {                                            // dormers
    const x = -FW / 2 + FW * (i + 0.5) / 11;
    g.add(box(3.0, 3.6, 2.6, sl, x, FH + 2.3, FZ + FD / 2 - 1.4));
    g.add(box(2.2, 2.4, 0.5, dgl, x, FH + 2.9, FZ + FD / 2 + 0.1));
  }
  // five storeys of windows, stone bands and a rusticated ground floor
  g.add(winGridZ(9, 4, 6.8, 4.4, 2.4, 3.0, P.darkglass, 0, 6.4, FZ + FD / 2));
  g.add(winGridZ(9, 4, 6.8, 4.4, 2.4, 3.0, P.darkglass, 0, 6.4, FZ - FD / 2));
  for (const yy of [5.2, FH - 5.0]) g.add(box(FW + 0.8, 0.8, FD + 0.8, pale, 0, yy, FZ));
  g.add(box(FW - 2, 5.0, FD + 1.2, pale, 0, 0.2, FZ));
  for (let i = 0; i < 5; i++) g.add(box(3.4, 4.4, 0.7, dk, -24 + i * 12, 0.4, FZ + FD / 2 + 0.7));
  // centre bay with a pedimented gable and the clock
  g.add(box(20, FH + 3.0, FD + 3.2, pale, 0, 0, FZ));
  g.add(pediment(22, 5.2, FD + 3.2, st, 0, FH + 3.0, FZ));
  const clk = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 2.0, 0.7, 16), M(0xe8e4d8));
  clk.rotation.x = Math.PI / 2; clk.position.set(0, FH + 5.2, FZ + FD / 2 + 2.0);
  g.add(clk);
  // corner pavilions with tall pyramidal roofs
  for (const sx of [-1, 1]) {
    g.add(box(14, FH + 2.0, FD + 2.6, st, sx * (FW / 2 - 7), 0, FZ));
    g.add(box(15.4, 1.2, FD + 4.0, pale, sx * (FW / 2 - 7), FH + 2.0, FZ));
    g.add(hipRoof(14, FD + 2.6, 9.5, sl, sx * (FW / 2 - 7), FH + 3.2, FZ, 0.15));
    g.add(cyl(0.35, 0.4, 2.4, ir, sx * (FW / 2 - 7), FH + 12.7, FZ, 6));
    g.add(chimney(2.4, 1.6, 3.0, P.stock, sx * 22, FH + 6.5, FZ, 3));
  }
  // the viaduct-level footway / entrance bridge linking the hotel to the platforms
  g.add(box(FW - 16, 1.0, 16, dst, 0, DECK - 1.0, FZ - FD / 2 - 8));
  for (let i = 0; i < 5; i++) g.add(cyl(0.4, 0.5, DECK - 1.0, bk, -22 + i * 11, 0, FZ - FD / 2 - 8, 8));
  g.add(box(110, 0.5, 1.0, dst, 0, 0, FZ + FD / 2 + 12));
}

await exportGLB(centreXZ(g), OUT + 'holborn_viaduct_station.glb');
