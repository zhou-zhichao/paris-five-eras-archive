// The Great Pagoda, Kew Gardens, Sir William Chambers 1762.  Grey brick, ten octagonal
// storeys, 50 m high; base ~15 m across, each storey narrower and shorter than the one below.
// Orientation: octagon centred on the origin; the entrance door faces +Z.
import { exportGLB, box, cyl, cone, lathe, THREE, P, M, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const bk = M(0x9a7b62), pale = M(P.pale), roof = M(0x4d5057), gold = M(P.gold), dark = M(0x3d3630);

g.add(cyl(9.2, 9.8, 1.2, M(P.dstone), 0, 0, 0, 8));
let y = 1.2;
for (let i = 0; i < 10; i++) {
  const r = 7.3 - i * 0.52;               // storey radius
  const h = 3.6 - i * 0.12;               // storey height
  g.add(cyl(r * 0.97, r, h, bk, 0, y, 0, 8));
  // arched window / door band
  for (let k = 0; k < 8; k++) {
    const a = (k + 0.5) / 8 * Math.PI * 2;
    const w = box(r * 0.42, h * 0.5, 0.5, dark, Math.cos(a) * r * 0.99, y + h * 0.28, Math.sin(a) * r * 0.99);
    w.rotation.y = -a; g.add(w);
  }
  g.add(cyl(r + 0.5, r + 0.5, 0.7, pale, 0, y + h, 0, 8));                 // balcony rail
  g.add(lathe([[r + 2.0, 0], [r + 1.3, 0.75], [r * 0.8, 1.45]], roof, 0, y + h + 0.7, 0, 8));
  g.add(cyl(r + 2.15, r + 1.9, 0.35, pale, 0, y + h + 0.6, 0, 8));
  y += h + 1.35;
}
// finial
g.add(cyl(1.1, 1.5, 1.4, pale, 0, y, 0, 8));
g.add(cone(1.2, 2.6, gold, 0, y + 1.4, 0, 8));
g.add(cyl(0.16, 0.16, 1.4, gold, 0, y + 4.0, 0, 6));

await exportGLB(g, OUT + 'kew_pagoda.glb');
