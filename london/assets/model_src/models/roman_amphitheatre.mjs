// Roman amphitheatre of Londinium (Guildhall Yard, c. AD 70, rebuilt in stone c.120).
// Elliptical ~100 x 85 m overall, arena ~62 x 43 m, raked timber/stone seating on
// an earth bank ~8 m high, with two vaulted entrance passages on the long axis.
// FRONT = +z (the long axis runs east-west along x; the two entrance passages are
// at -x and +x).  Ground y=0.
import { exportGLB, out, M, box, cyl, group, THREE } from './_lib_london.mjs';

import { mat } from '../export_glb.mjs';
const stone = M.rag, wallM = M.medieval, timber = M.timber, dark = M.dark;
const arenaM = mat(0xd8c9a6), seatM = mat(0xc2b79c);

const A_OUT = 50, B_OUT = 42.5;     // 100 x 85 m
const A_IN = 31, B_IN = 21.5;       // arena 62 x 43 m
const GAP = 0.14;                   // half-angle of the entrance gaps (radians)

const g = new THREE.Group();

// ---- helper: elliptical annulus sector, extruded from y to y+h ---------------
function arcRing(ai, bi, ao, bo, h, m, y, a0, a1, seg = 26) {
  const s = new THREE.Shape();
  for (let i = 0; i <= seg; i++) { const t = a0 + (a1 - a0) * i / seg; const p = [ao * Math.cos(t), bo * Math.sin(t)]; i ? s.lineTo(p[0], p[1]) : s.moveTo(p[0], p[1]); }
  for (let i = seg; i >= 0; i--) { const t = a0 + (a1 - a0) * i / seg; s.lineTo(ai * Math.cos(t), bi * Math.sin(t)); }
  s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: false });
  geo.rotateX(-Math.PI / 2);
  const me = new THREE.Mesh(geo, m); me.position.set(0, y, 0); return me;
}

// ---- arena floor and podium wall --------------------------------------------
{
  const s = new THREE.Shape();
  for (let i = 0; i <= 32; i++) { const t = i / 32 * Math.PI * 2; const p = [A_IN * Math.cos(t), B_IN * Math.sin(t)]; i ? s.lineTo(p[0], p[1]) : s.moveTo(p[0], p[1]); }
  const geo = new THREE.ExtrudeGeometry(s, { depth: 0.3, bevelEnabled: false }); geo.rotateX(-Math.PI / 2);
  g.add(new THREE.Mesh(geo, arenaM));
}

// ---- raked seating: four stepped tiers, split into two halves ----------------
const STEPS = [
  [A_IN, B_IN, 34.5, 25.5, 2.4],
  [34.5, 25.5, 38.5, 30.0, 4.2],
  [38.5, 30.0, 42.5, 34.5, 6.0],
  [42.5, 34.5, 46.5, 38.8, 7.8],
];
const halves = [[GAP, Math.PI - GAP], [Math.PI + GAP, Math.PI * 2 - GAP]];
for (const [a0, a1] of halves) {
  // podium wall around the arena (dark, 2 m)
  g.add(arcRing(A_IN, B_IN, A_IN + 1.4, B_IN + 1.2, 2.6, wallM, 0, a0, a1, 26));
  for (const [ai, bi, ao, bo, h] of STEPS) g.add(arcRing(ai, bi, ao, bo, h, seatM, 0, a0, a1, 26));
  // outer retaining wall
  g.add(arcRing(46.5, 38.8, A_OUT, B_OUT, 9.4, stone, 0, a0, a1, 30));
  // parapet
  g.add(arcRing(A_OUT - 1.4, B_OUT - 1.2, A_OUT, B_OUT, 10.6, stone, 0, a0, a1, 30));
  // timber seating-rail hints: a dark band on the top tier
  g.add(arcRing(44.6, 36.9, 46.4, 38.7, 8.5, timber, 0, a0, a1, 24));
}

// ---- two entrance passages on the long axis ---------------------------------
for (const sx of [-1, 1]) {
  const pw = 5.0;                 // clear width
  const x0 = sx * A_IN, x1 = sx * (A_OUT + 4);
  const len = Math.abs(x1 - x0);
  const cx = (x0 + x1) / 2;
  // side walls of the passage
  for (const sz of [-1, 1]) g.add(box(len, 6.2, 1.6, wallM, cx, 0, sz * (pw / 2 + 0.8)));
  // dark floor of the passage
  g.add(box(len, 0.3, pw, dark, cx, 0, 0));
  // barrel vault over the inner half (full cylinder; its lower half is buried
  // inside the passage) plus the earth/seating bank carried over it
  {
    const vl = len * 0.55, vx = sx * ((A_IN + A_OUT) / 2 + 1);
    const v = cyl(pw / 2 + 0.8, pw / 2 + 0.8, vl, wallM, 0, 0, 0, 12);
    v.rotation.z = Math.PI / 2; v.position.set(vx, 6.2, 0);
    g.add(v);
    g.add(box(vl, 2.6, pw + 3.2, seatM, vx, 6.7, 0));
  }
  // monumental stone gateway at the outer end
  const gx = sx * (A_OUT + 1.2);
  for (const sz of [-1, 1]) g.add(box(4.5, 10.5, 5.5, stone, gx, 0, sz * (pw / 2 + 3.0)));
  g.add(box(4.5, 3.0, pw + 11.0, stone, gx, 7.6, 0));
  const arch = cyl(pw / 2 + 0.6, pw / 2 + 0.6, 4.6, stone, 0, 0, 0, 12);
  arch.rotation.z = Math.PI / 2; arch.position.set(gx, 5.2, 0); g.add(arch);
  g.add(box(5.4, 1.2, pw + 12.0, stone, gx, 10.6, 0));
}

await exportGLB(g, out('roman_amphitheatre'));
