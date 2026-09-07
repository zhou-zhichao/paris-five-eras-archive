// County Hall, Ralph Knott, 1911-22.  Edwardian Baroque, Portland stone over a granite base.
// Orientation: the ~230 m RIVER FRONT, with its great crescent-shaped recessed colonnade,
// faces +Z (the Thames).  Six storeys plus mansards; ~30 m to the cornice.
// Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, hipRoof, THREE,
  P, M, column, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), gran = M(0x7d7367), slate = M(P.slate),
  lead = M(P.lead), dark = M(0x4a463d), dk = M(P.dstone);

const W = 230, H = 28, D = 110;
const FZ = D / 2;
const R = 150;                    // radius of the crescent, centre well behind the front

// ---------------------------------------------------------------- main mass
g.add(box(W + 4, 2.0, D + 4, gran, 0, 0, 0));
// wings behind
g.add(box(W, H, 46, st, 0, 2.0, -D / 2 + 23));
g.add(box(W + 1.8, 1.8, 47.8, pale, 0, 2.0 + H, -D / 2 + 23));
g.add(box(W - 2, 8.0, 42, slate, 0, 3.8 + H, -D / 2 + 23));
for (const sx of [-1, 1]) {
  g.add(box(46, H, D - 40, st, sx * (W / 2 - 23), 2.0, 12));
  g.add(box(47.8, 1.8, D - 38.2, pale, sx * (W / 2 - 23), 2.0 + H, 12));
  g.add(box(42, 8.0, D - 44, slate, sx * (W / 2 - 23), 3.8 + H, 12));
}
g.add(box(W - 92, H, 40, st, 0, 2.0, -6));            // inner block behind the crescent

// ---------------------------------------------------------------- the curved (crescent) river front
{
  const zC = FZ + R - 26;         // arc centre out in the river: the crescent is CONCAVE
  const n = 26;
  const aSpan = 2 * Math.asin((W - 96) / 2 / R);
  for (let i = 0; i <= n; i++) {
    const a = -aSpan / 2 + aSpan * i / n;
    const px = Math.sin(a) * R, pz = zC - Math.cos(a) * R;
    // the wall segment
    const seg = box((R * aSpan / n) + 1.2, H, 6.0, st, px, 2.0, pz);
    seg.rotation.y = -a; g.add(seg);
    // giant Ionic columns standing in front of it
    if (i < n) {
      const a2 = -aSpan / 2 + aSpan * (i + 0.5) / n;
      const cx = Math.sin(a2) * R, cz = zC - Math.cos(a2) * (R - 4.0);
      g.add(column(1.15, 15.0, pale, cx, 10.0, cz, 10));
      const w1 = box(3.2, 5.0, 0.6, dark, Math.sin(a2) * R, 3.5, zC - Math.cos(a2) * (R - 0.4));
      w1.rotation.y = -a2; g.add(w1);
      const w2 = box(3.2, 4.0, 0.6, dark, Math.sin(a2) * R, 11.5, zC - Math.cos(a2) * (R - 0.4));
      w2.rotation.y = -a2; g.add(w2);
      const w3 = box(3.0, 3.4, 0.6, dark, Math.sin(a2) * R, 22.5, zC - Math.cos(a2) * (R - 0.4));
      w3.rotation.y = -a2; g.add(w3);
    }
    // entablature and balustrade over the columns
    const e = box((R * aSpan / n) + 1.4, 3.0, 9.0, pale, px, 25.0, zC - Math.cos(a) * (R - 2.0));
    e.rotation.y = -a; g.add(e);
    const b = box((R * aSpan / n) + 1.4, 2.4, 9.0, pale, px, 30.0, zC - Math.cos(a) * (R - 2.0));
    b.rotation.y = -a; g.add(b);
    const rf = box((R * aSpan / n) + 1.4, 7.0, 7.0, slate, px, 32.4, zC - Math.cos(a) * (R - 0.5));
    rf.rotation.y = -a; g.add(rf);
  }
}

// ---------------------------------------------------------------- the end pavilions with pyramid roofs
for (const sx of [-1, 1]) {
  const px = sx * (W / 2 - 22);
  g.add(box(44, H + 4, 44, st, px, 2.0, FZ - 22));
  g.add(box(45.8, 2.0, 45.8, pale, px, 2.0 + H + 4, FZ - 22));
  g.add(balustrade(45.8, 45.8, 2.4, pale, px, 4.0 + H + 4, FZ - 22));
  g.add(hipRoof(40, 40, 13.0, slate, px, 6.4 + H + 4, FZ - 22, 0.2));
  g.add(cyl(1.4, 1.8, 2.4, pale, px, 51.4, FZ - 22, 10));
  g.add(cone(1.6, 2.4, lead, px, 53.8, FZ - 22, 10));
  // giant columns on the pavilion faces
  for (let i = 0; i < 4; i++) g.add(column(1.15, 15.0, pale, px - 12 + i * 8, 10.0, FZ + 0.5, 10));
  g.add(box(38, 3.0, 4.0, pale, px, 25.0, FZ + 0.5));
  // rusticated granite base and window tiers
  g.add(box(44.4, 8.0, 44.4, gran, px, 2.0, FZ - 22));
  for (let i = 0; i < 5; i++) {
    const x = px - 17 + i * 8.5;
    g.add(box(2.8, 4.0, 0.6, dark, x, 3.5, FZ + 0.1));
    g.add(box(2.6, 3.4, 0.6, dark, x, 22.5, FZ + 0.1));
  }
  for (let i = 0; i < 6; i++) {
    const z = FZ - 40 + i * 7.5;
    for (const y of [3.5, 12.0, 22.5]) g.add(box(0.6, 3.6, 2.6, dark, sx * (W / 2 + 0.1), y, z));
  }
}
// rusticated granite base along the whole river frontage
g.add(box(W, 8.0, 6.0, gran, 0, 2.0, FZ - 3));
// window tiers on the rear elevation
for (let i = 0; i < 34; i++) {
  const x = -W / 2 + 4 + i * (W - 8) / 33;
  for (const y of [5.0, 12.0, 19.0, 25.0]) g.add(box(2.4, 3.4, 0.6, dark, x, y, -D / 2 - 0.1));
}

await exportGLB(g, OUT + 'county_hall.glb');
