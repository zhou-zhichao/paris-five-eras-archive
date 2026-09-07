// Charing Cross station, 1864: E. M. Barry's French-Renaissance hotel front on the Strand
// with Hawkshaw's single-span arched train shed behind, and the Eleanor Cross in the forecourt.
// Orientation: the HOTEL FRONT faces +Z (the Strand); the ~155 m shed runs away to -Z
// towards the river.  Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, hipRoof, THREE,
  P, M, column, pediment, pinnacle, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), bk = M(P.stock),
  gl = M(P.glassroof), iron = M(P.iron), dark = M(0x3a3630), lead = M(P.lead), slate = M(P.slate);

const SPAN = 50, SHEDL = 155, SPRING = 8, RISE = 20;
const Z0 = 20;                                   // shed south end (behind the hotel)
const ZC = Z0 - SHEDL / 2;
const W = SPAN + 8;

// viaduct + platforms
g.add(box(W, 6.0, SHEDL, bk, 0, 0, ZC));
g.add(box(W, 1.0, SHEDL, M(0x6b6660), 0, 6.0, ZC));
for (const sx of [-1, 1]) {
  g.add(box(3.0, SPRING + 4, SHEDL, bk, sx * (W / 2 - 1.5), 6.0, ZC));
  for (let i = 0; i < 15; i++) g.add(box(3.8, SPRING + 6, 2.0, dk, sx * (W / 2 - 1.5), 6.0, Z0 - 6 - i * 10.4));
}

// ---------------------------------------------------------------- the arched glazed shed
{
  const n = 16, pts = [];
  for (let i = 0; i <= n; i++) { const t = -1 + 2 * i / n; pts.push([t * SPAN / 2, RISE * Math.sqrt(Math.max(0, 1 - t * t))]); }
  const s = new THREE.Shape();
  s.moveTo(-SPAN / 2, 0);
  for (const [x, y] of pts) s.lineTo(x, y);
  s.lineTo(SPAN / 2, 0); s.closePath();
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: SHEDL, bevelEnabled: false }), gl);
  m.position.set(0, 6.0 + SPRING, ZC - SHEDL / 2);
  g.add(m);
  for (let r = 0; r <= 15; r++) {
    const z = ZC - SHEDL / 2 + r * SHEDL / 15;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
      const len = Math.hypot(x1 - x0, y1 - y0);
      const b = box(len, 0.7, 0.9, iron, (x0 + x1) / 2, 6.0 + SPRING + (y0 + y1) / 2 - 0.35, z);
      b.rotation.z = Math.atan2(y1 - y0, x1 - x0);
      g.add(b);
    }
  }
  g.add(box(1.6, 1.0, SHEDL, lead, 0, 6.0 + SPRING + RISE + 0.5, ZC));
  const ng = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.2, bevelEnabled: false }), dark);
  ng.position.set(0, 6.0 + SPRING, ZC - SHEDL / 2 - 1.2);
  g.add(ng);
}

// ---------------------------------------------------------------- Charing Cross Hotel (+z)
{
  const HW = 62, HD = 22, HH = 26, FZ = Z0 + 2 + HD;
  g.add(box(HW, HH, HD, st, 0, 0, Z0 + 2 + HD / 2));
  g.add(box(HW + 1.8, 1.8, HD + 1.8, pale, 0, HH, Z0 + 2 + HD / 2));
  g.add(box(HW - 2, 7.5, HD - 3, slate, 0, HH + 1.8, Z0 + 2 + HD / 2));      // mansard
  g.add(box(HW - 8, 1.2, HD - 8, lead, 0, HH + 9.3, Z0 + 2 + HD / 2));
  for (let i = 0; i < 11; i++) {
    const x = -HW / 2 + 4 + i * (HW - 8) / 10;
    g.add(box(2.8, 3.6, 2.8, slate, x, HH + 2.2, FZ - 3));
    g.add(box(2.0, 2.2, 0.5, dark, x, HH + 3.0, FZ - 1.7));
  }
  for (let s2 = 0; s2 < 6; s2++) {
    const y = 2.5 + s2 * 3.8;
    for (let i = 0; i < 14; i++) {
      const x = -HW / 2 + 3 + i * (HW - 6) / 13;
      g.add(box(2.0, 2.6, 0.6, dark, x, y, FZ + 0.1));
      g.add(box(2.0, 2.6, 0.6, dark, x, y, Z0 + 1.9));
    }
  }
  // end and centre pavilions with steep pyramidal roofs
  for (const px of [-HW / 2 + 8, 0, HW / 2 - 8]) {
    g.add(box(17, HH + 2, HD + 3, st, px, 0, Z0 + 2 + HD / 2));
    g.add(box(18.4, 1.6, HD + 4.6, pale, px, HH + 2, Z0 + 2 + HD / 2));
    g.add(hipRoof(17, HD + 3, 9.5, slate, px, HH + 3.6, Z0 + 2 + HD / 2, 0.15));
    g.add(cyl(0.3, 0.3, 2.6, iron, px, HH + 13.1, Z0 + 2 + HD / 2, 6));
  }
  // forecourt with the Victorian Eleanor Cross (~21 m)
  g.add(box(HW + 6, 0.4, 16, dk, 0, 0, FZ + 9));
  const C = new THREE.Group();
  for (let i = 0; i < 3; i++) C.add(cyl(4.4 - i * 0.7, 4.8 - i * 0.7, 0.7, dk, 0, i * 0.7, 0, 8));
  C.add(cyl(3.0, 3.4, 5.0, pale, 0, 2.1, 0, 8));
  for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; C.add(box(1.0, 4.0, 0.5, dark, Math.cos(a) * 3.1, 2.6, Math.sin(a) * 3.1)); }
  C.add(cyl(3.8, 3.8, 0.8, pale, 0, 7.1, 0, 8));
  C.add(cyl(2.2, 2.6, 4.6, pale, 0, 7.9, 0, 8));
  for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; C.add(pinnacle(0.5, 2.6, pale, Math.cos(a) * 2.5, 12.5, Math.sin(a) * 2.5, 6)); }
  C.add(cyl(1.4, 1.8, 3.4, pale, 0, 12.5, 0, 8));
  C.add(cone(1.5, 3.6, pale, 0, 15.9, 0, 8));
  C.add(box(0.35, 2.2, 0.35, M(P.gold), 0, 19.5, 0));
  C.add(box(1.2, 0.35, 0.35, M(P.gold), 0, 20.4, 0));
  C.position.set(0, 0.4, FZ + 9);
  g.add(C);
}

await exportGLB(g, OUT + 'charing_cross_station.glb');
