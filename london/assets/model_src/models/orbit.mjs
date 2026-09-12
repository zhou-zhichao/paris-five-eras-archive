// ArcelorMittal Orbit, Olympic Park (2012, Anish Kapoor / Cecil Balmond) - 114.5 m
// of looping red tubular steel wrapped round a core, with a two-level observation
// deck at ~76-80 m and the spiral slide added in 2016.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, cyl, strut, tube, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const RED = m(P.red), STL = m(P.alu);
const H = 114.5, DECK = 76;

// --- central core: lift shaft + stair, dark, mostly hidden by the tangle ---------
g.add(cyl(2.6, 3.2, DECK + 6, STL, 0, 0, 0, 10));

// --- eight looping arcs: ground anchor -> out and up -> over the top -> down -----
for (let k = 0; k < 8; k++) {
  const a0 = k * 2 * Math.PI / 8;
  const a1 = a0 + 2.7;                     // the far anchor, most of the way round
  const P0 = a => [34 * Math.cos(a), 0, 34 * Math.sin(a)];
  const pts = [];
  const N = 7;
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    const a = a0 + (a1 - a0) * t;
    // radius swings out then in; height rises to the deck and loops above it
    const r = 34 - 22 * Math.sin(Math.PI * t) + 12 * Math.sin(2 * Math.PI * t + k);
    const y = DECK * Math.sin(Math.PI * t * 0.85) + 16 * Math.sin(3 * Math.PI * t + k * 0.7);
    pts.push([r * Math.cos(a), Math.max(0.5, y), r * Math.sin(a)]);
  }
  pts[0] = P0(a0); pts[N] = P0(a1);
  g.add(tube(pts, 1.15, RED, 40, 6));
}

// --- outer legs / tripod anchors ---------------------------------------------------
for (let k = 0; k < 8; k++) {
  const a = k * 2 * Math.PI / 8;
  g.add(strut([34 * Math.cos(a), 0, 34 * Math.sin(a)], [8 * Math.cos(a), 34, 8 * Math.sin(a)], 1.0, RED, 6));
  g.add(cyl(2.4, 3.0, 2.5, m(P.darkConcrete), 34 * Math.cos(a), 0, 34 * Math.sin(a), 8));
}

// --- observation deck: two round platforms with a canopy --------------------------
g.add(cyl(11, 11, 3.0, STL, 0, DECK, 0, 20));
g.add(cyl(11.5, 11.5, 0.6, RED, 0, DECK + 3.0, 0, 20));
g.add(cyl(10, 10, 3.0, m(P.paleGlass), 0, DECK + 3.6, 0, 20));
g.add(cyl(12, 12, 0.8, RED, 0, DECK + 6.6, 0, 20));

// --- the tangle crown above the deck, up to 114.5 m --------------------------------
for (let k = 0; k < 5; k++) {
  const a0 = k * 2 * Math.PI / 5, a1 = a0 + 3.4;
  const pts = [];
  for (let i = 0; i <= 6; i++) {
    const t = i / 6, a = a0 + (a1 - a0) * t;
    const r = 12 - 5 * Math.sin(Math.PI * t);
    pts.push([r * Math.cos(a), DECK + 7 + (H - DECK - 9) * Math.sin(Math.PI * t * 0.9), r * Math.sin(a)]);
  }
  g.add(tube(pts, 0.9, RED, 30, 6));
}
g.add(cyl(0.6, 1.2, 12, RED, 0, H - 12, 0, 8));

// --- the spiral slide winding down the outside ------------------------------------
const slide = [];
for (let i = 0; i <= 20; i++) {
  const t = i / 20, a = t * 5.6;
  slide.push([(16 + 8 * t) * Math.cos(a), DECK * (1 - t) + 2, (16 + 8 * t) * Math.sin(a)]);
}
g.add(tube(slide, 1.0, STL, 60, 6));

await exportGLB(g, out('orbit'));
