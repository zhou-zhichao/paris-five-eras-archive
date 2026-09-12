// Generic City office tower C - a 140 m glass tower, 34 storeys, with one fully
// rounded corner and a slight taper; pale blue curtain wall. 2010s filler.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out, loft } from '../london_lib.mjs';

const g = new THREE.Group();
const W = 40, D = 34, H = 140;

// plan: rectangle with the +x/+z corner swept into a quarter circle
function plan(s) {
  const hx = W / 2 * s, hz = D / 2 * s, R = 16 * s;
  const p = [[-hx, -hz], [hx, -hz], [hx, hz - R]];
  for (let i = 1; i <= 6; i++) {
    const a = -Math.PI / 2 + i * (Math.PI / 2) / 6;
    p.push([hx - R + R * Math.cos(a), hz - R + R * Math.sin(a)]);
  }
  p.push([-hx, hz]);
  return p;
}
g.add(loft([{ y: 0, pts: plan(1.0) }, { y: H, pts: plan(0.90) }], m(P.glass)));
for (let y = 4; y < H - 2; y += 4.0) {
  const s = 1.0 - 0.10 * y / H;
  const p = plan(s).map(([x, z]) => [x * 1.012, z * 1.012]);
  g.add(loft([{ y, pts: p }, { y: y + 1.3, pts: p }], m(P.paleGlass), 0, 0, 0, false, false));
}
// crown: a set-back plant enclosure that follows the plan
g.add(loft([{ y: H, pts: plan(0.86) }, { y: H + 7, pts: plan(0.80) }], m(P.alu)));
g.add(box(W + 16, 9, D + 14, m(P.stone), 0, 0, 0));

await exportGLB(g, out('office_tower_generic_c'));
