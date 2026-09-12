// One Blackfriars, "the Vase" / "the Boomerang" (2018, SimpsonHaugh) - 163 m,
// 50 storeys. A bulging convex glass form, widest around two-thirds height,
// with a lens-shaped plan.
// Convention: metres, ground y=0, footprint centred on origin, long axis x,
//             front (river, north) +z.
import { THREE, group, m, P, box, exportGLB, out, loft, ellipse } from '../london_lib.mjs';

const g = new THREE.Group();
const H = 163;

// half-axes swell from the base to ~0.62 H then pinch in towards the top
function plan(y) {
  const t = y / H;
  const s = 0.72 + 0.40 * Math.sin(Math.PI * Math.pow(t, 0.78));   // 0.72 -> ~1.12 -> 0.80
  return ellipse(23 * s, 14.5 * s, 22);
}
const secs = [];
for (let i = 0; i <= 14; i++) { const y = H * i / 14; secs.push({ y, pts: plan(y) }); }
g.add(loft(secs, m(P.paleGlass)));

// horizontal balcony/spandrel bands follow the bulge
for (let y = 4; y < H - 2; y += 5.5) {
  const p = plan(y).map(([x, z]) => [x * 1.02, z * 1.03]);
  g.add(loft([{ y, pts: p }, { y: y + 1.0, pts: p }], m(P.glass), 0, 0, 0, false, false));
}

// crown: a small set-back plant drum
g.add(loft([{ y: H, pts: plan(H).map(([x, z]) => [x * 0.8, z * 0.8]) },
            { y: H + 5, pts: plan(H).map(([x, z]) => [x * 0.7, z * 0.7]) }], m(P.alu)));

// podium
g.add(box(56, 8, 40, m(P.darkGlass), 0, 0, 0));

await exportGLB(g, out('one_blackfriars'));
