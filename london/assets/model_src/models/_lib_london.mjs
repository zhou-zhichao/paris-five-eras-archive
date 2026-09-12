// Shared helpers for the London (Roman -> Stuart) landmark models.
// Conventions: metres, ground y=0, footprint centred on x/z, long axis along x,
// main facade / river side towards +z.
import { mat, box, cyl, cone, dome, gableRoof, hipRoof, prism, lathe, group, THREE } from '../export_glb.mjs';
export { mat, box, cyl, cone, dome, gableRoof, hipRoof, prism, lathe, group, THREE };
export { exportGLB } from '../export_glb.mjs';

export const OUT = 'C:/Users/sam/Documents/ChatGPT/3D map project/.claude/worktrees/london/london/assets/models/';
export const out = id => OUT + id + '.glb';

// ---- palette ---------------------------------------------------------------
export const C = {
  portland: 0xd9d2c0, pale: 0xe3dccb, rag: 0xb8ad94, medieval: 0xa89f8a,
  brick: 0x9a5a48, tudor: 0x8f4f3e, stock: 0xb9a98a, slate: 0x4d5057,
  lead: 0x7b8087, copper: 0x5f8f7a, gold: 0xd0a23c, timber: 0x6e4a2b,
  darkTimber: 0x4a3320, thatch: 0x8b6f3c, tile: 0xa9573b, whitewash: 0xe9e2d2,
  grass: 0x6d8f4a, water: 0x4f7f8a, glass: 0x3a4048, dark: 0x2f3338,
};
export const M = {};
for (const k of Object.keys(C)) M[k] = mat(C[k]);

// ---- geometry helpers ------------------------------------------------------

// A wall panel of width w, height h, thickness t, standing in the XY plane and
// extruded along z. `holes` is an array of THREE.Path in the wall's local
// (x from -w/2..w/2, y from 0..h) coordinates.
export function wall(w, h, t, m, holes = [], x = 0, y = 0, z = 0, rotY = 0) {
  const s = new THREE.Shape();
  s.moveTo(-w / 2, 0); s.lineTo(w / 2, 0); s.lineTo(w / 2, h); s.lineTo(-w / 2, h); s.closePath();
  for (const hl of holes) s.holes.push(hl);
  const g = new THREE.ExtrudeGeometry(s, { depth: t, bevelEnabled: false });
  g.translate(0, 0, -t / 2);
  const me = new THREE.Mesh(g, m);
  me.position.set(x, y, z); me.rotation.y = rotY;
  return me;
}

// Arch-topped hole path. cx = centre x, w = width, sill = bottom y, springH =
// height of the vertical jamb, rise = height of the arch above the spring.
// pointed>0 gives a gothic point (pointed = extra apex rise factor).
export function archPath(cx, w, sill, springH, rise, pointed = 0, seg = 8) {
  const p = new THREE.Path();
  const hw = w / 2, sy = sill + springH;
  p.moveTo(cx - hw, sill);
  p.lineTo(cx - hw, sy);
  if (pointed > 0) {
    // two circular-ish arcs meeting at an apex
    const apex = sy + rise;
    for (let i = 1; i <= seg; i++) {
      const t = i / seg;
      const xx = cx - hw * (1 - t);
      const yy = sy + rise * Math.sqrt(Math.max(0, 1 - Math.pow(1 - t, 2) * 0.55)) * (0.55 + 0.45 * t);
      p.lineTo(xx, Math.min(yy, apex));
    }
    p.lineTo(cx, apex);
    for (let i = 1; i <= seg; i++) {
      const t = 1 - i / seg;
      const xx = cx + hw * (1 - t);
      const yy = sy + rise * Math.sqrt(Math.max(0, 1 - Math.pow(1 - t, 2) * 0.55)) * (0.55 + 0.45 * t);
      p.lineTo(xx, Math.min(yy, apex));
    }
    p.lineTo(cx + hw, sy);
  } else {
    for (let i = 0; i <= seg * 2; i++) {
      const a = Math.PI - (i / (seg * 2)) * Math.PI;
      p.lineTo(cx + hw * Math.cos(a), sy + rise * Math.sin(a));
    }
  }
  p.lineTo(cx + hw, sill);
  p.closePath();
  return p;
}

export function rectPath(cx, cy, w, h) {
  const p = new THREE.Path();
  p.moveTo(cx - w / 2, cy - h / 2); p.lineTo(cx + w / 2, cy - h / 2);
  p.lineTo(cx + w / 2, cy + h / 2); p.lineTo(cx - w / 2, cy + h / 2);
  p.closePath(); return p;
}

