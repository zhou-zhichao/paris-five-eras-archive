// Centre Point, St Giles Circus (1966, Richard Seifert) - 117 m, 34 storeys.
// Slim slab with the famous precast honeycomb facade; chamfered ends; low podium
// block linked by a bridge.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, exportGLB, out, loft } from '../london_lib.mjs';

const g = new THREE.Group();
const W = 58, D = 17, H = 117;

// slab with chamfered (faceted) ends
const pts = [[-W / 2, -D / 2 + 4], [-W / 2 + 5, -D / 2], [W / 2 - 5, -D / 2], [W / 2, -D / 2 + 4],
             [W / 2, D / 2 - 4], [W / 2 - 5, D / 2], [-W / 2 + 5, D / 2], [-W / 2, D / 2 - 4]];
g.add(loft([{ y: 0, pts }, { y: H, pts }], m(P.darkConcrete)));

// --- honeycomb facade: horizontal floor bands crossed by vertical mullions -------
const grow = s => pts.map(([x, z]) => [x * s, z * (1 + (s - 1) * 2.2)]);
for (let y = 4; y < H; y += 3.4) {
  const p = grow(1.012);
  g.add(loft([{ y, pts: p }, { y: y + 1.5, pts: p }], m(P.stone), 0, 0, 0, false, false));
}
for (let i = 0; i <= 18; i++) {             // vertical precast mullions
  const x = -W / 2 + 1.6 + i * (W - 3.2) / 18;
  for (const sz of [-1, 1]) g.add(box(1.5, H, 1.4, m(P.stone), x, 0, sz * (D / 2 + 0.3)));
}
for (const sx of [-1, 1]) g.add(box(1.6, H, D + 1.2, m(P.stone), sx * (W / 2 + 0.3), 0, 0));

// roof plant
g.add(box(W * 0.7, 5, D * 0.8, m(P.darkConcrete), 0, H, 0));

// --- podium, the linked lower block and the bridge --------------------------------
g.add(box(W + 22, 9, D + 16, m(P.darkConcrete), 0, 0, 0));
g.add(box(26, 32, 20, m(P.darkConcrete), -W / 2 - 34, 0, 12));       // the linked block
for (let y = 4; y < 32; y += 3.4) g.add(box(27, 1.4, 21, m(P.stone), -W / 2 - 34, y, 12));
g.add(box(26, 4, 7, m(P.stone), -W / 2 - 16, 12, 12));               // bridge link

await exportGLB(g, out('centre_point'));
