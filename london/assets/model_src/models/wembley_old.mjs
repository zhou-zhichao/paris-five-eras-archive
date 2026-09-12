// The Empire Stadium, Wembley (1923-2003) - oval bowl ~300 x 250 m, ~30 m high,
// with the white Twin Towers (35 m, domed) flanking the entrance on the +z front.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, dome, exportGLB, out, loft, ellipse } from '../london_lib.mjs';

const g = new THREE.Group();
const RX = 150, RZ = 125, HB = 23;

// --- outer wall: rendered white concrete with pilaster banding -------------------
g.add(loft([{ y: 0, pts: ellipse(RX, RZ, 36) }, { y: HB, pts: ellipse(RX, RZ, 36) }], m(P.stone), 0, 0, 0, false, false));
for (let i = 0; i < 36; i++) {                              // pilasters
  const a = i * 2 * Math.PI / 36;
  g.add(cyl(2.2, 2.2, HB, m(P.steel), RX * 1.0 * Math.cos(a), 0, RZ * 1.0 * Math.sin(a), 6));
}
g.add(loft([{ y: HB, pts: ellipse(RX * 1.02, RZ * 1.02, 36) },
            { y: HB + 2.2, pts: ellipse(RX * 1.02, RZ * 1.02, 36) }], m(P.stone), 0, 0, 0, false, false));   // cornice

// --- shallow cantilevered roof over the stands ------------------------------------
g.add(loft([{ y: HB + 2.2, pts: ellipse(RX * 1.02, RZ * 1.02, 36) },
            { y: HB - 2, pts: ellipse(112, 90, 36) }], m(P.alu), 0, 0, 0, false, false));

// --- terracing and pitch ----------------------------------------------------------
g.add(loft([{ y: HB - 3, pts: ellipse(112, 90, 36) }, { y: 1.5, pts: ellipse(60, 42, 36) }], m(P.darkConcrete), 0, 0, 0, false, false));
g.add(loft([{ y: 0, pts: ellipse(60, 42, 36) }, { y: 0.4, pts: ellipse(60, 42, 36) }], m(P.pitch)));

// --- the Twin Towers on the +z front ---------------------------------------------
for (const sx of [-1, 1]) {
  const x = sx * 32, z = RZ + 9;
  g.add(box(17, 28, 17, m(P.stone), x, 0, z));
  g.add(box(18.6, 2.4, 18.6, m(P.stone), x, 28, z));         // cornice
  g.add(box(14, 3.6, 14, m(P.stone), x, 30.4, z));           // parapet drum base
  g.add(dome(7.0, m(P.stone), x, 34.0, z, 12, 0.45));        // shallow dome
  g.add(cyl(0.3, 0.3, 5.0, m(P.gold), x, 37.2, z, 6));       // flagpole
}
// entrance block between and behind the towers
g.add(box(48, 18, 16, m(P.stone), 0, 0, RZ + 8));
g.add(box(56, 2.2, 18, m(P.stone), 0, 18, RZ + 8));
g.add(box(100, 13, 10, m(P.stone), 0, 0, RZ + 2));

await exportGLB(g, out('wembley_old'));
