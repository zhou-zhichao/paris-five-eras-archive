// Generic London railway goods shed, 60 x 20 m, eaves 10 m, hipped slate roof.
// Stock brick with round-headed cart entrances, loading platform and canopy on +z.
// Long axis (the internal track) along x.
import { exportGLB, box, cyl, hipRoof, THREE, P, M, openWall, chimney, tracksX, OUT,
  centreXZ } from './_lib_rail.mjs';

const g = new THREE.Group();
const W = 60, D = 20, H = 7.0;
const bk = M(P.stock), bkd = M(0xa08e6f), st = M(P.dstone), sl = M(P.slate),
  gl = M(P.darkglass), ir = M(P.iron), tim = M(P.timber);

// long walls with round-headed openings
const ops = [];
for (let i = 0; i < 7; i++) ops.push({ cx: -24 + i * 8, y0: 0.2, w: 4.4, h: 2.6, arch: true });
g.add(openWall(W, H, 1.0, bk, ops, 0, 0, D / 2 - 0.5, 8));
const ops2 = [];
for (let i = 0; i < 7; i++) ops2.push({ cx: -24 + i * 8, y0: 3.4, w: 2.6, h: 1.2, arch: true });
g.add(openWall(W, H, 1.0, bk, ops2, 0, 0, -D / 2 + 0.5, 8));
// end walls with the big track archways
for (const sx of [-1, 1]) {
  const w = openWall(D, H, 1.0, bk, [{ cx: 0, y0: 0, w: 6.6, h: 2.4, arch: true }], 0, 0, 0, 8);
  const gr = new THREE.Group(); gr.add(w); gr.rotation.y = Math.PI / 2; gr.position.set(sx * (W / 2 - 0.5), 0, 0);
  g.add(gr);
}

// brick piers between the bays
for (let i = 0; i < 8; i++) for (const sz of [-1, 1])
  g.add(box(1.6, H + 0.6, 1.5, bkd, -28 + i * 8, 0, sz * (D / 2 - 0.4)));

// eaves band + hipped slate roof
g.add(box(W + 1.4, 0.7, D + 1.4, st, 0, H, 0));
g.add(hipRoof(W + 1.4, D + 1.4, 3.4, sl, 0, H + 0.7, 0, 0.55));
// roof lights along the ridge
for (let i = 0; i < 6; i++) g.add(box(5.0, 0.5, 2.2, gl, -22 + i * 9, H + 3.2, 0));
g.add(chimney(1.2, 1.2, 2.0, P.stock, -W / 2 + 3, H + 1.7, -D / 2 + 3, 2));

// loading platform + light canopy on the +z (cart yard) side
g.add(box(W, 1.1, 4.0, M(P.platform), 0, 0, D / 2 + 2.5));
for (let i = 0; i < 9; i++) g.add(cyl(0.16, 0.2, 3.8, ir, -26 + i * 6.5, 1.1, D / 2 + 4.0, 6));
g.add(box(W, 0.4, 4.6, tim, 0, 4.9, D / 2 + 3.8));
// track through the shed
g.add(tracksX(W + 14, 4.4, 1, 0, 0.05, -3.5));

await exportGLB(centreXZ(g), OUT + 'goods_shed.glb');
