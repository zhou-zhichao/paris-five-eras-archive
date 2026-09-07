// 22 Bishopsgate (2020) - 278 m, 62 storeys, PLP Architecture. Faceted, stepped
// plan: a bulky irregular polygon that sheds facets and steps back as it rises.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out, loft, scalePoly } from '../london_lib.mjs';

const g = new THREE.Group();
const H = 278;

// irregular 9-sided base plan, ~62 x 58 m
const R = [31, 28, 30, 26, 29, 31, 27, 30, 28];
const base = R.map((r, i) => { const a = i * 2 * Math.PI / 9 + 0.25; return [r * Math.cos(a), r * 0.94 * Math.sin(a)]; });

// stepped setbacks: [height, plan scale]
const STEPS = [[0, 1.00], [92, 0.97], [92, 0.86], [160, 0.84], [160, 0.72],
               [214, 0.70], [214, 0.60], [258, 0.59], [258, 0.50], [278, 0.49]];
g.add(loft(STEPS.map(([y, s]) => ({ y, pts: scalePoly(base, s) })), m(P.glass)));

// spandrel banding follows the setback profile
function scaleAt(y) {
  for (let i = 0; i < STEPS.length - 1; i++) {
    const [y0, s0] = STEPS[i], [y1, s1] = STEPS[i + 1];
    if (y1 > y0 && y <= y1) return s0 + (s1 - s0) * (y - y0) / (y1 - y0);
  }
  return 0.49;
}
for (let y = 6; y < H - 2; y += 8) {
  const p = scalePoly(base, scaleAt(y) * 1.012);
  g.add(loft([{ y, pts: p }, { y: y + 1.2, pts: p }], m(P.paleGlass), 0, 0, 0, false, false));
}

// crown plant / viewing gallery
g.add(loft([{ y: H, pts: scalePoly(base, 0.46) }, { y: H + 5, pts: scalePoly(base, 0.40) }], m(P.alu)));

// podium
g.add(box(76, 10, 68, m(P.stone), 0, 0, 0));

await exportGLB(g, out('twentytwo_bishopsgate'));
