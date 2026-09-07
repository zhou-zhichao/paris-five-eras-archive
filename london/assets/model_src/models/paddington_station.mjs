// Paddington station, I. K. Brunel with M. D. Wyatt, 1854, and the Great Western Royal Hotel.
// Orientation: the HOTEL front faces +Z (Praed Street); the three glazed barrel vaults
// (~210 m long, ~96 m overall width) run away behind it towards -Z, crossed by two transepts.
// Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, hipRoof, gableRoof, THREE,
  P, M, column, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const gl = M(P.glassroof), iron = M(P.iron), ironl = M(0x6d7276), bk = M(P.stock),
  pale = M(P.pale), st = M(P.stone), slate = M(P.slate), dark = M(0x33302b), lead = M(P.lead);

const SHEDL = 210, SPRING = 7.5;
const SPANS = [[-31, 26, 13.5], [0, 36, 18.5], [31, 26, 13.5]];   // [centre x, span, rise]
const W = 96;
const Z0 = 4, ZC = Z0 - SHEDL / 2;

// platforms
g.add(box(W, 1.0, SHEDL, M(0x6b6660), 0, 0, ZC));

function vaultShape(span, rise, n = 16) {
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const t = -1 + 2 * i / n;
    pts.push([t * span / 2, rise * Math.sqrt(Math.max(0, 1 - t * t))]);
  }
  const s = new THREE.Shape();
  s.moveTo(-span / 2, 0);
  for (const [x, y] of pts) s.lineTo(x, y);
  s.lineTo(span / 2, 0); s.closePath();
  return { s, pts };
}

// ---------------------------------------------------------------- the three longitudinal vaults
for (const [cx, span, rise] of SPANS) {
  const { s, pts } = vaultShape(span, rise);
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: SHEDL, bevelEnabled: false }), gl);
  m.position.set(cx, SPRING, ZC - SHEDL / 2);
  g.add(m);
  for (let r = 0; r <= 18; r++) {
    const z = ZC - SHEDL / 2 + r * SHEDL / 18;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
      const len = Math.hypot(x1 - x0, y1 - y0);
      const b = box(len, 0.7, 0.9, iron, cx + (x0 + x1) / 2, SPRING + (y0 + y1) / 2 - 0.35, z);
      b.rotation.z = Math.atan2(y1 - y0, x1 - x0);
      g.add(b);
    }
    // iron columns carrying the arcades between the vaults
    if (cx === 0) for (const sx of [-1, 1]) g.add(cyl(0.55, 0.7, SPRING, iron, sx * 18, 1.0, z, 8));
  }
  g.add(box(1.4, 1.0, SHEDL, lead, cx, SPRING + rise + 0.5, ZC));
  // north gable screen
  const ng = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.0, bevelEnabled: false }), dark);
  ng.position.set(cx, SPRING, ZC - SHEDL / 2 - 1.0);
  g.add(ng);
  // south (station-end) glazed screen
  const sg = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.0, bevelEnabled: false }), gl);
  sg.position.set(cx, SPRING, Z0);
  g.add(sg);
}
// side walls
for (const sx of [-1, 1]) {
  g.add(box(2.4, SPRING + 4, SHEDL, bk, sx * (W / 2 - 1.2), 0, ZC));
  for (let i = 0; i < 20; i++) g.add(box(3.0, SPRING + 6, 1.8, pale, sx * (W / 2 - 1.2), 0, Z0 - 6 - i * 10.2));
}

// ---------------------------------------------------------------- the two transepts
for (const tz of [Z0 - 68, Z0 - 140]) {
  const { s, pts } = vaultShape(22, 12, 12);
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: W - 6 }), gl);
  const grp = new THREE.Group(); grp.add(m);
  m.position.set(0, 0, -(W - 6) / 2);
  grp.rotation.y = Math.PI / 2;
  grp.position.set(0, SPRING + 2, tz);
  g.add(grp);
  for (let r = 0; r <= 10; r++) {
    const x = -(W - 6) / 2 + r * (W - 6) / 10;
    for (let i = 0; i < pts.length - 1; i++) {
      const [z0, y0] = pts[i], [z1, y1] = pts[i + 1];
      const len = Math.hypot(z1 - z0, y1 - y0);
      const b = box(0.9, 0.7, len, iron, x, SPRING + 2 + (y0 + y1) / 2 - 0.35, tz + (z0 + z1) / 2);
      b.rotation.x = -Math.atan2(y1 - y0, z1 - z0);
      g.add(b);
    }
  }
}

// ---------------------------------------------------------------- Great Western Royal Hotel (+z)
{
  const HW = 92, HD = 26, HH = 28, FZ = Z0 + 2 + HD;
  g.add(box(HW, HH, HD, st, 0, 0, Z0 + 2 + HD / 2));
  g.add(box(HW + 1.8, 1.8, HD + 1.8, pale, 0, HH, Z0 + 2 + HD / 2));
  // steep French mansard roof + dormers
  g.add(box(HW - 2, 7.0, HD - 3, slate, 0, HH + 1.8, Z0 + 2 + HD / 2));
  g.add(box(HW - 6, 1.2, HD - 7, lead, 0, HH + 8.8, Z0 + 2 + HD / 2));
  for (let i = 0; i < 15; i++) {
    const x = -HW / 2 + 5 + i * (HW - 10) / 14;
    g.add(box(2.6, 3.2, 2.6, slate, x, HH + 2.4, FZ - 3));
    g.add(box(2.0, 2.0, 0.5, dark, x, HH + 3.2, FZ - 1.8));
  }
  // seven storeys of windows
  for (let s2 = 0; s2 < 7; s2++) {
    const y = 2.5 + s2 * 3.6;
    for (let i = 0; i < 19; i++) {
      const x = -HW / 2 + 3.5 + i * (HW - 7) / 18;
      g.add(box(2.0, 2.6, 0.6, dark, x, y, FZ + 0.1));
      g.add(box(2.0, 2.6, 0.6, dark, x, y, Z0 + 1.9));
    }
  }
  // pavilions at the ends and centre, with taller roofs
  for (const px of [-HW / 2 + 9, 0, HW / 2 - 9]) {
    g.add(box(20, HH + 3, HD + 4, st, px, 0, Z0 + 2 + HD / 2));
    g.add(box(21.6, 1.8, HD + 5.8, pale, px, HH + 3, Z0 + 2 + HD / 2));
    g.add(hipRoof(20, HD + 4, 9.0, slate, px, HH + 4.8, Z0 + 2 + HD / 2, 0.2));
    g.add(cyl(0.3, 0.3, 2.4, iron, px, HH + 13.8, Z0 + 2 + HD / 2, 6));
  }
}

await exportGLB(g, OUT + 'paddington_station.glb');
