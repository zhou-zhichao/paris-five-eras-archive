// 52 Lime Street, "the Scalpel" (2018, KPF) - 190 m, 38 storeys. A crystalline
// wedge: the west face rakes back in two big sloping planes to a sharp blade.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out, loft } from '../london_lib.mjs';

const g = new THREE.Group();
const H = 190;

// plan at height y: a quadrilateral whose -x edge slides inward (the raked face)
// and whose depth shrinks, giving the blade profile.
function plan(y) {
  const t = y / H;
  const xW = -24 + 27 * Math.min(1, t / 0.78);            // west edge marches east
  const xE = 24 - 4 * t;
  const zN = -21 + 8 * t, zS = 21 - 3 * t;
  return [[xW, zN], [xE, zN], [xE, zS], [xW + 4 * t, zS]];
}
const secs = [];
for (let i = 0; i <= 12; i++) { const y = H * i / 12; secs.push({ y, pts: plan(y) }); }
g.add(loft(secs, m(P.darkGlass)));

// the sharper upper blade: a second facet leaning the other way
g.add(loft([{ y: 120, pts: [[-6, -13], [20, -13], [20, 18], [-6, 18]] },
            { y: H, pts: [[3, -13], [20, -13], [20, 18], [3, 18]] },
            { y: H + 9, pts: [[11, -8], [20, -8], [20, 12], [11, 12]] }], m(P.glass)));

// spandrel banding on the main mass
for (let y = 5; y < H; y += 7) {
  const p = plan(y).map(([x, z]) => [x * 1.0 + (x < 0 ? -0.4 : 0.4), z * 1.02]);
  g.add(loft([{ y, pts: p }, { y: y + 1.1, pts: p }], m(P.paleGlass), 0, 0, 0, false, false));
}

// podium
g.add(box(60, 10, 52, m(P.stone), 0, 0, 0));

await exportGLB(g, out('scalpel'));
