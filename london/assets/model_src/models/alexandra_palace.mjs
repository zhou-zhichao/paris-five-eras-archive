// Alexandra Palace, John Johnson 1875 (rebuilt after the 1873 fire), with the BBC
// television mast of 1935 at its south-east corner.
// Orientation: the ~300 m building runs along X; the main SOUTH front, with its terrace
// looking over London, faces +Z.  Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, gableRoof, hipRoof, THREE,
  P, M, column, pediment, balustrade, openWall, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const bk = M(0xb08a72), pale = M(P.pale), st = M(P.stone), dk = M(P.dstone),
  slate = M(P.slate), lead = M(P.lead), gl = M(P.glassroof), iron = M(P.iron),
  dark = M(0x4a463d), grav = M(0xa89b82);

const L = 300, D = 84, H = 20;

// terrace
g.add(box(L + 20, 2.5, 22, dk, 0, 0, D / 2 + 12));

g.add(box(L + 4, 2.5, D + 4, dk, 0, 0, 0));

// ---------------------------------------------------------------- the long ranges
function range(w, d, x, z, h = H) {
  g.add(box(w, h, d, bk, x, 2.5, z));
  g.add(box(w + 1.4, 1.4, d + 1.4, pale, x, 2.5 + h, z));
  g.add(gableRoof(w, d, d * 0.16, slate, x, 3.9 + h, z, true, 0.5));
  const n = Math.round(w / 7);
  for (const zs of [1, -1]) for (let i = 0; i < n; i++) {
    const xx = x - w / 2 + 4 + i * (w - 8) / (n - 1);
    g.add(box(2.8, 6.0, 0.6, dark, xx, 6.0, z + zs * (d / 2 + 0.1)));
    const hd = new THREE.Mesh(new THREE.CylinderGeometry(1.4, 1.4, 0.6, 10, 1, false, 0, Math.PI), dark);
    hd.rotation.x = zs > 0 ? -Math.PI / 2 : Math.PI / 2;
    hd.position.set(xx, 12.0, z + zs * (d / 2 + 0.1)); g.add(hd);
    g.add(box(1.6, h, 1.0, pale, xx + (w - 8) / (2 * (n - 1)), 2.5, z + zs * (d / 2 + 0.2)));
  }
}
range(96, D, -102, 0);
range(96, D, 102, 0);
range(L, 24, 0, -D / 2 + 12, 17);

// ---------------------------------------------------------------- the Great Hall (centre)
{
  const GW = 86, GD = D + 10;
  g.add(box(GW, 26, GD, bk, 0, 2.5, 0));
  g.add(box(GW + 1.6, 1.8, GD + 1.6, pale, 0, 28.5, 0));
  // the great semicircular roof over the hall
  const span = GD - 6, rise = 17, n = 16, pts = [];
  for (let i = 0; i <= n; i++) { const t = -1 + 2 * i / n; pts.push([t * span / 2, rise * Math.sqrt(Math.max(0, 1 - t * t))]); }
  const s = new THREE.Shape();
  s.moveTo(-span / 2, 0);
  for (const [x, y] of pts) s.lineTo(x, y);
  s.lineTo(span / 2, 0); s.closePath();
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: GW }), gl);
  const grp = new THREE.Group(); grp.add(m); m.position.set(0, 0, -GW / 2);
  grp.rotation.y = Math.PI / 2; grp.position.set(0, 30.3, 0);
  g.add(grp);
  for (let r = 0; r <= 10; r++) {
    const x = -GW / 2 + r * GW / 10;
    for (let i = 0; i < pts.length - 1; i++) {
      const [z0, y0] = pts[i], [z1, y1] = pts[i + 1];
      const len = Math.hypot(z1 - z0, y1 - y0);
      const b = box(1.0, 0.8, len, iron, x, 30.3 + (y0 + y1) / 2 - 0.4, (z0 + z1) / 2);
      b.rotation.x = -Math.atan2(y1 - y0, z1 - z0);
      g.add(b);
    }
  }
  g.add(box(GW, 1.4, 2.2, lead, 0, 47.6, 0));
  // the great rose window in the south gable
  const sg = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.6, bevelEnabled: false }), bk);
  sg.position.set(0, 30.3, GD / 2 - 1.0); sg.rotation.y = 0;
  const sgg = new THREE.Group(); sgg.add(sg); sgg.rotation.y = 0; g.add(sgg);
  const rose = new THREE.Mesh(new THREE.CylinderGeometry(9.0, 9.0, 1.0, 20), gl);
  rose.rotation.x = Math.PI / 2; rose.position.set(0, 40.0, GD / 2 + 0.6); g.add(rose);
  for (let i = 0; i < 12; i++) {
    const a = i / 12 * Math.PI;
    const b = box(18.4, 0.7, 1.2, pale, 0, 40.0, GD / 2 + 0.9);
    b.rotation.z = a; g.add(b);
  }
  const ng = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 1.6, bevelEnabled: false }), bk);
  ng.position.set(0, 30.3, -GD / 2 - 0.6); g.add(ng);
  // south entrance porch and steps
  g.add(box(40, 16, 8, pale, 0, 2.5, GD / 2 + 4));
  g.add(box(42, 1.6, 9.6, pale, 0, 18.5, GD / 2 + 4));
  g.add(box(30, 12, 1.0, dark, 0, 2.5, GD / 2 + 7.6));
  for (let i = 0; i < 4; i++) g.add(box(46 - i * 2, 0.6, 4 + i * 1.6, dk, 0, 2.5 - (4 - i) * 0.6, GD / 2 + 10));
}

