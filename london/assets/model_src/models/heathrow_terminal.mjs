// Heathrow Terminal 5 (2008, RSHP) - the 396 x 176 m single-span concourse under a
// wave roof on external steel legs, the 87 m control tower, and the two satellite
// piers (T5B, T5C) parallel to the north.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, strut, exportGLB, out, loft } from '../london_lib.mjs';

const g = new THREE.Group();
const GL = m(P.paleGlass), STL = m(P.steel), DC = m(P.darkConcrete), AL = m(P.alu);
const L = 396, W = 176;

// --- the concourse box (glazed walls) --------------------------------------------
g.add(box(L, 26, W, GL, 0, 0, 0));
for (let y = 4; y < 26; y += 5.5) g.add(box(L + 1.2, 1.3, W + 1.2, AL, 0, y, 0));

// --- the wave roof: a shallow vault across z that undulates along x --------------
const NX = 22, NZ = 12;
const roofY = (x, z) => 26 + 13 * Math.cos(Math.PI * z / W) + 2.6 * Math.sin(x / L * Math.PI * 5);
const pos = [];
const V = (x, z) => [x, roofY(x, z), z];
for (let i = 0; i < NX; i++) for (let k = 0; k < NZ; k++) {
  const x0 = -L / 2 + L * i / NX, x1 = -L / 2 + L * (i + 1) / NX;
  const z0 = -W / 2 + W * k / NZ, z1 = -W / 2 + W * (k + 1) / NZ;
  const a = V(x0, z0), b = V(x1, z0), c = V(x1, z1), d = V(x0, z1);
  pos.push(...a, ...b, ...c, ...a, ...c, ...d);
  // the underside, 1.6 m below, so the roof reads as a slab
  const s = 1.6;
  pos.push(a[0], a[1] - s, a[2], c[0], c[1] - s, c[2], b[0], b[1] - s, b[2]);
  pos.push(a[0], a[1] - s, a[2], d[0], d[1] - s, d[2], c[0], c[1] - s, c[2]);
}
const rg = new THREE.BufferGeometry();
rg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
g.add(new THREE.Mesh(rg, STL));

// --- the external steel legs carrying the roof -----------------------------------
for (let i = 0; i <= 10; i++) {
  const x = -L / 2 + L * i / 10;
  for (const sz of [-1, 1]) {
    const z = sz * (W / 2 + 12);
    g.add(strut([x, 0, z], [x, roofY(x, sz * W / 2) - 2, sz * W / 2], 1.5, STL, 6));
    g.add(strut([x, 0, z], [x, 16, sz * (W / 2 + 2)], 1.0, STL, 5));
  }
}

// --- the 87 m control tower on the +z side ---------------------------------------
g.add(cyl(4.0, 6.0, 70, AL, 150, 0, W / 2 + 70, 12));
g.add(cyl(9.0, 7.0, 9, GL, 150, 70, W / 2 + 70, 14));
g.add(cyl(10.0, 10.0, 1.4, DC, 150, 79, W / 2 + 70, 14));
g.add(cyl(0.5, 0.9, 7, STL, 150, 80.4, W / 2 + 70, 6));

// --- the two satellite piers to the -z side --------------------------------------
for (const dz of [-220, -400]) {
  g.add(box(430, 18, 46, GL, 0, 0, dz));
  g.add(loft([{ y: 18, pts: [[-215, -25], [215, -25], [215, 25], [-215, 25]] },
              { y: 25, pts: [[-215, -12], [215, -12], [215, 12], [-215, 12]] }], STL, 0, 0, dz));
  g.add(box(440, 1.0, 90, DC, 0, 0, dz));
}

// apron
g.add(box(560, 0.8, 260, DC, 0, 0, 30));

await exportGLB(g, out('heathrow_terminal'));
