// Shared helpers for the Wren -> Edwardian London landmark set.
// (private to this agent's models; do not edit from other landmark scripts)
import { THREE, mat, box, cyl, cone, dome, gableRoof, hipRoof, prism, lathe, group, exportGLB } from '../export_glb.mjs';
export { THREE, mat, box, cyl, cone, dome, gableRoof, hipRoof, prism, lathe, group, exportGLB };

export const OUT = 'C:/Users/sam/Documents/ChatGPT/3D map project/.claude/worktrees/london/london/assets/models/';

export const P = {
  stone: 0xd9d2c0,   // Portland stone
  pale: 0xe3dccb,    // pale stone
  dstone: 0xb8ad94,  // darker stone
  brick: 0x9a5a48,   // red brick
  stock: 0xb9a98a,   // London stock brick
  vred: 0x9e5a45,    // Victorian red brick / terracotta
  slate: 0x4d5057,
  lead: 0x7b8087,
  copper: 0x5f8f7a,
  gold: 0xd0a23c,
  iron: 0x3d3f42,
  glassroof: 0x8fb0c4,
  glass: 0x5b7c96,
  timber: 0x6e4a2b,
  white: 0xe9e2d2,
  grass: 0x6d8f4a,
  water: 0x4f7f8a,
  bronze: 0x6b5a3a,
};

const _cache = new Map();
export function M(hex) { if (!_cache.has(hex)) _cache.set(hex, mat(hex)); return _cache.get(hex); }

// ---------------------------------------------------------------- columns
// classical column: tapered shaft + square base + square capital. y = bottom.
export function column(r, h, material, x = 0, y = 0, z = 0, seg = 8, capMat = material) {
  const g = new THREE.Group();
  const capH = Math.max(0.4, r * 0.9), baseH = Math.max(0.3, r * 0.5);
  g.add(cyl(r * 0.86, r, h - capH - baseH, material, 0, baseH, 0, seg));
  g.add(box(r * 2.3, baseH, r * 2.3, capMat, 0, 0, 0));
  g.add(box(r * 2.4, capH, r * 2.4, capMat, 0, h - capH, 0));
  g.position.set(x, y, z);
  return g;
}
// square pilaster / pier
export function pilaster(w, h, d, material, x = 0, y = 0, z = 0) {
  return group(box(w, h, d, material, x, y, z), box(w * 1.25, h * 0.05 + 0.4, d * 1.3, material, x, y + h - (h * 0.05 + 0.4), z));
}
// row of n columns along x, centred
export function colonnade(n, spacing, r, h, material, x = 0, y = 0, z = 0, seg = 8, capMat) {
  const g = new THREE.Group();
  for (let i = 0; i < n; i++) g.add(column(r, h, material, (i - (n - 1) / 2) * spacing, 0, 0, seg, capMat || material));
  g.position.set(x, y, z);
  return g;
}
// row of n columns along z, centred
export function colonnadeZ(n, spacing, r, h, material, x = 0, y = 0, z = 0, seg = 8) {
  const g = new THREE.Group();
  for (let i = 0; i < n; i++) g.add(column(r, h, material, 0, 0, (i - (n - 1) / 2) * spacing, seg));
  g.position.set(x, y, z);
  return g;
}
// circular peristyle of n columns on a ring
export function ringColonnade(n, radius, r, h, material, x = 0, y = 0, z = 0, seg = 6, a0 = 0, aSpan = Math.PI * 2) {
  const g = new THREE.Group();
  const full = Math.abs(aSpan - Math.PI * 2) < 1e-6;
  const div = full ? n : (n - 1);
  for (let i = 0; i < n; i++) {
    const a = a0 + aSpan * (i / div);
    g.add(column(r, h, material, Math.cos(a) * radius, 0, Math.sin(a) * radius, seg));
  }
  g.position.set(x, y, z);
  return g;
}

// ---------------------------------------------------------------- pediment
// triangular gable facing +z (extruded along z). y = bottom of the triangle.
export function pediment(w, h, d, material, x = 0, y = 0, z = 0) {
  const s = new THREE.Shape();
  s.moveTo(-w / 2, 0); s.lineTo(w / 2, 0); s.lineTo(0, h); s.closePath();
  const g = new THREE.ExtrudeGeometry(s, { depth: d, bevelEnabled: false });
  g.translate(0, 0, -d / 2);
  const me = new THREE.Mesh(g, material);
  me.position.set(x, y, z);
  return me;
}
// same but facing +x (extruded along x)
export function pedimentX(w, h, d, material, x = 0, y = 0, z = 0) {
  const me = pediment(w, h, d, material, 0, 0, 0);
  const g = new THREE.Group(); g.add(me); g.rotation.y = Math.PI / 2; g.position.set(x, y, z);
  return g;
}