// ---------------------------------------------------------------- corner towers with pyramid roofs
for (const [sx, sz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) {
  const tx = sx * (L / 2 - 12), tz = sz * (D / 2 - 10);
  g.add(box(20, 32, 20, bk, tx, 2.5, tz));
  g.add(box(21.6, 1.6, 21.6, pale, tx, 34.5, tz));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    g.add(box(dx ? 0.6 : 6.0, 5.0, dz ? 0.6 : 6.0, dark, tx + dx * 10.1, 27.0, tz + dz * 10.1));
  g.add(hipRoof(20, 20, 9.0, slate, tx, 36.1, tz, 0.15));
  g.add(cyl(0.4, 0.5, 2.4, iron, tx, 45.1, tz, 6));
}
// the two Palm Court domes flanking the Great Hall
for (const sx of [-1, 1]) {
  const cx = sx * 56;
  g.add(box(30, 24, 40, bk, cx, 2.5, 8));
  g.add(box(31.4, 1.6, 41.4, pale, cx, 26.5, 8));
  g.add(cyl(11.0, 11.6, 3.0, pale, cx, 28.1, 8, 16));
  g.add(lathe([[10.8, 0], [10.4, 1.6], [9.2, 3.6], [7.2, 5.6], [4.6, 7.2], [2.0, 8.1], [0, 8.4]],
    gl, cx, 31.1, 8, 16));
  for (let i = 0; i < 10; i++) {
    const a = i / 10 * Math.PI;
    const b = box(21.6, 0.7, 0.7, iron, cx, 33.0, 8);
    b.rotation.y = a; g.add(b);
  }
  g.add(cyl(1.4, 1.8, 2.0, pale, cx, 39.5, 8, 10));
  g.add(cone(1.6, 2.0, lead, cx, 41.5, 8, 10));
}

// ---------------------------------------------------------------- the BBC television mast (1935)
{
  const mx = L / 2 - 8, mz = D / 2 - 6;
  g.add(box(14, 8, 14, bk, mx, 2.5, mz));
  for (let i = 0; i < 9; i++) {
    const y = 10.5 + i * 6.4, r = 4.4 - i * 0.36;
    for (const [ox, oz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
      g.add(box(0.75, 6.4, 0.75, iron, mx + ox * r, y, mz + oz * r));
    g.add(box(2 * r + 0.75, 0.5, 2 * r + 0.75, iron, mx, y + 5.9, mz));
  }
  g.add(cyl(0.75, 1.0, 8.0, iron, mx, 68.1, mz, 8));
  g.add(cyl(0.22, 0.22, 4.0, iron, mx, 76.1, mz, 6));
}

await exportGLB(g, OUT + 'alexandra_palace.glb');
