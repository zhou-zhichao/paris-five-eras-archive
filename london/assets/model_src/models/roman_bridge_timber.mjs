// The Roman bridge over the Thames at Londinium (c. AD 50-60, rebuilt later):
// a timber pile-and-trestle bridge on the line of the later London Bridge, with
// a masonry-faced abutment and a removable centre span.
// CONVENTION: metres, WATER SURFACE AT y=0, centred on the origin, LONG axis
// along x (-x = the Southwark bank, +x = the City bank).  "Front" = +z is the
// downstream side.
//
// True dimensions: about 300 m from bank to bank, a 6 m plank deck some 5 m above
// the water, trestles of driven oak piles every ~8 m.
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, group, THREE, crenel,
} from './_lib_london.mjs';

const g = new THREE.Group();
const oak = M.timber, dark = M.darkTimber, plank = mat(0x8a7047);
const rag = M.rag, tileB = M.tile, road = mat(0x8d8574);
const LEN = 300, DECK = 5.0, W = 6.0, PITCH = 8.0;
const N = Math.round(LEN / PITCH);              // 38 trestles

// ---------------------------------------------------------------- trestles
for (let i = 0; i <= N; i++) {
  const x = -LEN / 2 + i * PITCH;
  const isBig = i % 5 === 0;
  const r = isBig ? 0.42 : 0.34;
  // four raking piles per trestle
  for (const sz of [-1, 1]) for (const o of [0, 1]) {
    const zTop = sz * (W / 2 - 0.6 - o * 0.0);
    const zBot = sz * (W / 2 + 1.3);
    const rake = Math.atan2(zBot - zTop, DECK + 2.4);
    const p = cyl(r, r * 1.15, DECK + 3.2, oak, 0, 0, 0, 6);
    p.rotation.x = -rake;
    p.position.set(x + (o ? 0.55 : -0.55), (DECK - 0.7) / 2 - 1.2, (zTop + zBot) / 2);
    g.add(p);
  }
  // cross bracing
  for (const sgn of [-1, 1]) {
    const b = box(0.28, 0.28, W + 2.4, oak, 0, 0, 0);
    b.rotation.x = sgn * 0.42;
    b.position.set(x, DECK * 0.45, 0);
    g.add(b);
  }
  // horizontal waling and the capping beam under the deck
  g.add(box(0.3, 0.3, W + 2.8, oak, x, DECK * 0.62, 0));
  g.add(box(1.5, 0.55, W + 1.8, dark, x, DECK - 0.85, 0));
  // an ice/debris breaker on the upstream side of the big trestles
  if (isBig) {
    const c = cyl(0.9, 1.1, DECK + 1.2, oak, x - 1.6, -1.0, 0, 4);
    c.rotation.y = Math.PI / 4; g.add(c);
  }
}

// ---------------------------------------------------------------- deck
g.add(box(LEN, 0.3, W, plank, 0, DECK - 0.3, 0));
g.add(box(LEN, 0.25, W - 1.2, road, 0, DECK, 0));
// longitudinal bearers under the planking
for (const o of [-2.2, 0, 2.2]) g.add(box(LEN, 0.35, 0.45, oak, 0, DECK - 0.65, o));
// handrails: posts every 4 m with two rails
for (const s of [-1, 1]) {
  for (let i = 0; i * 4 <= LEN; i++)
    g.add(box(0.22, 1.15, 0.22, dark, -LEN / 2 + i * 4, DECK, s * (W / 2 - 0.2)));
  g.add(box(LEN, 0.18, 0.28, oak, 0, DECK + 0.95, s * (W / 2 - 0.2)));
  g.add(box(LEN, 0.16, 0.24, oak, 0, DECK + 0.5, s * (W / 2 - 0.2)));
}
// the removable centre span, marked by a heavier pair of trestles and a gap in the rail
for (const s of [-1, 1]) {
  g.add(box(1.2, 2.6, 1.2, oak, s * 5.0, DECK, W / 2 - 0.2));
  g.add(box(1.2, 2.6, 1.2, oak, s * 5.0, DECK, -W / 2 + 0.2));
  g.add(box(1.4, 0.5, W + 1.0, dark, s * 5.0, DECK + 2.6, 0));
}

// ---------------------------------------------------------------- abutments and approach ramps
for (const s of [-1, 1]) {
  const ax = s * (LEN / 2 + 9);
  g.add(box(20, DECK + 1.2, W + 9, rag, ax, -1.2, 0));
  for (let i = 1; i * 1.15 < DECK + 1.2; i++) g.add(box(20.2, 0.22, W + 9.2, tileB, ax, -1.2 + i * 1.15, 0));
  g.add(box(20, 0.3, W + 2.0, road, ax, DECK, 0));
  // the approach causeway stepping down to the bank
  for (let k = 0; k < 4; k++) {
    const h = DECK * (1 - (k + 0.5) / 4.4) + 0.6;
    const cx = ax + s * (10 + 6.5 + k * 7);
    g.add(box(7.2, h, W + 4.0, rag, cx, 0, 0));
    for (let i = 1; i * 1.15 < h; i++) g.add(box(7.3, 0.2, W + 4.1, tileB, cx, i * 1.15, 0));
    g.add(box(7.2, 0.3, W + 1.0, road, cx, h, 0));
  }
}

await exportGLB(g, out('roman_bridge_timber'));