// ---------------------------------------------------------------- walls with openings
// wall in the x-y plane, thickness d along z. openings: {cx, y0, w, h, arch:true|false}
// for an arched opening h is the height to the springing; the semicircle sits on top.
export function openWall(w, h, d, material, openings = [], x = 0, y = 0, z = 0, seg = 8) {
  const s = new THREE.Shape();
  s.moveTo(-w / 2, 0); s.lineTo(w / 2, 0); s.lineTo(w / 2, h); s.lineTo(-w / 2, h); s.closePath();
  for (const o of openings) {
    const r = o.w / 2, y0 = o.y0 || 0;
    const p = new THREE.Path();
    if (o.arch === false) {
      p.moveTo(o.cx - r, y0); p.lineTo(o.cx + r, y0); p.lineTo(o.cx + r, y0 + o.h); p.lineTo(o.cx - r, y0 + o.h); p.closePath();
    } else if (o.arch === 'pointed') {
      const ap = o.pointed || 1.15;
      p.moveTo(o.cx - r, y0); p.lineTo(o.cx + r, y0); p.lineTo(o.cx + r, y0 + o.h);
      p.lineTo(o.cx, y0 + o.h + r * ap); p.lineTo(o.cx - r, y0 + o.h); p.closePath();
    } else {
      p.moveTo(o.cx - r, y0); p.lineTo(o.cx + r, y0); p.lineTo(o.cx + r, y0 + o.h);
      p.absarc(o.cx, y0 + o.h, r, 0, Math.PI, false);
      p.closePath();
    }
    s.holes.push(p);
  }
  const g = new THREE.ExtrudeGeometry(s, { depth: d, bevelEnabled: false, curveSegments: seg });
  g.translate(0, 0, -d / 2);
  const me = new THREE.Mesh(g, material);
  me.position.set(x, y, z);
  return me;
}
// convenience: regular arcade of n arches across width w
export function arcade(w, h, d, material, n, archW, archH, x = 0, y = 0, z = 0, y0 = 0, seg = 8) {
  const sp = w / n, ops = [];
  for (let i = 0; i < n; i++) ops.push({ cx: (i - (n - 1) / 2) * sp, y0, w: archW, h: archH, arch: true });
  return openWall(w, h, d, material, ops, x, y, z, seg);
}

