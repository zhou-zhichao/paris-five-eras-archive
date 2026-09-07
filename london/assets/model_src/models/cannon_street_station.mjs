// Cannon Street station, Sir John Hawkshaw 1866.  The single great arched shed lands on the
// river wall between two tall brick towers with lead cupolas.
// Orientation: the RIVER FRONT with its two ~40 m towers faces +Z; the 200 m shed runs
// away behind it towards -Z to the City Hotel front.  Ground y=0, centred on the origin.
import { exportGLB, box, cyl, cone, lathe, hipRoof, THREE,
  P, M, column, pediment, balustrade, openWall, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const bk = M(0x9a5a48), bkd = M(0x86493a), pale = M(P.pale), st = M(P.stone),
  gl = M(P.glassroof), iron = M(P.iron), dark = M(0x33302b), lead = M(P.lead), slate = M(P.slate);

const SPAN = 58, SHEDL = 200, SPRING = 9, RISE = 23;
const Z0 = 110;                       // river end of the shed (model centred on z)
const ZC = Z0 - SHEDL / 2;
const W = SPAN + 10;

// ---------------------------------------------------------------- viaduct + platforms
g.add(box(W, 8.0, SHEDL, bkd, 0, 0, ZC));
g.add(box(W, 1.0, SHEDL, M(0x6b6660), 0, 8.0, ZC));

// ---------------------------------------------------------------- side walls with buttress piers
for (const sx of [-1, 1]) {
  g.add(box(4.0, SPRING + 5, SHEDL, bk, sx * (W / 2 - 2), 8.0, ZC));
  for (let i = 0; i < 19; i++) g.add(box(5.0, SPRING + 8, 2.2, bkd, sx * (W / 2 - 2), 8.0, Z0 - 6 - i * 10.4));
}

// ---------------------------------------------------------------- the great glazed arch
{
  const n = 18, pts = [];
  for (let i = 0; i <= n; i++) {
    const t = -1 + 2 * i / n;
    pts.push([t * SPAN / 2, RISE * Math.sqrt(Math.max(0, 1 - t * t))]);
  }
  const s = new THREE.Shape();
  s.moveTo(-SPAN / 2, 0);
  for (const [x, y] of pts) s.lineTo(x, y);
  s.lineTo(SPAN / 2, 0); s.closePath();
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: SHEDL, bevelEnabled: false }), gl);
  m.position.set(0, 8.0 + SPRING, ZC - SHEDL / 2);
  g.add(m);
  for (let r = 0; r <= 18; r++) {
    const z = ZC - SHEDL / 2 + r * SHEDL / 18;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
      const len = Math.hypot(x1 - x0, y1 - y0);
      const b = box(len, 0.8, 1.0, iron, (x0 + x1) / 2, 8.0 + SPRING + (y0 + y1) / 2 - 0.4, z);
      b.rotation.z = Math.atan2(y1 - y0, x1 - x0);
      g.add(b);
    }
  }
  g.add(box(1.8, 1.2, SHEDL, lead, 0, 8.0 + SPRING + RISE + 0.6, ZC));
  // the river (south) glazed gable screen
  const sg = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.4, bevelEnabled: false }), gl);
  sg.position.set(0, 8.0 + SPRING, Z0);
  g.add(sg);
  for (let i = 1; i < 9; i++) {
    const t = -1 + 2 * i / 9, mh = RISE * Math.sqrt(Math.max(0, 1 - t * t));
    g.add(box(0.6, mh, 1.6, iron, t * SPAN / 2, 8.0 + SPRING, Z0 + 0.9));
  }
  // the northern gable
  const ng = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.2, bevelEnabled: false }), dark);
  ng.position.set(0, 8.0 + SPRING, ZC - SHEDL / 2 - 1.2);
  g.add(ng);
}

// ---------------------------------------------------------------- the two river towers (~40 m)
for (const sx of [-1, 1]) {
  const tx = sx * (W / 2 + 3.5), tz = Z0 - 5;
  const T = new THREE.Group();
  T.add(box(13, 30, 15, bk, 0, 0, 0));
  for (let s2 = 0; s2 < 4; s2++) for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 3.4, 4.6, dz ? 0.6 : 3.4, dark, dx * 6.6, 4 + s2 * 6.4, dz * 7.6));
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    T.add(box(2.4, 32, 2.4, bkd, dx * 6.0, 0, dz * 7.0));
  T.add(box(14.6, 1.6, 16.6, pale, 0, 30, 0));
  T.add(box(11.6, 4.5, 13.6, bk, 0, 31.6, 0));
  T.add(box(13.0, 1.2, 15.0, pale, 0, 36.1, 0));
  // lead ogee cupola + finial
  T.add(lathe([[6.4, 0], [6.1, 1.4], [5.0, 3.0], [3.2, 4.6], [1.6, 5.6], [0, 6.0]], lead, 0, 37.3, 0, 12));
  T.add(cyl(1.0, 1.3, 1.6, pale, 0, 43.3, 0, 8));
  T.add(cone(1.1, 1.6, lead, 0, 44.9, 0, 8));
  T.add(cyl(0.16, 0.16, 1.4, M(P.gold), 0, 46.5, 0, 6));
  T.position.set(tx, 0, tz);
  g.add(T);
}

// ---------------------------------------------------------------- the hotel block on Cannon Street (-z)
{
  const HZ = ZC - SHEDL / 2 - 12;
  g.add(box(W + 18, 26, 22, st, 0, 0, HZ));
  g.add(box(W + 20, 1.6, 24, pale, 0, 26, HZ));
  g.add(hipRoof(W + 16, 22, 8.0, slate, 0, 27.6, HZ, 0.5));
  for (let s2 = 0; s2 < 6; s2++) for (let i = 0; i < 15; i++) {
    const x = -(W + 14) / 2 + i * (W + 14) / 14;
    g.add(box(2.0, 2.6, 0.6, dark, x, 2.5 + s2 * 3.9, HZ - 11.1));
  }
}

await exportGLB(g, OUT + 'cannon_street_station.glb');
