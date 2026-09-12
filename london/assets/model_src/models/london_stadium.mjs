// London Stadium, Queen Elizabeth Olympic Park (2012) - oval bowl 315 x 256 m,
// ~45 m high; white cable-net roof ring carried on 14 triangular lighting masts.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, cyl, strut, exportGLB, out, loft, ellipse } from '../london_lib.mjs';

const g = new THREE.Group();
const RX = 157.5, RZ = 128, HB = 40;

// --- lower bowl (concrete, sunk look) and upper tier ------------------------------
g.add(loft([{ y: 0, pts: ellipse(RX * 0.90, RZ * 0.90, 40) },
            { y: 18, pts: ellipse(RX * 0.97, RZ * 0.97, 40) }], m(P.concrete), 0, 0, 0, false, false));
g.add(loft([{ y: 18, pts: ellipse(RX * 0.97, RZ * 0.97, 40) },
            { y: HB, pts: ellipse(RX, RZ, 40) }], m(P.paleGlass), 0, 0, 0, false, false));
for (let y = 20; y < HB; y += 6)
  g.add(loft([{ y, pts: ellipse(RX * 1.01, RZ * 1.01, 40) },
              { y: y + 1.2, pts: ellipse(RX * 1.01, RZ * 1.01, 40) }], m(P.alu), 0, 0, 0, false, false));

// --- white tensile roof ring -------------------------------------------------------
g.add(loft([{ y: HB, pts: ellipse(RX, RZ, 40) }, { y: HB + 2.5, pts: ellipse(RX, RZ, 40) }], m(P.steel), 0, 0, 0, false, false));
g.add(loft([{ y: HB + 2.5, pts: ellipse(RX, RZ, 40) }, { y: HB + 5, pts: ellipse(88, 66, 40) }], m(P.steel), 0, 0, 0, false, false));
g.add(loft([{ y: HB + 5, pts: ellipse(88, 66, 40) }, { y: HB + 2, pts: ellipse(84, 62, 40) }], m(P.alu), 0, 0, 0, false, false));

// --- 14 triangular lighting masts around the roof ----------------------------------
for (let i = 0; i < 14; i++) {
  const a = i * 2 * Math.PI / 14, c = Math.cos(a), s = Math.sin(a);
  const bx = RX * 0.99 * c, bz = RZ * 0.99 * s;
  const top = [bx * 0.90, HB + 25, bz * 0.90];
  for (const d of [-0.06, 0.06]) {
    const f = [RX * 1.0 * Math.cos(a + d), HB + 2, RZ * 1.0 * Math.sin(a + d)];
    g.add(strut(f, top, 0.55, m(P.steel), 5));
  }
  g.add(strut([bx * 1.02, HB + 2, bz * 1.02], top, 0.55, m(P.steel), 5));
  g.add(strut([top[0] - 5, top[1], top[2]], [top[0] + 5, top[1], top[2]], 1.1, m(P.alu), 5));   // floodlight bar
}

// --- seating rake and pitch --------------------------------------------------------
g.add(loft([{ y: HB - 2, pts: ellipse(84, 62, 40) }, { y: 2, pts: ellipse(62, 44, 40) }], m(P.darkConcrete), 0, 0, 0, false, false));
g.add(loft([{ y: 0, pts: ellipse(62, 44, 40) }, { y: 0.4, pts: ellipse(62, 44, 40) }], m(P.pitch)));
g.add(loft([{ y: 0, pts: ellipse(RX + 24, RZ + 24, 32) }, { y: 1.0, pts: ellipse(RX + 24, RZ + 24, 32) }], m(P.darkConcrete)));

await exportGLB(g, out('london_stadium'));
