// Battersea Power Station, Giles Gilbert Scott / Halliday & Agate.
// Station A (2 chimneys, complete 1935) and the full four-chimney building (Station B, 1955).
// Orientation: long axis along X, river (Thames) side faces +Z.  Ground y=0.
// Full building ~160 m (along the river) x 170 m; brick with 4 white concrete chimneys 103 m.
// Each variant is centred on its OWN footprint (so battersea_a stands on the A-station site).
// run: node models/battersea.mjs   -> battersea_a.glb + battersea_b.glb
import { exportGLB, box, cyl, cone, lathe, gableRoof, THREE, P, M, OUT } from './_lib_wren_edwardian.mjs';

const bk = M(0x9a5a48), bkd = M(0x814a3c), wh = M(P.white), pale = M(P.pale),
  glass = M(P.glass), dark = M(0x33383d), slate = M(P.slate);

const CH_TOP = 103;          // chimney tip
const BASE_H = 58;           // brick chimney-base tower
const HALL_H = 32;           // outer wing / turbine hall
const BOIL_H = 47;           // central boiler house

// half = true -> only the +? one half (Station A): x from -HALFL/2 .. +HALFL/2 with 2 chimneys
function build(full) {
  const g = new THREE.Group();
  const L = full ? 160 : 82;              // length along x
  const D = 108;                          // depth along z (river front at +z)
  const cx = [];                          // chimney x positions
  if (full) { cx.push(-64, 64); } else { cx.push(-24, 24); }

  // ---- plinth / retaining wall to the river
  g.add(box(L + 10, 4, D + 12, bkd, 0, 0, 0));
  g.add(box(L + 10, 2.0, 8, pale, 0, 4, D / 2 + 8));      // river wharf edge

  // ---- outer wings (turbine hall + wash house)
  for (const zs of [1, -1]) {
    g.add(box(L, HALL_H, 30, bk, 0, 4, zs * 37));
    g.add(box(L + 2, 2.2, 32, pale, 0, 4 + HALL_H, zs * 37));   // stone coping
    g.add(box(L - 6, 1.0, 26, slate, 0, 6.2 + HALL_H, zs * 37));
  }
  // ---- central boiler house (taller)
  g.add(box(L, BOIL_H, 42, bk, 0, 4, 0));
  g.add(box(L + 2, 2.4, 44, pale, 0, 4 + BOIL_H, 0));
  g.add(box(L - 8, 1.2, 36, slate, 0, 6.4 + BOIL_H, 0));

  // ---- vertical brick fluting (the fluted pilaster strips) on the long faces
  const nf = Math.round(L / 6.5);
  for (let i = 0; i <= nf; i++) {
    const x = -L / 2 + i * L / nf;
    for (const zs of [1, -1]) {
      g.add(box(2.2, HALL_H, 1.6, bkd, x, 4, zs * 52.3));
      g.add(box(2.2, BOIL_H, 1.6, bkd, x, 4, zs * 21.3));
    }
  }
  // glazing bands between the flutes
  for (const zs of [1, -1]) {
    g.add(box(L - 8, 14, 0.8, glass, 0, 12, zs * 52.2));
    g.add(box(L - 8, 8, 0.8, glass, 0, 30, zs * 52.2));
    g.add(box(L - 14, 18, 0.8, glass, 0, 16, zs * 21.2));
  }
  // end walls fluting
  for (const sx of [1, -1]) {
    for (let i = 0; i < 9; i++) {
      const z = -50 + i * 12.5;
      g.add(box(1.6, Math.abs(z) < 22 ? BOIL_H : HALL_H, 2.2, bkd, sx * (L / 2 + 0.8), 4, z));
    }
  }

  // ---- chimney base towers + white concrete chimneys
  for (const x of cx) for (const zs of [1, -1]) {
    const z = zs * 44;
    g.add(box(23, BASE_H, 23, bk, x, 4, z));               // brick base tower
    g.add(box(24.5, 2.2, 24.5, pale, x, 4 + BASE_H, z));
    // stepped brick top
    g.add(box(19, 5, 19, bk, x, 6.2 + BASE_H, z));
    g.add(box(20, 1.6, 20, pale, x, 11.2 + BASE_H, z));
    // vertical flutes on the base tower
    for (let i = 0; i < 4; i++) for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
      g.add(box(dx ? 1.4 : 3.0, BASE_H, dz ? 1.4 : 3.0, bkd,
        x + dx * 11.9 + (dx ? 0 : (i - 1.5) * 5.4), 4, z + dz * 11.9 + (dz ? 0 : (i - 1.5) * 5.4)));
    // the chimney
    const y0 = 12.8 + BASE_H;
    g.add(cyl(4.3, 5.6, CH_TOP - y0 - 2.4, wh, x, y0, z, 16));
    g.add(cyl(4.9, 4.3, 1.6, wh, x, CH_TOP - 2.4, z, 16));   // flared cap
    g.add(cyl(4.6, 4.9, 0.8, pale, x, CH_TOP - 0.8, z, 16));
  }
  return g;
}

await exportGLB(build(false), OUT + 'battersea_a.glb');
await exportGLB(build(true), OUT + 'battersea_b.glb');