// ---------------------------------------------------------------- roofs & tops
export function pinnacle(r, h, material, x = 0, y = 0, z = 0, seg = 6) {
  return group(cyl(r * 0.75, r, h * 0.5, material, x, y, z, seg), cone(r * 0.85, h * 0.5, material, x, y + h * 0.5, z, seg));
}
export function finialBallCross(r, h, material, x = 0, y = 0, z = 0) {
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.SphereGeometry(r, 10, 8), material));
  g.children[0].position.y = r;
  g.add(box(r * 0.35, h, r * 0.35, material, 0, r * 1.6, 0));
  g.add(box(h * 0.42, r * 0.35, r * 0.35, material, 0, r * 1.6 + h * 0.62, 0));
  g.position.set(x, y, z);
  return g;
}
// balustrade: a light parapet band with a slightly proud coping
export function balustrade(w, d, h, material, x = 0, y = 0, z = 0, t = 0.8) {
  const g = new THREE.Group();
  g.add(box(w, h * 0.8, d, material, 0, 0, 0));
  g.add(box(w + t, h * 0.2, d + t, material, 0, h * 0.8, 0));
  g.position.set(x, y, z);
  return g;
}
// hollow parapet ring around a rectangular roof
export function parapet(w, d, h, material, x = 0, y = 0, z = 0, t = 1.0) {
  const g = new THREE.Group();
  g.add(box(w, h, t, material, 0, 0, d / 2 - t / 2));
  g.add(box(w, h, t, material, 0, 0, -d / 2 + t / 2));
  g.add(box(t, h, d - 2 * t, material, w / 2 - t / 2, 0, 0));
  g.add(box(t, h, d - 2 * t, material, -w / 2 + t / 2, 0, 0));
  g.position.set(x, y, z);
  return g;
}
// simple cornice band (slightly proud box)
export function cornice(w, d, h, material, x = 0, y = 0, z = 0, out = 1.0) {
  return box(w + 2 * out, h, d + 2 * out, material, x, y, z);
}
// stepped platform, n steps, stepping outwards downwards
export function steps(w, d, n, riser, tread, material, x = 0, y = 0, z = 0) {
  const g = new THREE.Group();
  for (let i = 0; i < n; i++) g.add(box(w + 2 * tread * (n - i), riser, d + 2 * tread * (n - i), material, 0, i * riser, 0));
  g.position.set(x, y - n * riser, z);
  return g;
}
// barrel vault roof: half cylinder along x, length w, span d, y = springing
export function barrelVault(w, d, material, x = 0, y = 0, z = 0, seg = 16, rise = null) {
  const r = d / 2;
  const s = rise === null ? 1 : rise / r;
  const g = new THREE.Mesh(new THREE.CylinderGeometry(r, r, w, seg, 1, true, 0, Math.PI), material);
  g.rotation.z = Math.PI / 2;
  const o = new THREE.Group(); o.add(g);
  o.scale.set(1, s, 1);
  o.position.set(x, y, z);
  const w2 = new THREE.Group(); w2.add(o);
  return w2;
}
// solid half-cylinder shed (closed ends) along x
export function vaultSolid(w, span, rise, material, x = 0, y = 0, z = 0, seg = 14) {
  const s = new THREE.Shape();
  const r = span / 2;
  s.moveTo(-r, 0);
  for (let i = 0; i <= seg; i++) { const a = Math.PI - Math.PI * i / seg; s.lineTo(Math.cos(a) * r, Math.sin(a) * rise); }
  s.closePath();
  const g = new THREE.ExtrudeGeometry(s, { depth: w, bevelEnabled: false });
  g.rotateY(Math.PI / 2); g.translate(0, 0, 0);
  const me = new THREE.Mesh(g, material);
  me.position.set(x - w / 2, y, z);
  const gr = new THREE.Group(); gr.add(me); gr.position.set(0, 0, 0);
  me.position.set(x, y, z); me.rotation.y = 0;
  // ExtrudeGeometry after rotateY(PI/2): depth runs along -x; recentre
  me.position.x = x + w / 2;
  return me;
}
// torus arch (ring segment) in the x-y plane, thickness d along z
export function archRib(r, tube, material, x = 0, y = 0, z = 0, seg = 12, radial = 6, span = Math.PI) {
  const g = new THREE.Mesh(new THREE.TorusGeometry(r, tube, radial, seg, span), material);
  g.position.set(x, y, z);
  return g;
}
// gothic-ish pointed spire (octagonal)
export function spire(r, h, material, x = 0, y = 0, z = 0, seg = 8) {
  return cone(r, h, material, x, y, z, seg);
}
// broach spire with a small base band
export function spireOn(r, baseH, h, material, x = 0, y = 0, z = 0, seg = 8) {
  return group(cyl(r, r * 1.05, baseH, material, x, y, z, seg), cone(r, h, material, x, y + baseH, z, seg));
}

// dark recessed window band helper: a slightly inset darker box on a facade
export function bandZ(w, h, material, x, y, z, t = 0.35) { return box(w, h, t, material, x, y, z); }
export function bandX(d, h, material, x, y, z, t = 0.35) { return box(t, h, d, material, x, y, z); }

// evenly-spaced window boxes on a +z facade
export function windowsZ(n, spacing, w, h, material, x, y, z, t = 0.3) {
  const g = new THREE.Group();
  for (let i = 0; i < n; i++) g.add(box(w, h, t, material, (i - (n - 1) / 2) * spacing, 0, 0));
  g.position.set(x, y, z);
  return g;
}
export function windowsX(n, spacing, d, h, material, x, y, z, t = 0.3) {
  const g = new THREE.Group();
  for (let i = 0; i < n; i++) g.add(box(t, h, d, material, 0, 0, (i - (n - 1) / 2) * spacing));
  g.position.set(x, y, z);
  return g;
}
// a grid of storey window bands on all four sides of a block
export function storeyBands(w, d, storeys, y0, sh, gap, material, x = 0, z = 0) {
  const g = new THREE.Group();
  for (let s = 0; s < storeys; s++) {
    const yy = y0 + s * (sh + gap);
    g.add(box(w - 3, sh, d + 0.5, material, 0, yy, 0));
    g.add(box(w + 0.5, sh, d - 3, material, 0, yy, 0));
  }
  g.position.set(x, 0, z);
  return g;
}