// Row of merlons along a wall top. alongX: run parallel to x.
export function crenel(len, t, m, x, y, z, alongX = true, mh = 1.2, mw = 1.4, gap = 1.0) {
  const g = new THREE.Group();
  const pitch = mw + gap;
  const n = Math.max(2, Math.floor(len / pitch));
  const start = -((n - 1) * pitch) / 2;
  for (let i = 0; i < n; i++) {
    const u = start + i * pitch;
    g.add(alongX ? box(mw, mh, t, m, u, 0, 0) : box(t, mh, mw, m, 0, 0, u));
  }
  g.position.set(x, y, z);
  return g;
}

// Crenellated parapet around a rectangular tower/wall top (w x d footprint).
export function crenelRing(w, d, t, m, x, y, z, mh = 1.2, mw = 1.4, gap = 1.0) {
  return group(
    crenel(w, t, m, x, y, z + d / 2 - t / 2, true, mh, mw, gap),
    crenel(w, t, m, x, y, z - d / 2 + t / 2, true, mh, mw, gap),
    crenel(d, t, m, x + w / 2 - t / 2, y, z, false, mh, mw, gap),
    crenel(d, t, m, x - w / 2 + t / 2, y, z, false, mh, mw, gap),
  );
}

// Row of columns.
export function colonnade(n, pitch, r, h, m, x, y, z, alongX = true, seg = 8, cap = true) {
  const g = new THREE.Group();
  const start = -((n - 1) * pitch) / 2;
  for (let i = 0; i < n; i++) {
    const u = start + i * pitch;
    const cx = alongX ? u : 0, cz = alongX ? 0 : u;
    g.add(cyl(r * 0.86, r, h, m, cx, 0, cz, seg));
    if (cap) g.add(box(r * 2.4, r * 0.5, r * 2.4, m, cx, h, cz));
  }
  g.position.set(x, y, z);
  return g;
}

// Small octagonal pinnacle (spirelet on a base).
export function pinnacle(r, h, m, x = 0, y = 0, z = 0) {
  return group(
    cyl(r, r * 1.1, h * 0.4, m, 0, 0, 0, 8),
    cone(r * 1.05, h * 0.6, m, 0, h * 0.4, 0, 8),
  ).translateX(x).translateY(y).translateZ(z);
}

// Octagonal / polygonal turret with a conical cap.
export function turret(r, h, m, capM, x = 0, y = 0, z = 0, seg = 8, capH = 0) {
  const g = new THREE.Group();
  g.add(cyl(r, r, h, m, 0, 0, 0, seg));
  if (capH > 0) g.add(cone(r * 1.12, capH, capM, 0, h, 0, seg));
  g.position.set(x, y, z);
  return g;
}

// Flying buttress: pier + sloping arch strut towards the nave.
export function flyingButtress(pierW, pierH, reach, topY, m, x, z, sign = 1) {
  const g = new THREE.Group();
  g.add(box(pierW, pierH, pierW * 1.4, m, 0, 0, 0));
  g.add(cone(pierW * 0.7, pierW * 2.2, m, 0, pierH, 0, 6));
  // sloping strut
  const len = Math.hypot(reach, topY - pierH * 0.75);
  const strut = box(pierW * 0.55, 0.9, len, m, 0, 0, 0);
  strut.rotation.x = -Math.atan2(topY - pierH * 0.75, reach) * sign;
  strut.position.set(0, pierH * 0.75 + (topY - pierH * 0.75) / 2, -sign * reach / 2);
  g.add(strut);
  g.position.set(x, 0, z);
  return g;
}

// A band of dark recessed windows on a wall face (helps read scale).
export function windowBand(n, pitch, w, h, depth, m, x, y, z, alongX = true) {
  const g = new THREE.Group();
  const start = -((n - 1) * pitch) / 2;
  for (let i = 0; i < n; i++) {
    const u = start + i * pitch;
    g.add(alongX ? box(w, h, depth, m, u, 0, 0) : box(depth, h, w, m, 0, 0, u));
  }
  g.position.set(x, y, z);
  return g;
}

