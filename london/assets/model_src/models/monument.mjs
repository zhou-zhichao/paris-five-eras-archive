// The Monument to the Great Fire of London, Wren & Hooke 1677.  Portland stone.
// Free-standing Doric column 61.6 m to the top of the gilded flaming urn.
// Orientation: square pedestal centred on the origin; the inscribed panel faces +Z.
import { exportGLB, box, cyl, cone, lathe, THREE, P, M, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), gold = M(P.gold), dark = M(0x4a463d);

// steps + pedestal (21 ft square, 40 ft high)
for (let i = 0; i < 3; i++) g.add(box(11 - i * 1.2, 0.5, 11 - i * 1.2, dk, 0, i * 0.5, 0));
g.add(box(7.6, 1.6, 7.6, pale, 0, 1.5, 0));
g.add(box(6.4, 9.6, 6.4, st, 0, 3.1, 0));
g.add(box(5.4, 3.6, 0.5, dk, 0, 5.6, 3.25));            // relief panel (+z)
for (const [dx, dz] of [[1, 0], [-1, 0], [0, -1]])
  g.add(box(dx ? 0.5 : 4.6, 4.6, dz ? 0.5 : 4.6, dark, dx * 3.25, 5.6, dz * 3.25));
g.add(box(7.4, 1.4, 7.4, pale, 0, 12.7, 0));

// Doric column: base, fluted shaft (15 ft dia), capital
g.add(cyl(2.55, 2.9, 1.8, pale, 0, 14.1, 0, 16));
g.add(cyl(2.15, 2.4, 34.5, st, 0, 15.9, 0, 16));
for (let i = 0; i < 16; i++) {                           // flutes
  const a = i / 16 * Math.PI * 2, r = 2.3;
  const f = box(0.42, 34.5, 0.42, pale, Math.cos(a) * r, 15.9, Math.sin(a) * r);
  f.rotation.y = -a; g.add(f);
}
g.add(cyl(2.5, 2.2, 1.4, pale, 0, 50.4, 0, 16));         // echinus
g.add(box(6.0, 1.2, 6.0, pale, 0, 51.8, 0));             // abacus

// viewing platform + iron cage
g.add(box(7.4, 0.7, 7.4, pale, 0, 53.0, 0));
g.add(cyl(2.3, 2.3, 3.6, dark, 0, 53.7, 0, 12));
g.add(cyl(2.9, 2.9, 0.6, pale, 0, 57.3, 0, 12));
// gilded flaming urn
g.add(lathe([[1.5, 0], [1.7, 0.8], [1.4, 1.8], [0.8, 2.6], [1.2, 3.4], [0.9, 4.0], [0.3, 4.4], [0, 4.6]],
  gold, 0, 57.9, 0, 12));

await exportGLB(g, OUT + 'monument.glb');
