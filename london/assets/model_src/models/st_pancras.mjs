// St Pancras station: Barlow's single-span train shed (1868) + Scott's Midland Grand Hotel (1873).
// Orientation: the Midland Grand Gothic FRONT (Euston Road) faces +Z; the 213 x 74 m shed runs
// away behind it towards -Z.  Ground y=0, footprint centred on the origin.
// Clock tower 82 m (east end, +X), west tower 76 m.  Shed apex ~30 m above the platform deck.
import { exportGLB, box, cyl, cone, lathe, gableRoof, hipRoof, THREE,
  P, M, pinnacle, openWall, OUT } from './_lib_wren_edwardian.mjs';

const g = new THREE.Group();
const bk = M(0x9e5a45), bkd = M(0x86493a), pale = M(P.pale), st = M(P.stone),
  slate = M(P.slate), glass = M(P.glassroof), iron = M(P.iron), dark = M(0x3a3330), lead = M(P.lead);

const SPAN = 74, SHEDL = 213, DECK = 5.5, RISE = 30;
const Z0 = 6;                       // south (front) end of the shed
const ZC = Z0 - SHEDL / 2;          // shed centre in z

// ---------------------------------------------------------------- undercroft / platform deck
g.add(box(SPAN + 6, DECK, SHEDL, bkd, 0, 0, ZC));
for (let i = 0; i < 22; i++) g.add(box(1.6, DECK, 1.6, bk, 0, 0, Z0 - 5 - i * 10));

// ---------------------------------------------------------------- shed side walls
for (const sx of [-1, 1]) {
  g.add(box(3.0, 9, SHEDL, bk, sx * (SPAN / 2 - 1.5), DECK, ZC));
  for (let i = 0; i < 20; i++) g.add(box(3.6, 11, 2.0, bkd, sx * (SPAN / 2 - 1.5), DECK, Z0 - 6 - i * 10.5));
}

// ---------------------------------------------------------------- the great glazed vault
function archProfile(n) {                   // half-span 37, rise 30, slightly pointed crown
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const t = -1 + 2 * i / n;
    const x = t * (SPAN / 2);
    let y = RISE * Math.pow(Math.max(0, 1 - Math.pow(Math.abs(t), 2.2)), 0.44);
    y += 1.6 * Math.max(0, 1 - Math.abs(t) * 5);          // small point at the crown
    pts.push([x, y]);
  }
  return pts;
}
{
  const pts = archProfile(22);
  const s = new THREE.Shape();
  s.moveTo(-SPAN / 2, 0);
  for (const [x, y] of pts) s.lineTo(x, y);
  s.lineTo(SPAN / 2, 0);
  s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, { depth: SHEDL, bevelEnabled: false });
  const m = new THREE.Mesh(geo, glass);
  m.position.set(0, DECK, ZC - SHEDL / 2);
  g.add(m);
  // iron ribs standing slightly proud of the glass
  for (let r = 0; r <= 17; r++) {
    const z = ZC - SHEDL / 2 + r * SHEDL / 17;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
      const len = Math.hypot(x1 - x0, y1 - y0);
      const b = box(len, 0.9, 1.1, iron, (x0 + x1) / 2, DECK + (y0 + y1) / 2 - 0.45, z);
      b.rotation.z = Math.atan2(y1 - y0, x1 - x0);
      g.add(b);
    }
  }
  // ridge lantern
  g.add(box(2.6, 1.6, SHEDL, lead, 0, DECK + RISE + 1.4, ZC));
  // north gable screen
  g.add(new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.2, bevelEnabled: false }), dark)
    .translateY(0));
  g.children[g.children.length - 1].position.set(0, DECK, ZC - SHEDL / 2 - 1.2);
  // south (front) gable screen, glazed with a brick surround
  const sg = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.2, bevelEnabled: false }), glass);
  sg.position.set(0, DECK, Z0);
  g.add(sg);
}

