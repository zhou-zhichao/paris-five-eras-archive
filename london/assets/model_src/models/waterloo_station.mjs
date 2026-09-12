// WATERLOO, the 1900-1922 rebuild (J. R. Scott / A. W. Szlumper for the L&SWR).
// 21 platforms on a brick viaduct ~6 m above the street, covered by a vast steel
// ridge-and-furrow glazed roof; the 240 m curved concourse and the Portland-stone
// office frontage with the Victory Arch (1922) look out over Station Approach.
// Orientation: platforms along x, tracks leaving to -x, buffer stops and concourse at +x,
// the curved office front and the Victory Arch facing +z.  ~250 x 230 m.
import {
  exportGLB, box, cyl, cone, dome, lathe, hipRoof, gableRoof, THREE, P, M,
  ridgeFurrowX, platformsX, tracksX, openWall, arcade, column, colonnade,
  pediment, balustrade, parapet, winGridZ, winGridX, bufferStops, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const DECK = 6.0;                       // platform level above the street
const X0 = -125, X1 = 125;              // -x tracks leave, +x concourse / frontage
const Z0 = -115, Z1 = 115;
const SHEDX0 = -122, SHEDX1 = 62;       // the train shed
const SW = 190;                          // shed width (z), centred on z = -18
const SCZ = -18;

const bk = M(P.stock), bkd = M(0xa08e6f), st = M(P.stone), pale = M(P.pale),
  dst = M(P.dstone), gl = M(P.glassroof), ir = M(P.iron), sl = M(P.slate),
  dk = M(P.dark), pf = M(P.platform), conc = M(P.concrete), dgl = M(P.darkglass);

// ---------------------------------------------------------------- brick viaduct podium
{
  const L = SHEDX1 - X0, CX = (X0 + SHEDX1) / 2;
  g.add(box(L, DECK - 1.0, SW + 8, bkd, CX, 0, SCZ));
  // arcaded outer faces
  for (const sz of [-1, 1]) {
    const ops = [];
    for (let i = 0; i < 18; i++) ops.push({ cx: -L / 2 + L * (i + 0.5) / 18, y0: 0, w: 6.5, h: 1.4, arch: true });
    g.add(openWall(L, DECK, 1.6, bk, ops, CX, 0, SCZ + sz * (SW + 8) / 2, 8));
  }
  const ops2 = [];
  for (let i = 0; i < 14; i++) ops2.push({ cx: -SW / 2 + SW * (i + 0.5) / 14, y0: 0, w: 6.5, h: 1.4, arch: true });
  const ew = openWall(SW + 8, DECK, 1.6, bk, ops2, 0, 0, 0, 8);
  const ewg = new THREE.Group(); ewg.add(ew); ewg.rotation.y = Math.PI / 2;
  ewg.position.set(X0, 0, SCZ); g.add(ewg);
  g.add(box(L + 2, 1.0, SW + 10, dst, CX, DECK - 1.0, SCZ));   // deck slab edge
}

// ---------------------------------------------------------------- platforms and tracks
g.add(platformsX(SHEDX1 - X0, SW - 6, 11, (X0 + SHEDX1) / 2, DECK, SCZ, { pw: 9 }));
g.add(bufferStops(SW - 20, 11, SHEDX1 - 2, DECK, SCZ));

// ---------------------------------------------------------------- the great ridge-and-furrow roof
{
  const L = SHEDX1 - SHEDX0, CX = (SHEDX0 + SHEDX1) / 2, EAVES = DECK + 15.5;
  // longitudinal steel girders / side screens
  for (const sz of [-1, 1]) {
    g.add(box(L, 12.0, 2.2, bk, CX, DECK, SCZ + sz * (SW / 2 - 1.1)));
    g.add(box(L, 5.0, 1.6, dgl, CX, DECK + 12.0, SCZ + sz * (SW / 2 - 1.0)));
    for (let i = 0; i < 16; i++)
      g.add(box(2.4, 17.5, 3.0, bkd, CX - L / 2 + L * (i + 0.5) / 16, DECK, SCZ + sz * (SW / 2 - 1.1)));
  }
  // internal column lines carrying the roof
  for (let c = 0; c < 6; c++) {
    const cz = SCZ - SW / 2 + SW * (c + 1) / 7;
    for (let i = 0; i < 14; i++)
      g.add(cyl(0.55, 0.7, EAVES - DECK, ir, CX - L / 2 + L * (i + 0.5) / 14, DECK + 1.0, cz, 8));
  }
  g.add(ridgeFurrowX(L, SW, 19, 2.6, CX, EAVES, SCZ, { camber: 2.6, fascia: 0x6f7378 }));
  // the great glazed end screen where the roof meets the concourse (+x)
  g.add(box(1.5, 12.0, SW, gl, SHEDX1, DECK + 6.0, SCZ));
  for (let i = 0; i < 20; i++) g.add(box(2.0, 12.0, 0.6, ir, SHEDX1, DECK + 6.0, SCZ - SW / 2 + SW * (i + 0.5) / 20));
  // dark screen at the country (-x) end
  g.add(box(1.5, 17.0, SW, dk, SHEDX0, DECK, SCZ));
}

// ---------------------------------------------------------------- the concourse (+x end)
{
  const CX0 = SHEDX1, CX1 = 100, L = CX1 - CX0, CX = (CX0 + CX1) / 2, H = DECK + 17.0;
  g.add(box(L, DECK, SW + 8, bkd, CX, 0, SCZ));
  g.add(box(L + 2, 1.0, SW + 10, dst, CX, DECK - 1.0, SCZ));
  g.add(box(L, 1.0, SW - 6, conc, CX, DECK, SCZ));          // concourse floor
  // side walls and a shallow-arched glazed roof over the concourse
  for (const sz of [-1, 1]) g.add(box(L, H - DECK, 2.4, st, CX, DECK, SCZ + sz * (SW / 2 - 1.2)));
  for (let i = 0; i < 8; i++) {
    const zz = SCZ - SW / 2 + SW * (i + 0.5) / 8;
    g.add(cyl(0.6, 0.8, H - DECK - 1, ir, CX0 + 6, DECK + 1, zz, 8));
    g.add(cyl(0.6, 0.8, H - DECK - 1, ir, CX1 - 6, DECK + 1, zz, 8));
  }
  g.add(ridgeFurrowX(L, SW - 4, 5, 2.2, CX, H, SCZ, { camber: 1.2, fascia: 0x6f7378 }));
  // the row of shops / offices along the back (+x) of the concourse
  g.add(box(9, 12.0, SW - 10, st, CX1 - 5, DECK, SCZ));
  g.add(winGridX(16, 3, 11, 4.0, 3.0, 2.6, P.darkglass, CX1 - 0.4, DECK + 2.5, SCZ));
}

// ---------------------------------------------------------------- curved Portland-stone frontage (+z)
{
  const FH = 21.0, FD = 15.0, N = 15;
  for (let i = 0; i < N; i++) {
    const t = i / (N - 1);
    const x = -60 + t * 170;                          // x = -60 .. 110
    const zc = 90 - 11 * t * t;                       // the front curves gently away with x
    const seg = new THREE.Group();
    seg.add(box(14.0, FH, FD, st, 0, 0, 0));
    seg.add(box(15.0, 1.3, FD + 1.6, pale, 0, FH, 0));
    seg.add(box(13.4, 4.6, FD - 2, sl, 0, FH + 1.3, 0));            // mansard attic
    for (let d = 0; d < 3; d++) seg.add(box(2.2, 2.4, FD + 0.6, sl, (d - 1) * 4.2, FH + 1.8, 0));
    seg.add(winGridZ(3, 4, 4.0, 4.3, 2.4, 3.0, P.darkglass, 0, 3.6, FD / 2));
    seg.add(box(13.0, 4.6, 0.7, dgl, 0, 0.5, FD / 2 + 0.1));        // ground-floor arcade
    if (i % 4 === 2) {                                              // pavilion bays
      seg.add(box(9.0, FH + 4.0, FD + 2.2, pale, 0, 0, 0));
      seg.add(hipRoof(9.0, FD + 2.2, 4.0, sl, 0, FH + 4.0, 0, 0.25));
      seg.add(cyl(0.4, 0.5, 2.4, ir, 0, FH + 8.0, 0, 6));
    }
    seg.position.set(x, 0, zc);
    seg.rotation.y = 22 * t / 170 * 0.9;
    g.add(seg);
  }
  // cab road / forecourt wall between the frontage and Station Approach
  g.add(box(180, 1.4, 0.8, dst, 20, 0, 104));
}

// ---------------------------------------------------------------- the VICTORY ARCH (1922)
{
  const AX = 112, AZ = 88;
  const A = new THREE.Group();
  // the great arched opening between two heavy stone piers
  A.add(openWall(28, 18.0, 13.0, st, [{ cx: 0, y0: 0, w: 10.5, h: 5.0, arch: true }], 0, 0, 0, 10));
  for (const sx of [-1, 1]) {
    A.add(box(7.5, 18.0, 14.5, pale, sx * 10.5, 0, 0));
    A.add(box(8.6, 1.2, 15.5, st, sx * 10.5, 18.0, 0));
    A.add(box(3.6, 1.8, 3.6, pale, sx * 10.5, 19.2, 3.4));          // War / Peace groups
    A.add(box(2.0, 3.2, 2.0, dst, sx * 10.5, 21.0, 3.4));
  }
  A.add(box(29, 2.2, 15.5, pale, 0, 18.0, 0));                      // entablature
  A.add(box(21, 3.6, 13.0, st, 0, 20.2, 0));                        // attic with the inscription
  A.add(box(22, 1.0, 14.0, pale, 0, 23.8, 0));
  A.add(box(6.0, 2.0, 6.0, pale, 0, 24.8, 0));                      // pedestal
  A.add(cyl(1.0, 1.3, 3.6, dst, 0, 26.8, 0, 8));                    // Britannia
  A.add(dome(1.5, dst, 0, 30.4, 0, 10, 0.8));
  // the flight of steps up from Station Approach
  for (let i = 0; i < 7; i++) A.add(box(19 + i * 1.2, 0.75, 2.2, dst, 0, i * 0.75, 8.0 + (6 - i) * 2.2));
  A.position.set(AX, 0, AZ);
  g.add(A);
}

await exportGLB(centreXZ(g), OUT + 'waterloo_station.glb');
