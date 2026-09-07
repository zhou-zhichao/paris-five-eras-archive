// St Paul's Cathedral, Wren 1675-1710.  Portland stone.
// Orientation: liturgical long axis along X.  WEST FRONT (portico + 2 towers) at -X,
// apse/east end at +X.  SOUTH side (the river side) faces +Z.  Ground y=0, centred on origin.
// True sizes: overall length 158 m, width across transepts 75 m, nave block 37 m wide,
// parapet 33 m, west towers 65 m, dome (lead) top 85 m, lantern 102 m, gold cross 111.3 m.
import { exportGLB, group, box, cyl, cone, dome, lathe, prism, gableRoof, THREE,
  P, M, column, colonnade, ringColonnade, pediment, openWall,
  pinnacle, finialBallCross, balustrade, OUT } from './_lib_wren_edwardian.mjs';

const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), lead = M(P.lead), gold = M(P.gold), dark = M(P.iron);
const g = new THREE.Group();

const XC = 0;        // crossing / dome centre
const WF = -70;      // west facade plane (inner face of the front block)
const EA = 62;       // apse centre  (apse r 17 -> east extreme +79)
const BODYC = (WF + EA) / 2, BODYL = EA - WF;   // nave+choir block

// ---------------------------------------------------------------- podium
g.add(box(BODYL + 12, 1.6, 42, dk, BODYC - 3, 0, 0));
g.add(box(40, 1.6, 60, dk, XC, 0, 0));

// ---------------------------------------------------------------- main body (nave + choir)
g.add(box(BODYL, 15, 38, st, BODYC, 1.6, 0));            // lower order
g.add(box(BODYL + 1, 1.6, 39.5, pale, BODYC, 16.6, 0));  // first cornice
g.add(box(BODYL - 2, 12, 34, st, BODYC, 18.2, 0));       // upper screen wall
g.add(box(BODYL, 1.6, 36, pale, BODYC, 30.2, 0));        // main cornice
g.add(balustrade(BODYL, 36, 2.2, pale, BODYC, 31.8, 0)); // parapet 33 m
g.add(box(BODYL - 10, 1.0, 28, lead, BODYC, 30.2, 0));
g.add(gableRoof(BODYL - 10, 26, 3.2, lead, BODYC, 31.0, 0, true, 0));

// aisle window bands + pilasters (long sides)
for (const zs of [1, -1]) {
  for (let i = 0; i < 19; i++) {
    const x = WF + 4 + i * 6.7;
    if (Math.abs(x - XC) < 21) continue;
    if (x > EA - 3) continue;
    g.add(box(3.0, 8.0, 0.6, dark, x, 5.5, zs * 19.1));
    g.add(box(3.0, 6.5, 0.6, dark, x, 20.5, zs * 17.1));
    g.add(box(1.4, 15, 1.2, pale, x + 3.35, 1.6, zs * 19.0));
  }
}

// ---------------------------------------------------------------- transepts (75 m across)
g.add(box(34, 15, 56, st, XC, 1.6, 0));
g.add(box(35, 1.6, 57.5, pale, XC, 16.6, 0));
g.add(box(31, 12, 52, st, XC, 18.2, 0));
g.add(box(33, 1.6, 54, pale, XC, 30.2, 0));
g.add(balustrade(33, 54, 2.2, pale, XC, 31.8, 0));
g.add(box(28, 1.0, 46, lead, XC, 30.2, 0));
// transept end pediments + semicircular colonnaded porches
for (const zs of [1, -1]) {
  const p = new THREE.Group();
  p.add(pediment(26, 6.5, 3.0, pale, 0, 32.2, 27.0));
  p.add(cyl(9.5, 10.5, 2.0, dk, 0, 0, 28.0, 20));
  p.add(ringColonnade(7, 8.2, 1.15, 12.5, pale, 0, 2.0, 28.0, 8, 0, Math.PI));
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(9.6, 9.6, 2.2, 20, 1, false, 0, Math.PI), pale);
  cap.position.set(0, 15.6 + 1.1, 28.0); p.add(cap);
  const hd = new THREE.Mesh(new THREE.SphereGeometry(9.0, 20, 6, 0, Math.PI, 0, Math.PI / 2), lead);
  hd.position.set(0, 16.7, 28.0); hd.scale.y = 0.45; p.add(hd);
  p.rotation.y = zs > 0 ? 0 : Math.PI;
  p.position.x = XC;
  g.add(p);
}

// ---------------------------------------------------------------- apse (east end)
function halfCyl(r, h, m, x, y, seg = 20) {
  const c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg, 1, false, -Math.PI / 2, Math.PI), m);
  c.position.set(x, y + h / 2, 0); return c;
}
g.add(halfCyl(17, 15, st, EA, 1.6));
g.add(halfCyl(18, 1.6, pale, EA, 16.6));
g.add(halfCyl(15, 12, st, EA, 18.2));
g.add(halfCyl(16, 2.0, pale, EA, 30.2));
g.add(halfCyl(14, 1.2, lead, EA, 32.2));

