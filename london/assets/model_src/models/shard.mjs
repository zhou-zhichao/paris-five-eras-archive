// The Shard, London Bridge (2012) - 309.6 m, 87 storeys, Renzo Piano.
// Eight sloping glass "shards" that taper but never meet: the crown is open and jagged.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front (river/north) +z.
import { THREE, group, m, P, loft, box, exportGLB, out, scalePoly } from '../london_lib.mjs';

const g = new THREE.Group();

// --- base plan: irregular octagon ~ 62 x 56 m -------------------------------------
const R = [31, 26, 29.5, 24, 31, 25.5, 28.5, 26.5];      // radius per facade corner
const A0 = Math.PI / 8;
const basePts = R.map((r, i) => {
  const a = A0 + i * Math.PI / 4;
  return [r * Math.cos(a), r * 0.90 * Math.sin(a)];
});

// linear taper: scale(y) = 1 - y/H0  (facades are straight planes)
const H0 = 342;
const planAt = y => scalePoly(basePts, 1 - y / H0);

// --- solid core: full mass up to 235 m, slightly inset from the fins ---------------
const coreTop = 236;
g.add(loft([
  { y: 0,        pts: scalePoly(planAt(0), 0.93) },
  { y: coreTop,  pts: scalePoly(planAt(coreTop), 0.93) },
], m(P.darkGlass)));

// --- eight shard fins, each ending at its own height => jagged open crown ----------
const TOPS = [309.6, 292, 303, 281, 306, 286, 298, 289];
const T = 3.2;                                    // fin thickness inward
for (let i = 0; i < 8; i++) {
  const top = TOPS[i];
  const sec = y => {
    const p = planAt(y);
    const a = p[i], b = p[(i + 1) % 8];
    // inward normal (towards origin) offsets
    const ai = [a[0] * (1 - T / Math.hypot(a[0], a[1])), a[1] * (1 - T / Math.hypot(a[0], a[1]))];
    const bi = [b[0] * (1 - T / Math.hypot(b[0], b[1])), b[1] * (1 - T / Math.hypot(b[0], b[1]))];
    return [a, b, bi, ai];
  };
  const shade = (i % 2) ? P.glass : P.paleGlass;
  g.add(loft([{ y: 0, pts: sec(0) }, { y: coreTop, pts: sec(coreTop) }, { y: top, pts: sec(top) }], m(shade)));
}

// --- horizontal banding on the lower shaft (floor plates read at map scale) --------
for (let y = 12; y < 230; y += 14) {
  const p = scalePoly(planAt(y), 1.012);
  g.add(loft([{ y, pts: p }, { y: y + 1.4, pts: p }], m(P.alu), 0, 0, 0, false, false));
}

// --- railway-station podium / base at the foot (London Bridge concourse) -----------
g.add(box(74, 9, 46, m(P.darkGlass), 0, 0, -4));

await exportGLB(g, out('shard'));
