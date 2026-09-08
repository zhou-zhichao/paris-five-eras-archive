// Generic 1930s-to-modern London suburban station: two 200 m island platforms (4 faces),
// flat concrete canopies, a glazed ticket hall on +z with a concrete-framed bridge over
// the tracks.  Tracks along x.
import {
  exportGLB, box, cyl, THREE, P, M, canopyX, tracksX, OUT,
  centreXZ,} from './_lib_rail.mjs';

const g = new THREE.Group();
const L = 200, W = 34;
const conc = M(P.concrete), dconc = M(P.dconcrete), pf = M(P.platform),
  gl = M(P.glass), dgl = M(P.darkglass), st = M(P.steelwhite), ir = M(P.iron), br = M(P.stock);

// ---- track bed with four tracks
g.add(box(L + 60, 0.6, W, M(P.ballast), 0, -0.6, 0));
const PZ = [-9.5, 9.5];            // two island platforms
const PW = 11.0;
for (const cz of PZ) {
  g.add(box(L, 1.0, PW, pf, 0, 0, cz));
  for (const sz of [-1, 1]) g.add(box(L, 1.0, 0.4, M(0xd8d2c2), 0, 0, cz + sz * (PW / 2 - 0.2)));
  for (const sz of [-1, 1]) {
    const tz = cz + sz * (PW / 2 + 2.6);
    g.add(box(L + 60, 0.25, 0.18, M(P.rail), 0, 0, tz - 0.72));
    g.add(box(L + 60, 0.25, 0.18, M(P.rail), 0, 0, tz + 0.72));
  }
  // flat concrete canopy, cantilevered off a single row of columns
  for (let i = 0; i < 13; i++) g.add(cyl(0.3, 0.34, 4.4, conc, -L / 2 + 10 + i * 15, 1.0, cz, 8));
  g.add(box(L - 16, 0.5, 2.0, dconc, 0, 5.4, cz));
  g.add(box(L - 16, 0.7, PW + 3.0, conc, 0, 5.4, cz));
  g.add(box(L - 16, 0.45, 0.4, st, 0, 5.1, cz + (PW + 3.0) / 2));
  g.add(box(L - 16, 0.45, 0.4, st, 0, 5.1, cz - (PW + 3.0) / 2));
  // platform kiosk / waiting shelter
  g.add(box(16, 3.0, 6.0, dgl, 12, 1.0, cz));
  g.add(box(16.8, 0.35, 6.8, st, 12, 4.0, cz));
  // signage masts
  for (let i = 0; i < 5; i++) g.add(cyl(0.12, 0.12, 7.0, ir, -L / 2 + 20 + i * 38, 1.0, cz + PW / 2 - 1.0, 6));
}

// ---- glazed ticket hall on +z
{
  const HW = 34, HD = 16, HH = 8.5, HZ = W / 2 + HD / 2 - 1;
  g.add(box(HW, 1.2, HD + 6, conc, 0, 0, HZ + 2));                   // podium
  g.add(box(HW, HH, HD, gl, 0, 1.2, HZ));
  for (let i = 0; i < 11; i++) g.add(box(0.45, HH, HD + 0.6, st, -HW / 2 + 1 + i * (HW - 2) / 10, 1.2, HZ));
  g.add(box(HW - 4, 1.6, HD - 3, br, 0, 1.2, HZ - 1));               // brick core behind the glass
  g.add(box(HW + 3.0, 0.8, HD + 3.0, conc, 0, 1.2 + HH, HZ));        // oversailing flat roof
  g.add(box(HW + 3.4, 0.35, HD + 3.4, st, 0, 1.2 + HH + 0.8, HZ));
  // entrance canopy
  g.add(box(14, 0.5, 5.0, conc, 0, 5.4, HZ + HD / 2 + 2.5));
  for (const sx of [-1, 1]) g.add(cyl(0.25, 0.25, 5.4, st, sx * 6, 1.2, HZ + HD / 2 + 4.5, 8));
}

// ---- concrete/steel bridge from the ticket hall over the tracks, with stairs down
{
  const BY = 9.0, BW = 4.5;
  g.add(box(BW, 1.0, W + 10, conc, -24, BY, 0));
  for (const sz of [-1, 1]) g.add(box(BW + 0.6, 1.5, 0.35, ir, -24, BY + 1.0, 0));
  for (const sx of [-1, 1]) g.add(box(0.35, 1.5, W + 10, dgl, -24 + sx * BW / 2, BY + 1.0, 0));
  g.add(box(BW + 1.2, 0.4, W + 10, st, -24, BY + 2.9, 0));           // light roof
  for (const cz of [...PZ, W / 2 + 3])
    for (const sx of [-1, 1]) g.add(cyl(0.28, 0.28, BY, conc, -24 + sx * 1.8, 1.0, cz, 8));
  // stairs down to each island platform, running along x
  for (const cz of PZ) for (let i = 0; i < 10; i++)
    g.add(box(1.4, 0.36, BW, conc, -24 + 2.2 + i * 1.4, 1.0 + (BY - 1.0) * (9 - i) / 10, cz));
}

await exportGLB(centreXZ(g), OUT + 'suburban_station_b.glb');
