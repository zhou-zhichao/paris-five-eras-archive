// 20 Fenchurch Street, "the Walkie-Talkie" (2014) - 160 m, 37 storeys, Rafael Vinoly.
// Top-heavy: the plan flares outward with height; concave west face, big curved east
// bulge, Sky Garden crown set back under a curved roof.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out, loft, roundRect } from '../london_lib.mjs';

const g = new THREE.Group();
const H = 150;                                  // top of the glazed shaft (crown above)

// Lop-sided flare: the -x (west) face is almost straight, the +x (east) face bulges
// strongly outward, so the tower is markedly top-heavy. Depth in z grows a little.
function plan(y) {
  const t = y / H;
  const hxW = 14.5 + 4.5 * Math.pow(t, 1.25);   // west half-width  14.5 -> 19
  const hxE = 14.5 + 21 * Math.pow(t, 1.25);    // east half-width  14.5 -> 35.5
  const hz = 21 + 4.5 * Math.pow(t, 1.25);
  // broad flat N/S facades: a rounded rectangle, pushed off-centre so the east
  // face bulges much more than the west one
  return roundRect((hxW + hxE), hz * 2, 8, 4, (hxE - hxW) / 2, 0);
}

const secs = [];
for (let i = 0; i <= 10; i++) { const y = H * i / 10; secs.push({ y, pts: plan(y) }); }
g.add(loft(secs, m(P.glass)));

// horizontal spandrel bands (glass/aluminium) to read as a glazed curtain wall
for (let y = 5; y < H; y += 7.5) {
  const p = plan(y).map(([x, z]) => [x * 1.008, z * 1.01]);
  g.add(loft([{ y, pts: p }, { y: y + 1.1, pts: p }], m(P.paleGlass), 0, 0, 0, false, false));
}

// Sky Garden crown: set back, curved roof, and the plant level
const c0 = plan(H).map(([x, z]) => [x * 0.97, z * 0.93]);
const c1 = plan(H).map(([x, z]) => [x * 0.95, z * 0.72]);
g.add(loft([{ y: H, pts: c0 }, { y: H + 7, pts: c0 }, { y: H + 10, pts: c1 }], m(P.paleGlass)));
g.add(loft([{ y: H + 10, pts: c1 }, { y: H + 12.5, pts: c1.map(([x, z]) => [x * 0.9, z * 0.6]) }], m(P.alu)));

// podium
g.add(box(40, 8, 46, m(P.darkGlass), 0, 0, 0));

await exportGLB(g, out('walkie_talkie'));
