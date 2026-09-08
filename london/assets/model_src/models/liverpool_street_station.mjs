// LIVERPOOL STREET, Edward Wilson for the Great Eastern Railway, 1874-75.
// Four spans of pointed Gothic iron-and-glass roof on slender cast-iron columns, with
// brick gables and spirelets at the buffer end, and Charles Barry jr's red-brick Great
// Eastern Hotel (1884) along the street front.
// Orientation: platforms along x, tracks leaving to -x, buffer stops at +x, the hotel
// front facing +z.  ~200 x 180 m.
import {
  exportGLB, box, cyl, cone, dome, lathe, hipRoof, gableRoof, THREE, P, M,
  shedX, platformsX, openWall, arcade, pediment, balustrade, spire, pinnacle,
  winGridZ, winGridX, bufferStops, chimney, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const SX0 = -100, SX1 = 62, SL = SX1 - SX0, SCX = (SX0 + SX1) / 2;
const SPANS = [[-49.5, 32, 17], [-16.5, 32, 18.5], [16.5, 32, 18.5], [49.5, 32, 17]];
const SW = 132, SCZ = -18;                   // shed centred on z = -18
const SPRING = 8.0;

const bk = M(P.stock), rb = M(P.red), rbd = M(P.reddark), st = M(P.stone),
  pale = M(P.pale), dst = M(P.dstone), gl = M(P.glassroof), ir = M(P.iron),
  sl = M(P.slate), dk = M(P.dark), dgl = M(P.darkglass), tc = M(P.terracotta);

// ---------------------------------------------------------------- platforms (Liverpool St sits in a cutting)
g.add(box(SL + 24, 0.6, SW + 8, M(P.ballast), SCX + 6, -0.6, SCZ));
g.add(platformsX(SL + 16, SW - 10, 9, SCX + 6, 0, SCZ, { pw: 8.5 }));
g.add(bufferStops(SW - 24, 9, SX1 + 1, 0, SCZ));

// ---------------------------------------------------------------- the four Gothic iron spans
for (const [dz, span, rise] of SPANS) {
  g.add(shedX(SL, span, rise, SCX, SPRING, SCZ + dz, {
    segs: 12, ribs: 14, gableAMat: P.dark, gableBMat: P.glassroof,
  }));
}
// arcaded cast-iron column lines between the spans
for (const cz of [SCZ - 33, SCZ, SCZ + 33]) {
  for (let i = 0; i < 15; i++) {
    const x = SX0 + SL * (i + 0.5) / 15;
    g.add(cyl(0.45, 0.6, SPRING, ir, x, 0, cz, 8));
    g.add(box(1.4, 0.9, 1.4, ir, x, SPRING - 0.9, cz));
  }
  g.add(box(SL, 1.0, 1.1, ir, SCX, SPRING, cz));
}
// Gothic brick side walls with buttresses and pointed windows
for (const sz of [-1, 1]) {
  const zz = SCZ + sz * (SW / 2 - 1.4);
  const ops = [];
  for (let i = 0; i < 15; i++) ops.push({ cx: -SL / 2 + SL * (i + 0.5) / 15, y0: 3.0, w: 3.4, h: 4.0, arch: 'pointed' });
  g.add(openWall(SL, SPRING + 5.5, 2.8, bk, ops, SCX, 0, zz, 6));
  for (let i = 0; i <= 15; i++)
    g.add(box(2.2, SPRING + 8.5, 3.8, rbd, SX0 + SL * i / 15, 0, zz));
  g.add(box(SL, 0.9, 3.8, dst, SCX, SPRING + 8.5, zz));
}

// ---------------------------------------------------------------- buffer-end gables and spirelets (+x)
for (const [dz, span, rise] of SPANS) {
  const zz = SCZ + dz;
  g.add(box(2.0, SPRING + rise + 5.5, span + 2.5, rb, SX1 + 1.5, 0, zz));      // brick gable wall
  // pointed gable head
  const s = new THREE.Shape();
  s.moveTo(-span / 2 - 1.2, 0); s.lineTo(span / 2 + 1.2, 0); s.lineTo(0, 9.0); s.closePath();
  const gm = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 2.0, bevelEnabled: false }), rb);
  const gg = new THREE.Group(); gg.add(gm); gm.position.z = -1.0;
  gg.rotation.y = Math.PI / 2; gg.position.set(SX1 + 1.5, SPRING + rise + 5.5, zz);
  g.add(gg);
  // rose / lunette in the gable
  g.add(cyl(3.2, 3.2, 2.4, gl, SX1 + 1.5, SPRING + rise + 6.0, zz, 12).rotateZ(Math.PI / 2));
}
// the four corner spirelets of the Liverpool Street frontage
for (const dz of [-66, -33, 0, 33, 66]) {
  const zz = SCZ + dz;
  g.add(box(6.5, 34, 6.5, rb, SX1 + 3.0, 0, zz));
  g.add(box(7.4, 1.2, 7.4, dst, SX1 + 3.0, 34, zz));
  g.add(box(5.6, 4.5, 5.6, rb, SX1 + 3.0, 35.2, zz));
  g.add(cone(4.4, 9.0, sl, SX1 + 3.0, 39.7, zz, 8));
  g.add(cyl(0.25, 0.3, 2.0, ir, SX1 + 3.0, 48.7, zz, 6));
}

