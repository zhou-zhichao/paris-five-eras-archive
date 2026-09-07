// The Crystal Palace re-erected at Sydenham, Paxton 1854 (burnt 1936).
// Orientation: the 490 m glass-and-iron building runs along X; the great garden TERRACES
// and the main front face +Z.  Ground y=0, whole composition centred on the origin.
// Barrel-vaulted nave; great central transept vault to ~51 m; two end transepts;
// Brunel's two water towers 85 m stand beyond each end of the building.
import { exportGLB, box, cyl, cone, gableRoof, THREE, P, M, OUT } from './_lib_wren_edwardian.mjs';

const g = new THREE.Group();
const gl = M(P.glassroof), gl2 = M(0x9fbdd0), iron = M(P.iron), ironl = M(0x6d7276),
  st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), grass = M(P.grass), brick = M(0x9a5a48);

const L = 490, WD = 117;             // building 490 x 117 m
const T1 = 12, T2 = 10;              // two glazed tiers, then the nave vault

// ---------------------------------------------------------------- terraces (front, +z)
g.add(box(L + 80, 3.0, 60, dk, 0, 0, WD / 2 + 42));
g.add(box(L + 40, 3.0, 34, pale, 0, 3.0, WD / 2 + 26));
g.add(box(L + 20, 2.5, 18, pale, 0, 6.0, WD / 2 + 16));
for (let i = 0; i < 22; i++) {           // terrace balustrade urns
  const x = -L / 2 - 10 + i * (L + 20) / 21;
  g.add(cyl(1.1, 1.4, 2.6, pale, x, 8.5, WD / 2 + 24));
}
g.add(box(L + 90, 0.4, 40, grass, 0, 0, WD / 2 + 90));

// ---------------------------------------------------------------- stepped glazed body
g.add(box(L, T1, WD, gl, 0, 8.5, 0));
g.add(box(L, T2, 70, gl2, 0, 8.5 + T1, 0));
// iron framing: columns / mullions on the long faces
for (let i = 0; i <= 62; i++) {
  const x = -L / 2 + i * L / 62;
  for (const zs of [1, -1]) {
    g.add(box(1.1, T1, 1.1, iron, x, 8.5, zs * (WD / 2 - 0.3)));
    g.add(box(1.0, T2, 1.0, iron, x, 8.5 + T1, zs * 34.7));
  }
}
// horizontal string courses
for (const [y, w] of [[8.5 + T1, WD], [8.5 + T1 + T2, 70]]) {
  g.add(box(L + 1.5, 1.1, w + 1.5, ironl, 0, y - 0.55, 0));
}
// end walls
for (const sx of [-1, 1]) g.add(box(1.4, T1 + T2, WD, ironl, sx * L / 2, 8.5, 0));

// ---------------------------------------------------------------- barrel vaults
function vault(len, span, rise, y, x, z, alongX = true, m = gl, ribs = 14) {
  const n = 14, pts = [];
  for (let i = 0; i <= n; i++) {
    const t = -1 + 2 * i / n;
    pts.push([t * span / 2, rise * Math.sqrt(Math.max(0, 1 - t * t))]);
  }
  const s = new THREE.Shape();
  s.moveTo(-span / 2, 0);
  for (const [px, py] of pts) s.lineTo(px, py);
  s.lineTo(span / 2, 0); s.closePath();
  const me = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: len, bevelEnabled: false }), m);
  const grp = new THREE.Group(); grp.add(me);
  me.position.set(0, 0, -len / 2);
  grp.rotation.y = alongX ? Math.PI / 2 : 0;
  grp.position.set(x, y, z);
  g.add(grp);
  // ribs
  for (let r = 0; r <= ribs; r++) {
    const off = -len / 2 + r * len / ribs;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
      const ln = Math.hypot(x1 - x0, y1 - y0);
      const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
      const b = alongX
        ? box(0.8, 0.7, ln, iron, x + off, y + cy - 0.35, z + cx)
        : box(ln, 0.7, 0.8, iron, x + cx, y + cy - 0.35, z + off);
      if (alongX) b.rotation.x = -Math.atan2(y1 - y0, x1 - x0);
      else b.rotation.z = Math.atan2(y1 - y0, x1 - x0);
      g.add(b);
    }
  }
}
const TOP = 8.5 + T1 + T2;                         // 30.5 -> top of the glazed tiers
// the long barrel-vaulted nave, crown ~ 43 m
vault(L, 26, 12.5, TOP, 0, 0, true, gl2, 40);
// great central transept: span 37, crown ~ 51 m
vault(WD + 16, 37, 20.5, TOP, 0, 0, false, gl, 16);
g.add(box(40, TOP - 8.5, WD + 16, gl2, 0, 8.5, 0));       // transept body rising through the tiers
for (let i = 0; i <= 12; i++) {
  const z = -(WD + 16) / 2 + i * (WD + 16) / 12;
  for (const sx of [-1, 1]) g.add(box(1.2, 22, 1.2, iron, sx * 20, 8.5, z));
}
// two end transepts: span 24, crown ~ 40 m
for (const sx of [-1, 1]) {
  const tx = sx * 160;
  g.add(box(26, TOP - 8.5, WD + 6, gl2, tx, 8.5, 0));
  vault(WD + 6, 24, 11.0, TOP, tx, 0, false, gl, 12);
  for (let i = 0; i <= 10; i++) {
    const z = -(WD + 6) / 2 + i * (WD + 6) / 10;
    for (const s2 of [-1, 1]) g.add(box(1.0, TOP - 8.5, 1.0, iron, tx + s2 * 13, 8.5, z));
  }
}

// ---------------------------------------------------------------- Brunel water towers (85 m)
for (const sx of [-1, 1]) {
  const tx = sx * (L / 2 + 42);
  g.add(box(22, 6, 22, brick, tx, 0, 0));
  g.add(box(18, 8, 18, brick, tx, 6, 0));
  // tapering open iron shaft
  for (let i = 0; i < 8; i++) {
    const y = 14 + i * 7.6, r = 7.6 - i * 0.42;
    for (const [ox, oz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
      g.add(box(1.5, 7.6, 1.5, iron, tx + ox * r, y, oz * r));
    g.add(box(2 * r + 1.5, 1.0, 2 * r + 1.5, ironl, tx, y + 7.0, 0));
  }
  // the water tank + cornice
  g.add(cyl(9.5, 9.5, 12, ironl, tx, 74, 0, 12));
  g.add(cyl(10.6, 10.6, 1.6, iron, tx, 74, 0, 12));
  g.add(cyl(10.6, 10.6, 1.6, iron, tx, 84.4, 0, 12));
  g.add(cone(9.8, 2.0, iron, tx, 86, 0, 12));
}

await exportGLB(g, OUT + 'crystal_palace_sydenham.glb');
