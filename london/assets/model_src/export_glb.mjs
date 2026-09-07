// Minimal GLB exporter for three.js scenes (node, no DOM needed).
// Bakes world transforms, merges everything into ONE mesh with flat shading and
// per-vertex colours (COLOR_0) taken from each mesh's material.color.
// Units: metres. Convention for landmark models: ground plane y=0, model centred
// on x/z, "front" facade towards +z.  Blender imports glTF Y-up -> Z-up automatically.
//
// usage (from a model script):
//   import { exportGLB } from './export_glb.mjs';
//   await exportGLB(group, 'out/model.glb');
import * as THREE from 'three';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

function pad4(n) { return (4 - (n % 4)) % 4; }

export function bakeScene(root) {
  root.updateMatrixWorld(true);
  const pos = [], nrm = [], col = [], idx = [];
  let base = 0;
  const tmpN = new THREE.Matrix3();
  root.traverse(o => {
    if (!o.isMesh) return;
    let g = o.geometry.index ? o.geometry.toNonIndexed() : o.geometry;
    g = g.clone();
    g.applyMatrix4(o.matrixWorld);
    g.computeVertexNormals();           // flat normals (non-indexed)
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    const p = g.attributes.position.array, n = g.attributes.normal.array;
    const count = g.attributes.position.count;
    const groups = g.groups.length ? g.groups : [{ start: 0, count, materialIndex: 0 }];
    for (const grp of groups) {
      const m = mats[Math.min(grp.materialIndex ?? 0, mats.length - 1)] || mats[0];
      const c = (m && m.color) ? m.color : new THREE.Color(0.8, 0.8, 0.8);
      const end = grp.count === Infinity ? count : Math.min(count, grp.start + grp.count);
      for (let i = grp.start; i < end; i++) {
        pos.push(p[3 * i], p[3 * i + 1], p[3 * i + 2]);
        nrm.push(n[3 * i], n[3 * i + 1], n[3 * i + 2]);
        col.push(c.r, c.g, c.b, 1.0);
        idx.push(base + (i - grp.start) + (grp.start));
      }
    }
    base += count;
  });
  // rebuild indices sequentially (we pushed verts in order)
  const nverts = pos.length / 3;
  const index = new Uint32Array(nverts);
  for (let i = 0; i < nverts; i++) index[i] = i;
  return { pos: new Float32Array(pos), nrm: new Float32Array(nrm), col: new Float32Array(col), index };
}

export function toGLB(root, name = 'model') {
  const { pos, nrm, col, index } = bakeScene(root);
  const buffers = [];
  const views = [];
  let byteLength = 0;
  function addView(arr, target) {
    const bytes = new Uint8Array(arr.buffer, arr.byteOffset, arr.byteLength);
    views.push({ buffer: 0, byteOffset: byteLength, byteLength: bytes.byteLength, target });
    buffers.push(bytes);
    byteLength += bytes.byteLength;
    const p = pad4(byteLength);
    if (p) { buffers.push(new Uint8Array(p)); byteLength += p; }
    return views.length - 1;
  }
  const vPos = addView(pos, 34962), vNrm = addView(nrm, 34962), vCol = addView(col, 34962), vIdx = addView(index, 34963);
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < pos.length; i += 3) for (let k = 0; k < 3; k++) { min[k] = Math.min(min[k], pos[i + k]); max[k] = Math.max(max[k], pos[i + k]); }
  const nverts = pos.length / 3;
  const json = {
    asset: { version: '2.0', generator: 'export_glb.mjs' },
    scene: 0,
    scenes: [{ nodes: [0] }],
    nodes: [{ mesh: 0, name }],
    meshes: [{ name, primitives: [{ attributes: { POSITION: 0, NORMAL: 1, COLOR_0: 2 }, indices: 3, material: 0, mode: 4 }] }],
    materials: [{ name: 'flat', pbrMetallicRoughness: { baseColorFactor: [1, 1, 1, 1], metallicFactor: 0, roughnessFactor: 0.9 } }],
    accessors: [
      { bufferView: vPos, componentType: 5126, count: nverts, type: 'VEC3', min, max },
      { bufferView: vNrm, componentType: 5126, count: nverts, type: 'VEC3' },
      { bufferView: vCol, componentType: 5126, count: nverts, type: 'VEC4' },
      { bufferView: vIdx, componentType: 5125, count: nverts, type: 'SCALAR' },
    ],
    bufferViews: views,
    buffers: [{ byteLength }],
  };
  let jsonStr = JSON.stringify(json);
  while (jsonStr.length % 4) jsonStr += ' ';
  const jsonBytes = Buffer.from(jsonStr, 'utf8');
  const binBytes = Buffer.concat(buffers.map(b => Buffer.from(b.buffer, b.byteOffset, b.byteLength)));
  const total = 12 + 8 + jsonBytes.length + 8 + binBytes.length;
  const out = Buffer.alloc(total);
  let o = 0;
  out.writeUInt32LE(0x46546C67, o); o += 4; out.writeUInt32LE(2, o); o += 4; out.writeUInt32LE(total, o); o += 4;
  out.writeUInt32LE(jsonBytes.length, o); o += 4; out.writeUInt32LE(0x4E4F534A, o); o += 4; jsonBytes.copy(out, o); o += jsonBytes.length;
  out.writeUInt32LE(binBytes.length, o); o += 4; out.writeUInt32LE(0x004E4942, o); o += 4; binBytes.copy(out, o);
  return { glb: out, stats: { vertices: nverts, triangles: nverts / 3, bbox: { min, max } } };
}

