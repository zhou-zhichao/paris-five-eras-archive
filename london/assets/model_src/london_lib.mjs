// Shared helpers for the LONDON landmark models (agent: london 1920-2025).
// Conventions: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, mat, box, cyl, cone, dome, prism, lathe, group, exportGLB } from './export_glb.mjs';

export const OUTDIR = 'C:/Users/sam/Documents/ChatGPT/3D map project/.claude/worktrees/london/london/assets/models/';
export const out = id => OUTDIR + id + '.glb';

export const P = {
  glass: 0x5b7c96, darkGlass: 0x34474f, greenGlass: 0x6f9a8f, paleGlass: 0x9dbdc9,
  steel: 0xe6e6e6, alu: 0xb9bcc0, concrete: 0xb5b2ab, darkConcrete: 0x8d8a84,
  brick: 0x9e5a45, stone: 0xd9d2c0, gold: 0xd0a23c, red: 0xb03a2e, black: 0x2a2a2c,
  copper: 0x5f8f7a, pitch: 0x4f8a3d, yellow: 0xd9b544,
};
export const M = {};   // lazily built material cache
export function m(hex) { if (!M[hex]) M[hex] = mat(hex); return M[hex]; }

// ---- polygon helpers (all in world (x,z)) ------------------------------------------
export function area2(pts) { let a = 0; for (let i = 0; i < pts.length; i++) { const p = pts[i], q = pts[(i + 1) % pts.length]; a += p[0] * q[1] - q[0] * p[1]; } return a / 2; }
export function cw(pts) { return area2(pts) > 0 ? pts.slice().reverse() : pts.slice(); }   // CW in (x,z) => top cap faces +y

// extruded polygon given in TRUE world (x,z) coordinates (wraps prism, which mirrors z)
export function poly(pts, h, material, x = 0, y = 0, z = 0) {
  return prism(pts.map(p => [p[0], -p[1]]), h, material, x, y, z);
}

export function regular(n, r, rot = 0, cx = 0, cz = 0) {
  const p = []; for (let i = 0; i < n; i++) { const a = rot + i * 2 * Math.PI / n; p.push([cx + r * Math.cos(a), cz + r * Math.sin(a)]); } return p;
}
export function ellipse(rx, rz, seg = 32, cx = 0, cz = 0) {
  const p = []; for (let i = 0; i < seg; i++) { const a = i * 2 * Math.PI / seg; p.push([cx + rx * Math.cos(a), cz + rz * Math.sin(a)]); } return p;
}
// rectangle w x d with rounded ends (radius r) -- r = d/2 gives a stadium shape
export function roundRect(w, d, r, seg = 8, cx = 0, cz = 0) {
  const p = [], hx = w / 2 - r, hz = d / 2 - r;
  const corners = [[hx, hz, 0], [-hx, hz, Math.PI / 2], [-hx, -hz, Math.PI], [hx, -hz, 1.5 * Math.PI]];
  for (const [ox, oz, a0] of corners) for (let i = 0; i <= seg; i++) { const a = a0 + i * (Math.PI / 2) / seg; p.push([cx + ox + r * Math.cos(a), cz + oz + r * Math.sin(a)]); }
  return p;
}
export function scalePoly(pts, sx, sz = sx, cx = 0, cz = 0) { return pts.map(p => [cx + (p[0] - cx) * sx, cz + (p[1] - cz) * sz]); }
export function movePoly(pts, dx, dz) { return pts.map(p => [p[0] + dx, p[1] + dz]); }
export function lerpPoly(a, b, t) { return a.map((p, i) => [p[0] + (b[i][0] - p[0]) * t, p[1] + (b[i][1] - p[1]) * t]); }

