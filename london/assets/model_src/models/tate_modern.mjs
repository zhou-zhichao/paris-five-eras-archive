// Tate Modern - Bankside Power Station (1947-63, Giles Gilbert Scott; converted
// 2000 by Herzog & de Meuron) plus the 2016 Switch House / Blavatnik Building.
// Brick, 200 m long along the river, central chimney 99 m; the twisted brick
// pyramid of the Switch House stands behind, on the -z side.
// Convention: metres, ground y=0, footprint centred on origin, long axis x,
//             front (river) +z.
import { THREE, group, m, P, box, exportGLB, out, loft } from '../london_lib.mjs';

const g = new THREE.Group();
const B = m(P.brick), DB = m(P.darkConcrete), GL = m(P.paleGlass);

// --- the power station: tall central boiler house between lower flanking wings ----
g.add(box(200, 35, 36, B, 0, 0, 6));                      // turbine hall block
g.add(box(200, 24, 32, B, 0, 0, -26));                    // switch house range (rear)
g.add(box(200, 20, 12, B, 0, 0, 30));                     // low river frontage
// brick pilaster rhythm on the long facades
for (let i = 0; i <= 26; i++) {
  const x = -100 + i * 200 / 26;
  g.add(box(3.0, 35, 37.2, B, x, 0, 6));
}
// tall vertical window slots
for (let i = 0; i < 26; i++) {
  const x = -98 + i * 200 / 26;
  for (const sz of [1, -1]) g.add(box(3.4, 24, 1.0, m(P.darkGlass), x, 6, 6 + sz * 18.4));
}
// the 2000 "light beam" glazed roof box
g.add(box(160, 6, 24, GL, 0, 35, 6));
g.add(box(164, 1.2, 28, DB, 0, 41, 6));

// --- the central chimney, 99 m ----------------------------------------------------
g.add(loft([{ y: 0, pts: [[-6.5, -6.5], [6.5, -6.5], [6.5, 6.5], [-6.5, 6.5]] },
            { y: 92, pts: [[-4.6, -4.6], [4.6, -4.6], [4.6, 4.6], [-4.6, 4.6]] }], B, 0, 0, 18));
g.add(box(11.5, 5, 11.5, DB, 0, 92, 18));
g.add(box(9.4, 2.5, 9.4, GL, 0, 97, 18));                 // the Swiss Light lantern

// --- Switch House / Blavatnik Building: twisted truncated brick pyramid ----------
function pent(s, rot) {
  const p = [];
  for (let i = 0; i < 5; i++) { const a = rot + i * 2 * Math.PI / 5 + 0.3; p.push([22 * s * Math.cos(a), 22 * s * Math.sin(a)]); }
  return p;
}
const SH = [];
for (let i = 0; i <= 6; i++) {
  const t = i / 6;
  SH.push({ y: 65 * t, pts: pent(1 - 0.42 * t, 0.30 * t) });
}
const sh = loft(SH, B, 78, 0, -62);
g.add(sh);
// perforated brick lattice reads as bands
for (let i = 1; i < 12; i++) {
  const t = i / 12, s = 1 - 0.42 * t;
  const p = pent(s * 1.02, 0.30 * t);
  g.add(loft([{ y: 65 * t, pts: p }, { y: 65 * t + 1.6, pts: p }], DB, 78, 0, -62, false, false));
}

// riverside terrace
g.add(box(240, 1.0, 130, DB, 0, 0, -10));

await exportGLB(g, out('tate_modern'));
