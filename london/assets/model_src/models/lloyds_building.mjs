// Lloyd's of London, Lime Street (1986) - 95.1 m to the top of the tallest service
// tower, Richard Rogers. "Inside-out": six stainless service towers with blue
// maintenance cranes on top, stepped main block, barrel-vaulted atrium roof.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, strut, exportGLB, out, banded } from '../london_lib.mjs';

const g = new THREE.Group();

// --- stepped main block (the atrium block steps down towards +x) ------------------
g.add(banded(46, 68, 40, P.paleGlass, P.alu, -11, 0, 0, 4.0, 0.5));
g.add(banded(22, 46, 40, P.paleGlass, P.alu, 23, 0, 0, 4.0, 0.5));
g.add(banded(16, 30, 34, P.paleGlass, P.alu, 42, 0, 0, 4.0, 0.5));
// barrel-vaulted glass roof over the Room (ridge along x)
const vault = cyl(11, 11, 44, m(P.paleGlass), -11, 0, 0, 12);
vault.rotation.z = Math.PI / 2; vault.position.set(-11, 68, 0);
vault.scale.set(0.55, 1, 1); g.add(vault);

// --- six external service towers, stainless, rising above the roof ---------------
// [x, z, plan size, height]
const TOWERS = [[-36, 22, 9, 88], [-36, -22, 9, 84], [2, 25, 8, 95.1],
                [2, -25, 8, 80], [34, 22, 7.5, 76], [34, -22, 7.5, 72]];
for (const [x, z, s, h] of TOWERS) {
  g.add(box(s, h, s, m(P.alu), x, 0, z));
  for (let y = 5; y < h; y += 4) g.add(box(s + 0.7, 1.0, s + 0.7, m(P.steel), x, y, z));
  // exposed lift shafts / stair drums clipped to the outside
  g.add(cyl(2.6, 2.6, h * 0.92, m(P.steel), x + (x < 0 ? -s / 2 - 1.6 : s / 2 + 1.6), 0, z, 10));
  // blue maintenance crane: mast + jib + counterweight
  g.add(cyl(0.5, 0.6, 11, m(P.glass), x, h, z, 6));
  g.add(strut([x - 5, h + 10, z], [x + 9, h + 10, z], 0.45, m(P.glass), 5));
  g.add(box(1.8, 1.6, 1.8, m(P.glass), x - 5.5, h + 9.2, z));
}

// --- exposed pipework and the escape stairs on the long facades ------------------
for (const sz of [-1, 1]) for (let i = 0; i < 6; i++) {
  const x = -44 + i * 12;
  g.add(cyl(1.1, 1.1, 62, m(P.steel), x, 0, sz * 21.5, 8));
}

// ground / plaza
g.add(box(104, 1.0, 56, m(P.darkConcrete), 4, 0, 0));

await exportGLB(g, out('lloyds_building'));
