// One 30 m wrought-iron plate-girder railway bridge span on brick abutments.
// Deck top 7 m, 9 m wide.  Long axis (the track) along x.
import { exportGLB, box, cyl, THREE, P, M, girderX, tracksX, OUT,
  centreXZ } from './_lib_rail.mjs';

const g = new THREE.Group();
const SPAN = 30, DECK = 7.0, W = 9.0, ABUT = 7.0;
const LEN = SPAN + 2 * ABUT;      // 44 m overall

const bk = M(P.stock), bkd = M(0xa08e6f), st = M(P.dstone), ir = M(P.iron);

// brick abutments at both ends, battered slightly
for (const sx of [-1, 1]) {
  const cx = sx * (SPAN / 2 + ABUT / 2);
  g.add(box(ABUT, DECK - 1.6, W + 2.0, bk, cx, 0, 0));
  g.add(box(ABUT + 0.8, 1.0, W + 3.0, st, cx, DECK - 1.6, 0));      // impost band
  g.add(box(ABUT, 1.6, W + 2.0, bkd, cx, DECK - 0.6, 0));
  // wing walls splaying outwards
  for (const sz of [-1, 1])
    g.add(box(ABUT * 1.6, DECK - 2.6, 1.4, bk, cx + sx * ABUT * 0.4, 0, sz * (W / 2 + 2.2)));
}

// the two plate girders
g.add(girderX(SPAN + 1.6, 3.2, W, 0, DECK - 3.4, 0, { stiff: 12 }));
// cross girders / deck plate between them
g.add(box(SPAN, 0.5, W - 1.6, ir, 0, DECK - 1.0, 0));
for (let i = 0; i <= 10; i++) g.add(box(0.4, 0.7, W - 1.6, M(0x4c4f54), -SPAN / 2 + SPAN * i / 10, DECK - 1.7, 0));

// cross bracing between the girders, under the deck
for (let i = 0; i < 10; i++) {
  const x0 = -SPAN / 2 + SPAN * i / 10, x1 = x0 + SPAN / 10;
  for (const s2 of [-1, 1]) {
    const b = box(Math.hypot(SPAN / 10, W - 3), 0.35, 0.35, M(0x4c4f54), (x0 + x1) / 2, DECK - 3.9, 0);
    b.rotation.y = s2 * Math.atan2(W - 3, SPAN / 10);
    g.add(b);
  }
}
// rivet lines along the flanges
for (const sz of [-1, 1]) for (let i = 0; i < 26; i++)
  g.add(box(0.35, 0.35, 0.35, M(0x2f3134), -SPAN / 2 + SPAN * (i + 0.5) / 26, DECK - 1.4, sz * (W / 2 + 0.05)));
// track on the deck, on transverse timber sleepers
g.add(tracksX(LEN, 4.6, 1, 0, DECK, 0));
for (let i = 0; i < 26; i++) g.add(box(0.3, 0.22, 3.4, M(0x5a4a38), -LEN / 2 + LEN * (i + 0.5) / 26, DECK - 0.2, 0));
// safety refuges on the parapet line
for (const sz of [-1, 1]) {
  g.add(box(SPAN, 1.3, 0.35, M(0x4c4f54), 0, DECK - 0.9, sz * (W / 2 - 0.1)));
  for (let i = 0; i < 12; i++) g.add(box(0.2, 1.3, 0.5, M(0x4c4f54), -SPAN / 2 + SPAN * (i + 0.5) / 12, DECK - 0.9, sz * (W / 2 - 0.1)));
}
// bearings
for (const sx of [-1, 1]) for (const sz of [-1, 1])
  g.add(cyl(0.6, 0.7, 0.8, st, sx * SPAN / 2, DECK - 4.2, sz * (W / 2 - 0.5), 8));

await exportGLB(centreXZ(g), OUT + 'rail_bridge_girder_unit.glb');