// ---------------------------------------------------------------- WEST FRONT
// broad flight of steps, stepping westwards only
for (let i = 0; i < 6; i++) g.add(box(1.0, 0.75, 40 - i * 1.6, dk, -75.5 + i, i * 0.75, 0));
// facade wall block
g.add(box(8, 34, 60, st, WF - 4, 1.6, 0));
g.add(box(9, 2.0, 61.5, pale, WF - 4, 35.6, 0));
// two-storey portico with PAIRED Corinthian columns
const portZ = [-12.2, -9.4, -5.4, -2.6, 2.6, 5.4, 9.4, 12.2];
const portZlo = [-13.0, -10.0, -6.6, -3.6, 3.6, 6.6, 10.0, 13.0];
for (const z of portZlo) g.add(column(1.5, 13.5, pale, -73.6, 4.2, z, 10));
g.add(box(9, 2.6, 30, pale, -73.5, 17.7, 0));               // lower entablature
for (const z of portZ) g.add(column(1.25, 10.5, pale, -73.3, 20.3, z, 10));
g.add(box(8.4, 2.4, 28, pale, -73.5, 30.8, 0));             // upper entablature
{ const pd = new THREE.Group(); pd.add(pediment(28, 7.2, 8.4, pale, 0, 0, 0)); pd.rotation.y = -Math.PI / 2; pd.position.set(-73.5, 33.2, 0); g.add(pd); }
g.add(box(1.0, 26, 26, dark, -70.4, 4.2, 0));               // shadow behind columns

// ---------------------------------------------------------------- WEST TOWERS (65 m)
for (const zs of [1, -1]) {
  const t = new THREE.Group();
  t.add(box(13, 34, 13, st, 0, 1.6, 0));
  t.add(box(14.2, 2.0, 14.2, pale, 0, 35.6, 0));
  t.add(box(11.5, 8, 11.5, st, 0, 37.6, 0));
  t.add(box(12.5, 1.6, 12.5, pale, 0, 45.6, 0));
  t.add(cyl(4.4, 4.6, 9.5, st, 0, 47.2, 0, 12));
  t.add(ringColonnade(8, 5.6, 0.75, 9.5, pale, 0, 47.2, 0, 6));
  t.add(cyl(6.4, 6.4, 1.4, pale, 0, 56.7, 0, 12));
  t.add(lathe([[4.6, 0], [4.4, 1.6], [3.4, 3.4], [2.0, 4.8], [1.1, 6.0], [0.5, 6.8], [0, 7.2]], lead, 0, 58.1, 0, 12));
  t.add(cone(1.3, 2.4, gold, 0, 62.3, 0, 8));
  t.add(cyl(0.25, 0.25, 1.0, gold, 0, 64.0, 0, 6));
  for (const a of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) t.add(pinnacle(1.2, 4.4, pale, a[0] * 5.4, 45.6, a[1] * 5.4, 6));
  t.position.set(WF - 3, 0, zs * 24.5);
  g.add(t);
}

// ---------------------------------------------------------------- DOME
const D = new THREE.Group();
D.add(box(44, 34, 44, st, 0, 1.6, 0));
D.add(box(46, 2.0, 46, pale, 0, 33.6, 0));
D.add(cyl(21.5, 22.5, 4.0, st, 0, 35.6, 0, 24));
// drum wall + peristyle (32 columns)
D.add(cyl(18.5, 18.5, 15.0, st, 0, 39.6, 0, 24));
D.add(ringColonnade(32, 20.4, 1.05, 13.0, pale, 0, 40.2, 0, 6));
D.add(cyl(21.6, 21.6, 2.2, pale, 0, 53.2, 0, 24));       // stone gallery entablature
const bal = new THREE.Mesh(new THREE.CylinderGeometry(21.8, 21.8, 1.8, 24, 1, true), pale);
bal.position.y = 56.3; D.add(bal);
// attic stage above the peristyle
D.add(cyl(17.0, 17.6, 8.5, st, 0, 55.4, 0, 24));
D.add(cyl(18.0, 18.0, 1.6, pale, 0, 63.9, 0, 24));
// the dome itself, lead, top of the masonry at ~85 m
D.add(lathe([[17.2, 0], [17.1, 1.5], [16.7, 4], [16.0, 7], [15.0, 10], [13.7, 13],
  [12.0, 15.8], [9.9, 18.3], [7.4, 20.3], [5.4, 21.5]], lead, 0, 65.5, 0, 24));
// golden gallery + lantern
D.add(cyl(5.4, 5.8, 3.2, pale, 0, 87.0, 0, 16));
D.add(cyl(4.4, 4.4, 8.0, st, 0, 90.2, 0, 12));
D.add(ringColonnade(8, 5.0, 0.62, 8.0, pale, 0, 90.2, 0, 6));
D.add(cyl(5.6, 5.6, 1.6, pale, 0, 98.2, 0, 16));
D.add(lathe([[4.0, 0], [3.6, 1.2], [2.8, 2.6], [1.8, 3.8], [1.0, 4.6], [0.4, 5.2], [0, 5.6]], lead, 0, 99.8, 0, 12));
D.add(cyl(1.0, 1.0, 1.6, gold, 0, 105.4, 0, 8));
D.add(finialBallCross(1.2, 3.4, gold, 0, 107.0, 0));
D.position.set(XC, 0, 0);
g.add(D);

await exportGLB(g, OUT + 'st_pauls_cathedral.glb');