export async function exportGLB(root, path) {
  const { glb, stats } = toGLB(root, path.split(/[\\/]/).pop().replace(/\.glb$/, ''));
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, glb);
  console.log(`[glb] ${path}  tris=${stats.triangles}  bbox x[${stats.bbox.min[0].toFixed(1)},${stats.bbox.max[0].toFixed(1)}] y[${stats.bbox.min[1].toFixed(1)},${stats.bbox.max[1].toFixed(1)}] z[${stats.bbox.min[2].toFixed(1)},${stats.bbox.max[2].toFixed(1)}]`);
  return stats;
}

// ---- convenience helpers for the modelling scripts ---------------------------------
export function mat(hex) { return new THREE.MeshStandardMaterial({ color: new THREE.Color(hex), flatShading: true }); }
export function box(w, h, d, material, x = 0, y = 0, z = 0) {   // y = bottom of the box
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
  m.position.set(x, y + h / 2, z);
  return m;
}
export function cyl(rTop, rBot, h, material, x = 0, y = 0, z = 0, seg = 16) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(rTop, rBot, h, seg), material);
  m.position.set(x, y + h / 2, z);
  return m;
}
export function cone(r, h, material, x = 0, y = 0, z = 0, seg = 8) { return cyl(0, r, h, material, x, y, z, seg); }
export function dome(r, material, x = 0, y = 0, z = 0, seg = 16, squash = 1.0) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, seg, Math.max(4, seg / 2), 0, Math.PI * 2, 0, Math.PI / 2), material);
  m.position.set(x, y, z); m.scale.set(1, squash, 1);
  return m;
}
// prism roof: ridge along x (length w), spans d, height h; y = eaves height
export function gableRoof(w, d, h, material, x = 0, y = 0, z = 0, alongX = true, overhang = 0.3) {
  const shape = new THREE.Shape();
  const hd = d / 2 + overhang;
  shape.moveTo(-hd, 0); shape.lineTo(hd, 0); shape.lineTo(0, h); shape.closePath();
  const g = new THREE.ExtrudeGeometry(shape, { depth: w + 2 * overhang, bevelEnabled: false });
  g.translate(0, 0, -(w + 2 * overhang) / 2);
  const m = new THREE.Mesh(g, material);
  m.position.set(x, y, z);
  m.rotation.y = alongX ? Math.PI / 2 : 0;
  return m;
}
// hip roof: rectangular base w x d, ridge shortened by ridgeFrac, height h
export function hipRoof(w, d, h, material, x = 0, y = 0, z = 0, ridgeFrac = 0.5) {
  const g = new THREE.BufferGeometry();
  const long = Math.max(w, d), short = Math.min(w, d);
  const rl = (long - short) * ridgeFrac / 2;
  const ax = w >= d;
  const P = (u, v, hh) => ax ? [u, hh, v] : [v, hh, u];
  const b = [P(-long / 2, -short / 2, 0), P(long / 2, -short / 2, 0), P(long / 2, short / 2, 0), P(-long / 2, short / 2, 0)];
  const r = [P(-rl, 0, h), P(rl, 0, h)];
  const tris = [
    [b[0], b[1], r[1]], [b[0], r[1], r[0]],
    [b[2], b[3], r[0]], [b[2], r[0], r[1]],
    [b[1], b[2], r[1]], [b[3], b[0], r[0]],
  ];
  const arr = [];
  for (const t of tris) for (const p of t) arr.push(...p);
  g.setAttribute('position', new THREE.Float32BufferAttribute(arr, 3));
  const m = new THREE.Mesh(g, material);
  m.position.set(x, y, z);
  return m;
}
// extruded footprint polygon (array of [x,z]) from y to y+h
export function prism(points, h, material, x = 0, y = 0, z = 0) {
  const shape = new THREE.Shape(points.map(p => new THREE.Vector2(p[0], p[1])));
  const g = new THREE.ExtrudeGeometry(shape, { depth: h, bevelEnabled: false });
  g.rotateX(-Math.PI / 2);   // extrude along +y
  g.translate(0, 0, 0);
  const m = new THREE.Mesh(g, material);
  m.position.set(x, y, z);
  return m;
}
// lathe (profile of [radius, height] pairs) for spires, domes, columns
export function lathe(profile, material, x = 0, y = 0, z = 0, seg = 16) {
  const m = new THREE.Mesh(new THREE.LatheGeometry(profile.map(p => new THREE.Vector2(p[0], p[1])), seg), material);
  m.position.set(x, y, z);
  return m;
}
export function group(...children) { const g = new THREE.Group(); for (const c of children) g.add(c); return g; }
export { THREE };
