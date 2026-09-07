// King's Cross station, Lewis Cubitt 1852.  London stock brick, twin arched train sheds.
// Orientation: the twin-arch FACADE with its clock turret faces +Z; the two 250 m sheds
// run away behind it towards -Z.  Ground y=0, footprint centred on the origin.
// Sheds 2 x 32.5 m span (~70 m overall), 250 m long, ~29 m to the crown; facade 21 m,
// clock turret ~36 m.
import { exportGLB, box, cyl, cone, lathe, gableRoof, hipRoof, THREE,
  P, M, openWall, balustrade, OUT } from './_lib_wren_edwardian.mjs';

const g = new THREE.Group();
const bk = M(P.stock), bkd = M(0xa08e6f), pale = M(P.pale), st = M(P.stone),
  slate = M(P.slate), glass = M(P.glassroof), iron = M(P.iron), dark = M(0x33302b), lead = M(P.lead);

const SPAN = 32.5, SHEDL = 250, RISE = 20, SPRING = 9;
const Z0 = 5;                       // south face of the sheds (behind the facade)
const ZC = Z0 - SHEDL / 2;
const CX = 17.5;                    // centres of the two vaults
const W = 2 * CX + SPAN + 4;        // overall width ~ 71 m

// ---------------------------------------------------------------- platform level & side walls
g.add(box(W, 1.2, SHEDL, M(0x6b6660), 0, 0, ZC));
for (const sx of [-1, 1]) {
  g.add(box(2.6, SPRING + 3, SHEDL, bk, sx * (W / 2 - 1.3), 0, ZC));
  for (let i = 0; i < 24; i++) g.add(box(3.2, SPRING + 5, 1.8, bkd, sx * (W / 2 - 1.3), 0, Z0 - 5 - i * 10.2));
}
g.add(box(4.5, SPRING + 3, SHEDL, bk, 0, 0, ZC));       // central spine wall
for (let i = 0; i < 24; i++) g.add(box(5.0, SPRING + 6, 1.8, bkd, 0, 0, Z0 - 5 - i * 10.2));

// ---------------------------------------------------------------- the two glazed vaults
function vaultProfile(n) {
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const t = -1 + 2 * i / n;
    pts.push([t * SPAN / 2, RISE * Math.sqrt(Math.max(0, 1 - t * t))]);
  }
  return pts;
}
const vp = vaultProfile(16);
for (const sx of [-1, 1]) {
  const s = new THREE.Shape();
  s.moveTo(-SPAN / 2, 0);
  for (const [x, y] of vp) s.lineTo(x, y);
  s.lineTo(SPAN / 2, 0); s.closePath();
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: SHEDL, bevelEnabled: false }), glass);
  m.position.set(sx * CX, SPRING, ZC - SHEDL / 2);
  g.add(m);
  // ribs
  for (let r = 0; r <= 20; r++) {
    const z = ZC - SHEDL / 2 + r * SHEDL / 20;
    for (let i = 0; i < vp.length - 1; i++) {
      const [x0, y0] = vp[i], [x1, y1] = vp[i + 1];
      const len = Math.hypot(x1 - x0, y1 - y0);
      const b = box(len, 0.7, 0.9, iron, sx * CX + (x0 + x1) / 2, SPRING + (y0 + y1) / 2 - 0.35, z);
      b.rotation.z = Math.atan2(y1 - y0, x1 - x0);
      g.add(b);
    }
  }
  g.add(box(1.8, 1.2, SHEDL, lead, sx * CX, SPRING + RISE + 0.6, ZC));    // ridge vent
  // north gable screens
  const ng = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.0, bevelEnabled: false }), dark);
  ng.position.set(sx * CX, SPRING, ZC - SHEDL / 2 - 1.0);
  g.add(ng);
}

// ---------------------------------------------------------------- FACADE (+z), twin arches
{
  const FZ = Z0 + 3;
  const ops = [
    { cx: -CX, y0: 2.0, w: 21.0, h: 8.0, arch: true },
    { cx: CX, y0: 2.0, w: 21.0, h: 8.0, arch: true },
  ];
  g.add(openWall(W, 21.5, 3.0, bk, ops, 0, 0, FZ, 14));
  // recessed glazed lunettes behind the arches
  for (const sx of [-1, 1]) {
    const s2 = new THREE.Shape();
    s2.moveTo(-10.2, 0); s2.lineTo(10.2, 0); s2.lineTo(10.2, 8);
    s2.absarc(0, 8, 10.2, 0, Math.PI, false); s2.closePath();
    const m2 = new THREE.Mesh(new THREE.ExtrudeGeometry(s2, { depth: 0.6, bevelEnabled: false }), glass);
    m2.position.set(sx * CX, 2.0, FZ - 2.0);
    g.add(m2);
    // glazing bars
    for (let i = 1; i < 6; i++) g.add(box(0.45, 17, 0.9, iron, sx * CX - 10.2 + i * 3.4, 2.0, FZ - 1.7));
    g.add(box(20.4, 0.5, 0.9, iron, sx * CX, 8.0, FZ - 1.7));
  }
  // pilasters & cornice
  for (const x of [-W / 2 + 1.5, -7, 7, W / 2 - 1.5]) g.add(box(3.4, 21.5, 4.2, bkd, x, 0, FZ));
  g.add(box(W + 2, 1.6, 5.5, pale, 0, 21.5, FZ));
  g.add(box(W, 2.0, 4.5, bk, 0, 23.1, FZ));
  // low arcaded screen wall wings
  for (const sx of [-1, 1]) g.add(box(16, 9, 6, bk, sx * (W / 2 + 8), 0, FZ));

  // ------------------------------------------------------------ clock turret (~36 m)
  const T = new THREE.Group();
  T.add(box(10.0, 30, 10.0, bk, 0, 0, 0));
  T.add(box(11.0, 1.2, 11.0, pale, 0, 30, 0));
  T.add(box(9.2, 7.0, 9.2, bk, 0, 31.2, 0));               // clock stage
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const d = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2.5, 0.9, 18), M(0xe8e4d8));
    if (dz) d.rotation.x = Math.PI / 2; else d.rotation.z = Math.PI / 2;
    d.position.set(dx * 4.8, 34.7, dz * 4.8); T.add(d);
  }
  T.add(box(10.8, 1.4, 10.8, pale, 0, 38.2, 0));
  T.add(hipRoof(10, 10, 2.8, slate, 0, 39.6, 0, 0.25));    // shallow Italianate roof
  T.add(cyl(0.5, 0.7, 1.2, lead, 0, 42.4, 0, 8));
  T.position.set(0, 0, FZ - 1);
  g.add(T);
}

await exportGLB(g, OUT + 'kings_cross.glb');
