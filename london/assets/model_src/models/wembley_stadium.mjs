// Wembley Stadium (2007, Foster + Partners / Populous) - oval bowl ~315 x 275 m,
// roof ~52 m, and the 133 m tall, 315 m span lattice steel arch leaning over the
// north stand and carrying the roof on cables.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, strut, tube, exportGLB, out, loft, ellipse } from '../london_lib.mjs';

const g = new THREE.Group();
const RX = 157.5, RZ = 137.5, HB = 48;          // outer half-axes and bowl height

// --- outer bowl skin (slightly flared, banded) -----------------------------------
g.add(loft([{ y: 0, pts: ellipse(RX * 0.94, RZ * 0.94, 40) },
            { y: 14, pts: ellipse(RX, RZ, 40) },
            { y: HB, pts: ellipse(RX, RZ, 40) }], m(P.paleGlass), 0, 0, 0, false, false));
for (let y = 8; y < HB; y += 8)
  g.add(loft([{ y, pts: ellipse(RX * 1.008, RZ * 1.008, 40) },
              { y: y + 1.4, pts: ellipse(RX * 1.008, RZ * 1.008, 40) }], m(P.alu), 0, 0, 0, false, false));

// --- roof ring: outer edge down to the inner opening over the pitch --------------
g.add(loft([{ y: HB, pts: ellipse(RX, RZ, 40) }, { y: HB + 4, pts: ellipse(RX, RZ, 40) }], m(P.alu), 0, 0, 0, false, false));
g.add(loft([{ y: HB + 4, pts: ellipse(RX, RZ, 40) }, { y: HB + 1, pts: ellipse(78, 56, 40) }], m(P.steel), 0, 0, 0, false, false));

// --- seating bowl and the pitch ---------------------------------------------------
g.add(loft([{ y: HB - 2, pts: ellipse(78, 56, 40) }, { y: 2, pts: ellipse(62, 44, 40) }], m(P.darkConcrete), 0, 0, 0, false, false));
g.add(loft([{ y: 0, pts: ellipse(62, 44, 40) }, { y: 0.4, pts: ellipse(62, 44, 40) }], m(P.pitch)));

// --- the arch: 315 m span, 133 m apex, leaning over the north (-z) stand ---------
const ARCH = [[-RX, 2, -96], [-138, 52, -84], [-86, 105, -62], [0, 133, -48],
              [86, 105, -62], [138, 52, -84], [RX, 2, -96]];
g.add(tube(ARCH, 3.5, m(P.steel), 60, 8));
// lattice reads: a thinner parallel chord plus cross bracing
const ARCH2 = ARCH.map(([x, y, z]) => [x * 0.99, y - 6.5, z + 1.5]);
g.add(tube(ARCH2, 1.6, m(P.steel), 48, 6));
// arch feet
for (const sx of [-1, 1]) g.add(cyl(7, 9, 8, m(P.concrete), sx * RX, 0, -96, 10));
// cable stays from the arch down to the roof ring (north) and back stays (south)
for (let i = 1; i < 12; i++) {
  const t = i / 12, ai = Math.round(t * 60);
  const c = new THREE.CatmullRomCurve3(ARCH.map(p => new THREE.Vector3(...p))).getPoint(t);
  const a = Math.PI + (t - 0.5) * 1.9;
  g.add(strut([c.x, c.y, c.z], [92 * Math.cos(a - Math.PI / 2) * 0 + c.x * 0.62, HB + 3, -RZ * 0.55], 0.5, m(P.steel), 4));
  g.add(strut([c.x, c.y, c.z], [c.x * 0.75, HB + 3, RZ * 0.42], 0.5, m(P.steel), 4));
}

// concourse ramps / podium
g.add(loft([{ y: 0, pts: ellipse(RX + 26, RZ + 26, 32) }, { y: 1.2, pts: ellipse(RX + 26, RZ + 26, 32) }], m(P.darkConcrete)));

await exportGLB(g, out('wembley_stadium'));