// ---- loft: stack of sections [{y, pts}] with the same point count --------------------
export function loft(sections, material, x = 0, y = 0, z = 0, capBottom = true, capTop = true) {
  const secs = sections.map(s => ({ y: s.y, pts: cw(s.pts) }));
  const pos = [];
  const push = (p) => pos.push(p[0], p[1], p[2]);
  const V = (pt, yy) => [pt[0], yy, pt[1]];
  for (let s = 0; s < secs.length - 1; s++) {
    const A = secs[s], B = secs[s + 1], n = A.pts.length;
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      const b0 = V(A.pts[i], A.y), b1 = V(A.pts[j], A.y), t1 = V(B.pts[j], B.y), t0 = V(B.pts[i], B.y);
      push(b0); push(b1); push(t1);
      push(b0); push(t1); push(t0);
    }
  }
  const capOf = (sec, up) => {
    const c = sec.pts.map(p => new THREE.Vector2(p[0], p[1]));
    const faces = THREE.ShapeUtils.triangulateShape(c, []);
    for (const f of faces) {
      const tri = up ? [f[0], f[1], f[2]] : [f[2], f[1], f[0]];
      for (const k of tri) push(V(sec.pts[k], sec.y));
    }
  };
  if (capBottom) capOf(secs[0], false);
  if (capTop) capOf(secs[secs.length - 1], true);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  const mesh = new THREE.Mesh(g, material);
  mesh.position.set(x, y, z);
  return mesh;
}

// simple tapered box from (w0,d0) at y0 to (w1,d1) at y1, optional shear (dx,dz of top centre)
export function taper(w0, d0, w1, d1, h, material, x = 0, y = 0, z = 0, dx = 0, dz = 0) {
  const r = (w, d, ox = 0, oz = 0) => [[-w / 2 + ox, -d / 2 + oz], [w / 2 + ox, -d / 2 + oz], [w / 2 + ox, d / 2 + oz], [-w / 2 + ox, d / 2 + oz]];
  return loft([{ y: 0, pts: r(w0, d0) }, { y: h, pts: r(w1, d1, dx, dz) }], material, x, y, z);
}

// ---- banded facade: alternating glass / spandrel bands, spandrel slightly proud ------
export function banded(w, h, d, glassHex, bandHex, x = 0, y = 0, z = 0, floorH = 3.6, proud = 0.35) {
  const g = new THREE.Group();
  const n = Math.max(1, Math.round(h / floorH)), fh = h / n;
  const gm = m(glassHex), bm = m(bandHex);
  g.add(box(w, h, d, gm, x, y, z));
  for (let i = 0; i < n; i++) {
    g.add(box(w + proud, fh * 0.34, d + proud, bm, x, y + i * fh + fh * 0.66, z));
  }
  return g;
}
// banded ring for cylinders
export function bandedCyl(r, h, glassHex, bandHex, x = 0, y = 0, z = 0, floorH = 3.6, seg = 20, proud = 0.35) {
  const g = new THREE.Group(); const n = Math.max(1, Math.round(h / floorH)), fh = h / n;
  g.add(cyl(r, r, h, m(glassHex), x, y, z, seg));
  for (let i = 0; i < n; i++) g.add(cyl(r + proud, r + proud, fh * 0.32, m(bandHex), x, y + i * fh + fh * 0.68, z, seg));
  return g;
}

// ---- tube along a polyline (Catmull-Rom) --------------------------------------------
export function tube(points, r, material, tubSeg = 48, radSeg = 8, closed = false) {
  const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(p[0], p[1], p[2])), closed);
  return new THREE.Mesh(new THREE.TubeGeometry(curve, tubSeg, r, radSeg, closed), material);
}
export function torus(R, r, material, x = 0, y = 0, z = 0, tubSeg = 48, radSeg = 8) {
  const mesh = new THREE.Mesh(new THREE.TorusGeometry(R, r, radSeg, tubSeg), material);
  mesh.position.set(x, y, z); return mesh;
}
// thin strut between two 3-D points
export function strut(a, b, r, material, seg = 6) {
  const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b);
  const len = A.distanceTo(B);
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, seg), material);
  mesh.position.copy(A).add(B).multiplyScalar(0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), B.clone().sub(A).normalize());
  return mesh;
}
export function rot(mesh, rx = 0, ry = 0, rz = 0) { mesh.rotation.set(rx, ry, rz); return mesh; }
export function at(obj, x, y, z) { obj.position.set(x, y, z); return obj; }

export { THREE, mat, box, cyl, cone, dome, prism, lathe, group, exportGLB };
