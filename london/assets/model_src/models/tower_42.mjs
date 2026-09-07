// Tower 42 / NatWest Tower (1980) - 183 m, 47 storeys. Three chevron wings around a
// core, stepping up; dark bronze glass with strong horizontal banding.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, exportGLB, out, poly, banded } from '../london_lib.mjs';

const g = new THREE.Group();
const HS = [183, 166, 149];               // the three wings step down

// central service core (hexagonal), runs the full height
g.add(cyl(12.5, 12.5, 183, m(P.darkConcrete), 0, 0, 0, 6));

// three chevron wings at 120 deg
for (let k = 0; k < 3; k++) {
  const th = k * 2 * Math.PI / 3 + Math.PI / 2;
  const H = HS[k];
  const wing = new THREE.Group();
  // chevron = two slabs meeting at an outward apex
  for (const s of [-1, 1]) {
    const b = banded(15, H, 30, P.darkGlass, P.black, 0, 0, 0, 4.2, 0.45);
    b.rotation.y = s * 0.42;
    b.position.set(s * 11, 0, 15);
    wing.add(b);
  }
  wing.rotation.y = th;
  g.add(wing);
}

// rooftop plant + mast
g.add(box(16, 6, 16, m(P.black), 0, 183, 0));
g.add(cyl(0.5, 0.9, 9, m(P.steel), 0, 189, 0, 6));

// podium (Old Broad Street)
g.add(box(64, 14, 56, m(P.stone), 0, 0, 0));

await exportGLB(g, out('tower_42'));
