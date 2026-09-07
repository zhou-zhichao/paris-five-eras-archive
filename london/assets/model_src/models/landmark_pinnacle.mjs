// Landmark Pinnacle, Marsh Wall, Isle of Dogs (2020, Squire & Partners) - 233 m,
// 75 storeys. A very thin residential slab with shallow setbacks and a stepped,
// crown-lit top; pale glass with strong horizontal balcony banding.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out, loft, roundRect } from '../london_lib.mjs';

const g = new THREE.Group();
const H = 233;

// slab plan 52 x 26, shedding width in three shallow setbacks
function plan(y) {
  const s = y < 120 ? 1.0 : y < 190 ? 0.94 : 0.86;
  const t = y < 120 ? 0.98 : y < 190 ? 0.92 : 0.84;
  return roundRect(52 * s, 26 * t, 6, 3);
}
g.add(loft([{ y: 0, pts: plan(0) }, { y: 120, pts: plan(0) },
            { y: 120, pts: plan(150) }, { y: 190, pts: plan(150) },
            { y: 190, pts: plan(200) }, { y: H, pts: plan(200) }], m(P.paleGlass)));

// balcony bands every floor
for (let y = 4; y < H - 2; y += 3.1) {
  const p = plan(y).map(([x, z]) => [x * 1.03, z * 1.05]);
  g.add(loft([{ y, pts: p }, { y: y + 0.7, pts: p }], m(P.glass), 0, 0, 0, false, false));
}
// vertical mullion piers breaking the slab into three bays
for (const x of [-17, 0, 17]) g.add(box(3.2, H, 27.5, m(P.steel), x, 0, 0));

// stepped crown
g.add(loft([{ y: H, pts: plan(200) }, { y: H + 6, pts: plan(200).map(([x, z]) => [x * 0.8, z * 0.8]) },
            { y: H + 9, pts: plan(200).map(([x, z]) => [x * 0.5, z * 0.6]) }], m(P.alu)));

g.add(box(66, 9, 40, m(P.darkConcrete), 0, 0, 0));

await exportGLB(g, out('landmark_pinnacle'));
