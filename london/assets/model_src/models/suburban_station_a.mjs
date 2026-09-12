// Generic Victorian London suburban station: two 120 m platforms with ridged timber
// canopies, a stock-brick station house with chimneys on the +z (street) side, and a
// covered iron footbridge across the tracks.  Tracks along x.
import {
  exportGLB, box, cyl, hipRoof, gableRoof, THREE, P, M,
  canopyX, tracksX, footbridgeZ, chimney, winGridZ, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const L = 120, PW = 7.0, GAUGE = 5.0;
const PZ = 6.5;                    // platform centres at z = ±PZ
const bk = M(P.stock), bkd = M(0xa08e6f), st = M(P.dstone), sl = M(P.slate),
  gl = M(P.darkglass), ir = M(P.iron), tim = M(0x6d5136), pf = M(P.platform);

// ---- track bed and the two tracks between the platforms
g.add(box(L + 40, 0.5, 2 * PZ - PW, M(P.ballast), 0, -0.5, 0));
for (const sz of [-1, 1]) {
  const tz = sz * (PZ - PW / 2 - GAUGE / 2 - 0.2);
  g.add(box(L + 40, 0.25, 0.16, M(P.rail), 0, 0, tz - 0.72));
  g.add(box(L + 40, 0.25, 0.16, M(P.rail), 0, 0, tz + 0.72));
}

// ---- the two side platforms
for (const sz of [-1, 1]) {
  g.add(box(L, 1.0, PW, pf, 0, 0, sz * PZ));
  g.add(box(L, 1.0, 0.35, bkd, 0, 0, sz * (PZ - PW / 2)));        // platform edge
  // ridged canopy over the middle third
  g.add(canopyX(52, PW + 2.2, 4.2, 0, 1.0, sz * (PZ + 0.4), { rh: 1.6, roofMat: P.slate, valMat: 0x6d5136 }));
  // low platform buildings / waiting room
  g.add(box(14, 3.2, 4.4, bk, sz * 26, 1.0, sz * (PZ + 0.6)));
  g.add(hipRoof(15, 5.2, 1.6, sl, sz * 26, 4.2, sz * (PZ + 0.6), 0.4));
  g.add(chimney(1.0, 1.0, 1.6, P.stock, sz * 21, 5.0, sz * (PZ + 0.6), 2));
  // lamp posts
  for (let i = 0; i < 7; i++) g.add(cyl(0.1, 0.12, 3.4, ir, -L / 2 + 8 + i * 17, 1.0, sz * (PZ - 2.4), 6));
}

// ---- station house on +z (street level), two storeys with a gabled front
{
  const HW = 22, HD = 11, HH = 7.4, HZ = PZ + PW / 2 + HD / 2 + 0.5;
  g.add(box(HW, HH, HD, bk, 0, 0, HZ));
  g.add(box(HW + 0.9, 0.5, HD + 0.9, st, 0, HH, HZ));
  g.add(hipRoof(HW + 0.9, HD + 0.9, 3.4, sl, 0, HH + 0.5, HZ, 0.35));
  // gabled centre bay with the entrance
  g.add(box(8.0, HH + 1.2, HD + 2.4, bk, 0, 0, HZ));
  g.add(gableRoof(HD + 2.4, 8.0, 3.0, sl, 0, HH + 1.2, HZ, false, 0.35));
  g.add(box(3.2, 4.0, 0.5, M(P.dark), 0, 0.2, HZ + HD / 2 + 1.2));       // doorway
  g.add(box(4.4, 0.5, 1.6, st, 0, 4.2, HZ + HD / 2 + 1.2));              // canopy hood
  // windows
  g.add(winGridZ(3, 2, 5.0, 3.6, 1.6, 2.2, P.darkglass, -7.5, 1.6, HZ + HD / 2));
  g.add(winGridZ(3, 2, 5.0, 3.6, 1.6, 2.2, P.darkglass, 7.5, 1.6, HZ + HD / 2));
  for (const sx of [-1, 1]) g.add(chimney(1.6, 1.2, 2.6, P.stock, sx * 8.5, HH + 2.4, HZ, 3));
  // low forecourt wall
  g.add(box(HW + 14, 1.1, 0.5, bk, 0, 0, HZ + HD / 2 + 9));
}

// ---- covered iron footbridge crossing the tracks near the -x end
g.add(footbridgeZ(2 * PZ + 4, 6.0, -34, 1.0, 0, { roofed: true, legs: 2 }));

await exportGLB(centreXZ(g), OUT + 'suburban_station_a.glb');