// ---------------------------------------------------------------- MIDLAND GRAND HOTEL front (+z)
const FL = 118;                     // frontage length along x
const FZ = Z0 + 11;                 // front face plane
{
  g.add(box(FL, 30, 22, bk, 0, 0, FZ - 11));                  // main range, eaves ~30
  g.add(box(FL + 1.5, 1.6, 23.5, pale, 0, 30, FZ - 11));      // cornice
  g.add(gableRoof(FL, 22, 10, slate, 0, 31.6, FZ - 11, true, 0.5));  // steep roof -> 42 m
  // stone banding + pointed window tiers
  for (const zz of [FZ + 0.1, FZ - 22.1]) {
    for (let s = 0; s < 4; s++) {
      const yy = 4 + s * 6.6;
      g.add(box(FL - 4, 0.8, 0.5, pale, 0, yy - 1.2, zz));
      for (let i = 0; i < 20; i++) {
        const x = -FL / 2 + 5 + i * (FL - 10) / 19;
        g.add(box(2.6, 4.2, 0.5, dark, x, yy, zz));
        g.add(cone(1.9, 1.6, dark, x, yy + 4.2, zz, 6));
      }
    }
  }
  // dormer row on the steep roof
  for (let i = 0; i < 13; i++) {
    const x = -FL / 2 + 6 + i * (FL - 12) / 12;
    g.add(box(3.2, 5, 4, bk, x, 31.6, FZ - 3));
    g.add(gableRoof(3.4, 4.2, 2.6, slate, x, 36.6, FZ - 3, false, 0.2));
  }
  // projecting porte-cochere / oriel bays
  for (const px of [-34, 0, 34]) {
    g.add(box(14, 32, 6, bk, px, 0, FZ + 3));
    g.add(box(15, 1.4, 7, pale, px, 32, FZ + 3));
    g.add(gableRoof(13, 7, 6, slate, px, 33.4, FZ + 3, true, 0.3));
    g.add(pinnacle(1.1, 5, pale, px - 7, 33.4, FZ + 3, 6));
    g.add(pinnacle(1.1, 5, pale, px + 7, 33.4, FZ + 3, 6));
  }
  // west wing angled away to the north-west
  const ww = new THREE.Group();
  ww.add(box(46, 26, 18, bk, 0, 0, 0));
  ww.add(box(47, 1.4, 19, pale, 0, 26, 0));
  ww.add(gableRoof(46, 18, 8, slate, 0, 27.4, 0, true, 0.4));
  ww.rotation.y = -0.55;
  ww.position.set(-FL / 2 - 14, 0, FZ - 22);
  g.add(ww);
}

// ---------------------------------------------------------------- CLOCK TOWER 82 m (east, +x)
{
  const tx = FL / 2 - 5, tz = FZ - 8;
  const T = new THREE.Group();
  T.add(box(15, 46, 15, bk, 0, 0, 0));
  for (let s = 0; s < 5; s++) for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 3.2, 5.4, dz ? 0.6 : 3.2, dark, dx * 7.6, 6 + s * 8, dz * 7.6));
  T.add(box(16.4, 1.6, 16.4, pale, 0, 46, 0));
  // clock stage
  T.add(box(14.4, 12, 14.4, bk, 0, 47.6, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const d = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 3.2, 0.9, 18), M(0xe8e4d8));
    if (dz) d.rotation.x = Math.PI / 2; else d.rotation.z = Math.PI / 2;
    d.position.set(dx * 7.5, 53.6, dz * 7.5); T.add(d);
  }
  T.add(box(16.0, 1.6, 16.0, pale, 0, 59.6, 0));
  // belfry stage + steep pyramid roof to 82 m
  T.add(box(13.0, 8, 13.0, bk, 0, 61.2, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 7, 6, dz ? 0.6 : 7, dark, dx * 6.6, 62, dz * 6.6));
  T.add(box(14.6, 1.4, 14.6, pale, 0, 69.2, 0));
  T.add(hipRoof(13, 13, 9.5, slate, 0, 70.6, 0, 0.1));
  T.add(cyl(0.9, 1.2, 1.4, lead, 0, 80.1, 0, 8));
  T.add(cone(0.9, 1.5, lead, 0, 81.5, 0, 8));
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    T.add(pinnacle(1.5, 8.5, pale, dx * 6.6, 69.2, dz * 6.6, 6));
  T.position.set(tx, 0, tz);
  g.add(T);
}

// ---------------------------------------------------------------- WEST TOWER 76 m
{
  const tx = -FL / 2 + 6, tz = FZ - 9;
  const T = new THREE.Group();
  T.add(box(14, 44, 14, bk, 0, 0, 0));
  for (let s = 0; s < 5; s++) for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 3.0, 5.0, dz ? 0.6 : 3.0, dark, dx * 7.1, 6 + s * 7.6, dz * 7.1));
  T.add(box(15.4, 1.6, 15.4, pale, 0, 44, 0));
  T.add(cyl(6.6, 7.0, 12, bk, 0, 45.6, 0, 8));                 // octagonal upper stage
  for (let i = 0; i < 8; i++) {
    const a = (i + 0.5) / 8 * Math.PI * 2;
    T.add(box(2.4, 7, 0.7, dark, Math.cos(a) * 6.6, 47.5, Math.sin(a) * 6.6));
  }
  T.add(cyl(7.6, 7.6, 1.4, pale, 0, 57.6, 0, 8));
  T.add(cone(7.2, 15.5, slate, 0, 59.0, 0, 8));
  T.add(cyl(0.7, 0.9, 1.5, lead, 0, 74.5, 0, 6));
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    T.add(pinnacle(1.3, 6.5, pale, dx * 6.4, 44, dz * 6.4, 6));
  T.position.set(tx, 0, tz);
  g.add(T);
}

await exportGLB(g, OUT + 'st_pancras.glb');
