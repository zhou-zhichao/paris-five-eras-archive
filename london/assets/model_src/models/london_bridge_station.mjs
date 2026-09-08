// LONDON BRIDGE: the oldest London terminus (1836) as rebuilt by Grimshaw in 2013-18.
// Fifteen platforms sit on the widened brick viaduct ~7 m above the street; a vast
// street-level concourse runs through the arches, and the platforms are covered by the
// undulating white aluminium and glass roof.
// Orientation: platforms along x, tracks leaving to -x, terminating bays at +x, the main
// (Tooley Street / St Thomas Street) concourse front facing +z.  ~300 x 160 m.
import {
  exportGLB, box, cyl, cone, hipRoof, gableRoof, THREE, P, M,
  shedX, platformsX, tracksX, viaductX, openWall, winGridZ, bufferStops, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const X0 = -150, X1 = 150, L = X1 - X0;
const DECK = 7.0;
const VZ = -12, VW = 118;                 // viaduct centre / width
const bk = M(P.stock), bkd = M(0xa08e6f), rbd = M(0x8f7a5c), st = M(P.dstone),
  gl = M(P.glassroof), dgl = M(P.darkglass), ir = M(P.iron), alu = M(P.steelwhite),
  conc = M(P.concrete), dconc = M(P.dconcrete), pf = M(P.platform), sl = M(P.slate);

// ---------------------------------------------------------------- the brick viaduct
{
  const n = 25, bay = L / n;
  g.add(box(L, DECK - 1.2, VW - 3, rbd, 0, 0, VZ));
  for (const sz of [-1, 1]) {
    const ops = [];
    for (let i = 0; i < n; i++) ops.push({ cx: -L / 2 + bay * (i + 0.5), y0: 0, w: bay - 3.4, h: 1.1, arch: true });
    g.add(openWall(L, DECK, 1.6, bk, ops, 0, 0, VZ + sz * (VW / 2 - 0.8), 8));
  }
  // cross walls / piers
  for (let i = 0; i <= n; i++) g.add(box(3.4, DECK - 1.2, VW - 3, bkd, -L / 2 + bay * i, 0, VZ));
  g.add(box(L + 2, 1.2, VW + 2, st, 0, DECK - 1.2, VZ));
  // glazed shopfronts filling the arches on the +z concourse side
  for (let i = 0; i < n; i++)
    g.add(box(bay - 4.0, 4.4, 0.7, dgl, -L / 2 + bay * (i + 0.5), 0.2, VZ + VW / 2 + 0.3));
}

// ---------------------------------------------------------------- platforms and tracks on the deck
g.add(platformsX(L, VW - 12, 8, 0, DECK, VZ, { pw: 9.5 }));
g.add(bufferStops(VW - 40, 6, X1 - 14, DECK, VZ + 8));

// ---------------------------------------------------------------- the undulating 2018 roof
{
  const RW = VW - 26, n = 8, sw = RW / n, EAVES = DECK + 11.5;
  // supporting tree columns
  for (let c = 0; c < n + 1; c++) {
    const cz = VZ - RW / 2 + sw * c;
    for (let i = 0; i < 11; i++) {
      const x = -L / 2 + 12 + i * (L - 24) / 10;
      g.add(cyl(0.5, 0.7, EAVES - DECK - 1.5, alu, x, DECK + 1.0, cz, 8));
    }
  }
  // shallow curved bays whose ridge height rises and falls across the station
  for (let i = 0; i < n; i++) {
    const cz = VZ - RW / 2 + sw * (i + 0.5);
    const rise = 3.0 + 2.6 * Math.sin(Math.PI * (i + 0.5) / n) + 1.1 * Math.sin(2.4 * i);
    const ey = EAVES + 0.9 * Math.sin(1.7 * i);
    g.add(shedX(L - 12, sw + 0.6, rise, 0, ey, cz, {
      segs: 8, ribs: 14, glass: (i % 2 === 1) ? P.glassroof : P.steelwhite,
      iron: 0xcfd2d4, gableA: false, gableB: false, ridge: false,
    }));
    g.add(box(L - 12, ey - (EAVES - 2.4), sw + 0.6, alu, 0, EAVES - 2.4, cz));   // fascia / soffit
    g.add(box(L - 12, 0.5, 0.7, M(0xcfd2d4), 0, ey - 0.3, cz - sw / 2));         // valley
  }
  g.add(box(L - 12, 0.6, RW + 1.5, alu, 0, EAVES - 2.9, VZ));                    // roof soffit
}

// ---------------------------------------------------------------- street-level concourse front (+z)
{
  const CZ = VZ + VW / 2, CD = 22;
  // the wide sweeping entrance canopy
  g.add(box(150, 1.1, CD, alu, -20, DECK - 1.0, CZ + CD / 2));
  g.add(box(152, 0.7, CD + 2, M(0xcfd2d4), -20, DECK - 2.0, CZ + CD / 2));
  for (let i = 0; i < 9; i++) g.add(cyl(0.55, 0.65, DECK - 2.0, alu, -90 + i * 17.5, 0, CZ + CD - 2.5, 8));
  // glazed concourse box below the viaduct
  g.add(box(150, DECK - 2.2, 4.0, dgl, -20, 0, CZ + 2.0));
  for (let i = 0; i < 26; i++) g.add(box(0.6, DECK - 2.2, 4.4, alu, -95 + i * 6.0, 0, CZ + 2.0));
  // the big western entrance hall (glazed, rises past the deck)
  g.add(box(46, DECK + 9.0, 26, gl, 92, 0, CZ + 10));
  for (let i = 0; i < 9; i++) g.add(box(0.8, DECK + 9.0, 27, alu, 70 + i * 5.6, 0, CZ + 10));
  g.add(box(48, 1.2, 28, alu, 92, DECK + 9.0, CZ + 10));
  g.add(box(46, 4.0, 26, dconc, 92, 0, CZ + 10));
  // bus / taxi forecourt kerbs
  g.add(box(240, 0.4, 1.0, conc, -10, 0, CZ + 40));
}

// ---------------------------------------------------------------- retained low brick offices on -z
g.add(box(L * 0.6, 9.0, 14, bk, -30, 0, VZ - VW / 2 - 7));
g.add(box(L * 0.6 + 2, 0.8, 15, st, -30, 9.0, VZ - VW / 2 - 7));
g.add(hipRoof(L * 0.6, 14, 4.0, sl, -30, 9.8, VZ - VW / 2 - 7, 0.75));

await exportGLB(centreXZ(g), OUT + 'london_bridge_station.glb');
