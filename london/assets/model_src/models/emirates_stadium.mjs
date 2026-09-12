// Emirates Stadium, Holloway (2006, Populous) - elliptical bowl ~230 x 200 m,
// ~41 m high, with the roof carried on four big tubular tripod girders.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, strut, exportGLB, out, loft, ellipse } from '../london_lib.mjs';

const g = new THREE.Group();
const RX = 115, RZ = 100, HB = 36;

// --- clad elliptical bowl ---------------------------------------------------------
g.add(loft([{ y: 0, pts: ellipse(RX * 0.96, RZ * 0.96, 36) },
            { y: 10, pts: ellipse(RX, RZ, 36) },
            { y: HB, pts: ellipse(RX, RZ, 36) }], m(P.paleGlass), 0, 0, 0, false, false));
for (let y = 6; y < HB; y += 7)
  g.add(loft([{ y, pts: ellipse(RX * 1.01, RZ * 1.01, 36) },
              { y: y + 1.3, pts: ellipse(RX * 1.01, RZ * 1.01, 36) }], m(P.alu), 0, 0, 0, false, false));

// --- roof: outer fascia ring, then a sloping polycarbonate roof to the opening ----
g.add(loft([{ y: HB, pts: ellipse(RX, RZ, 36) }, { y: HB + 3, pts: ellipse(RX, RZ, 36) }], m(P.steel), 0, 0, 0, false, false));
g.add(loft([{ y: HB + 3, pts: ellipse(RX, RZ, 36) }, { y: HB + 5, pts: ellipse(66, 50, 36) }], m(P.steel), 0, 0, 0, false, false));
g.add(loft([{ y: HB + 5, pts: ellipse(66, 50, 36) }, { y: HB + 2, pts: ellipse(62, 46, 36) }], m(P.paleGlass), 0, 0, 0, false, false));

// --- the four tubular tripod girders spanning the long sides ---------------------
for (const sz of [-1, 1]) {
  for (const dz of [0.44, 0.80]) {
    const z = sz * RZ * dz;
    const XM = RX * Math.sqrt(1 - dz * dz) * 0.98;      // stay inside the ellipse
    const pts = [];
    for (let i = 0; i <= 8; i++) {
      const t = i / 8, x = -XM + 2 * XM * t;
      pts.push([x, HB + 4 + 8 * Math.sin(Math.PI * t), z]);
    }
    for (let i = 0; i < 8; i++) g.add(strut(pts[i], pts[i + 1], 1.5, m(P.steel), 6));
    // tripod legs down onto the bowl rim
    for (const sx of [-1, 1]) g.add(strut([sx * XM, HB + 4, z], [sx * XM * 1.04, HB - 8, z * 0.95], 1.6, m(P.steel), 6));
  }
}

// --- seating rake, pitch and the entrance bridges ---------------------------------
g.add(loft([{ y: HB - 2, pts: ellipse(62, 46, 36) }, { y: 1.5, pts: ellipse(58, 40, 36) }], m(P.darkConcrete), 0, 0, 0, false, false));
g.add(loft([{ y: 0, pts: ellipse(56, 38, 36) }, { y: 0.4, pts: ellipse(56, 38, 36) }], m(P.pitch)));
for (const [x, z] of [[0, RZ + 14], [0, -RZ - 14], [RX + 14, 0], [-RX - 14, 0]])
  g.add(box(Math.abs(x) > 0 ? 30 : 44, 6, Math.abs(x) > 0 ? 44 : 30, m(P.darkConcrete), x, 0, z));

await exportGLB(g, out('emirates_stadium'));