// ---------------------------------------------------------------- Great Eastern Hotel (1884) on +z
{
  const HZ = 68, HD = 24, HW = 150, HH = 30, HX = -12;
  g.add(box(HW, HH, HD, rb, HX, 0, HZ));
  g.add(box(HW + 2.0, 1.4, HD + 2.4, dst, HX, HH, HZ));
  g.add(box(HW - 3, 7.5, HD - 3, sl, HX, HH + 1.4, HZ));                       // mansard
  g.add(box(HW - 40, 1.2, HD - 12, M(P.lead), HX, HH + 8.9, HZ));
  for (let i = 0; i < 19; i++) {                                               // dormers
    const x = HX - HW / 2 + HW * (i + 0.5) / 19;
    g.add(box(3.0, 3.4, 2.6, sl, x, HH + 2.2, HZ + HD / 2 - 1.4));
    g.add(box(2.2, 2.4, 0.5, dgl, x, HH + 2.8, HZ + HD / 2 + 0.1));
  }
  // storeys of windows and stone bands
  g.add(winGridZ(19, 5, 7.6, 4.6, 2.6, 3.2, P.darkglass, HX, 5.0, HZ + HD / 2));
  g.add(winGridZ(19, 5, 7.6, 4.6, 2.6, 3.2, P.darkglass, HX, 5.0, HZ - HD / 2));
  for (const yy of [4.2, 27.6]) g.add(box(HW + 0.8, 0.9, HD + 0.8, dst, HX, yy, HZ));
  g.add(box(HW - 4, 3.8, HD + 1.2, dst, HX, 0.3, HZ));                        // stone ground floor
  // projecting centre bay with a pedimented gable, and end pavilions
  g.add(box(24, HH + 3.5, HD + 5.0, rbd, HX, 0, HZ));
  g.add(pediment(26, 6.5, HD + 5.0, dst, HX, HH + 3.5, HZ));
  g.add(box(24, 4.6, 0.7, dgl, HX, 3.0, HZ + HD / 2 + 2.6));
  for (const sx of [-1, 1]) {
    g.add(box(20, HH + 2.0, HD + 3.5, rb, HX + sx * (HW / 2 - 10), 0, HZ));
    g.add(hipRoof(20, HD + 3.5, 9.0, sl, HX + sx * (HW / 2 - 10), HH + 2.0, HZ, 0.25));
    g.add(chimney(3.4, 2.0, 4.0, P.reddark, HX + sx * (HW / 2 - 10), HH + 8.0, HZ, 4));
  }
  for (const sx of [-1, 1]) g.add(chimney(3.0, 2.0, 3.6, P.reddark, HX + sx * 42, HH + 5.0, HZ, 4));
}

// low brick offices closing the -z side of the cutting
g.add(box(SL, 12.0, 16, bk, SCX, 0, SCZ - SW / 2 - 8));
g.add(box(SL + 2, 1.0, 17, dst, SCX, 12.0, SCZ - SW / 2 - 8));
g.add(hipRoof(SL, 16, 4.5, sl, SCX, 13.0, SCZ - SW / 2 - 8, 0.7));

await exportGLB(centreXZ(g), OUT + 'liverpool_street_station.glb');