// Gothic lancet windows (dark) applied to a wall face.
export function lancets(n, pitch, w, h, depth, m, x, y, z, alongX = true) {
  const g = new THREE.Group();
  const start = -((n - 1) * pitch) / 2;
  for (let i = 0; i < n; i++) {
    const u = start + i * pitch;
    const cx = alongX ? u : 0, cz = alongX ? 0 : u;
    if (alongX) {
      g.add(box(w, h, depth, m, cx, 0, cz));
      g.add(prismTriX(w, w * 0.8, depth, m, cx, h, cz));
    } else {
      g.add(box(depth, h, w, m, cx, 0, cz));
      g.add(prismTriZ(w, w * 0.8, depth, m, cx, h, cz));
    }
  }
  g.position.set(x, y, z);
  return g;
}
function prismTriX(w, h, t, m, x, y, z) {
  const s = new THREE.Shape(); s.moveTo(-w / 2, 0); s.lineTo(w / 2, 0); s.lineTo(0, h); s.closePath();
  const g = new THREE.ExtrudeGeometry(s, { depth: t, bevelEnabled: false }); g.translate(0, 0, -t / 2);
  const me = new THREE.Mesh(g, m); me.position.set(x, y, z); return me;
}
function prismTriZ(w, h, t, m, x, y, z) { const me = prismTriX(w, h, t, m, x, y, z); me.rotation.y = Math.PI / 2; return me; }
export { prismTriX, prismTriZ };

// A rose window: dark disc + a few spokes.
export function rose(r, depth, mStone, mGlass, x, y, z, rotY = 0, spokes = 8) {
  const g = new THREE.Group();
  g.add(cyl(r, r, depth, mGlass, 0, -depth / 2, 0, 16).rotateX(Math.PI / 2));
  const ring = new THREE.Mesh(new THREE.TorusGeometry(r * 1.06, r * 0.09, 6, 20), mStone);
  g.add(ring);
  for (let i = 0; i < spokes; i++) {
    const b = box(r * 1.9, r * 0.09, depth * 0.9, mStone, 0, -r * 0.045, 0);
    b.rotation.z = (i / spokes) * Math.PI; g.add(b);
  }
  g.position.set(x, y, z); g.rotation.y = rotY;
  return g;
}

// Simple ridge-with-hips roof for a long range (ridge along x).
export function rangeRoof(w, d, h, m, x, y, z) { return hipRoof(w, d, h, m, x, y, z, 0.85); }

// Chimney stacks along a range.
export function chimneys(n, pitch, w, h, m, x, y, z) {
  const g = new THREE.Group();
  const start = -((n - 1) * pitch) / 2;
  for (let i = 0; i < n; i++) g.add(box(w, h, w, m, start + i * pitch, 0, 0));
  g.position.set(x, y, z);
  return g;
}

// Tudor octagonal brick chimney (tall, thin) with a cap.
export function tudorChimney(r, h, m, capM, x, y, z) {
  return group(box(r * 2.6, h * 0.12, r * 2.6, m, 0, 0, 0), cyl(r, r, h * 0.82, m, 0, h * 0.12, 0, 8),
    box(r * 2.6, h * 0.09, r * 2.6, capM, 0, h * 0.94, 0)).translateX(x).translateY(y).translateZ(z);
}

// Extruded shape from a list of [x,y] outline points, extruded along +z by t,
// centred on z. Useful for gable ends / profiles.
export function profileWall(pts, t, m, x = 0, y = 0, z = 0, rotY = 0) {
  const s = new THREE.Shape(pts.map(p => new THREE.Vector2(p[0], p[1])));
  const g = new THREE.ExtrudeGeometry(s, { depth: t, bevelEnabled: false });
  g.translate(0, 0, -t / 2);
  const me = new THREE.Mesh(g, m); me.position.set(x, y, z); me.rotation.y = rotY;
  return me;
}

// Ellipse/ring solid: outer ellipse (a,b) with inner ellipse hole (ia,ib),
// extruded from y to y+h.  Lies in the XZ plane.
export function ellipseRing(a, b, ia, ib, h, m, x = 0, y = 0, z = 0, seg = 40) {
  const s = new THREE.Shape();
  for (let i = 0; i <= seg; i++) { const t = (i / seg) * Math.PI * 2; const px = a * Math.cos(t), py = b * Math.sin(t); i ? s.lineTo(px, py) : s.moveTo(px, py); }
  if (ia > 0) {
    const hpath = new THREE.Path();
    for (let i = 0; i <= seg; i++) { const t = -(i / seg) * Math.PI * 2; const px = ia * Math.cos(t), py = ib * Math.sin(t); i ? hpath.lineTo(px, py) : hpath.moveTo(px, py); }
    s.holes.push(hpath);
  }
  const g = new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: false });
  g.rotateX(-Math.PI / 2);
  const me = new THREE.Mesh(g, m); me.position.set(x, y, z); return me;
}

// Footprint prism helper that takes true [x,z] world offsets (prism() in
// export_glb.mjs mirrors z, so negate here).
export function foot(points, h, m, x = 0, y = 0, z = 0) {
  return prism(points.map(p => [p[0], -p[1]]), h, m, x, y, z);
}
