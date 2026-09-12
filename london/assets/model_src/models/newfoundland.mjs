// Newfoundland Quay, Canary Wharf (2020, Horden Cherry Lee) - 220 m, 58 storeys.
// Slim residential tower inside a bold white steel diagrid exoskeleton; the plan is
// a rounded rectangle, pinched at the base and the top.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, strut, exportGLB, out, loft, roundRect } from '../london_lib.mjs';

const g = new THREE.Group();
const H = 220;

// half-widths: pinched at both ends, widest around mid height
const sAt = y => 0.80 + 0.20 * Math.sin(Math.PI * Math.pow(y / H, 0.92));
const plan = y => roundRect(31 * sAt(y), 25 * sAt(y), 5, 3);

const secs = [];
for (let i = 0; i <= 12; i++) { const y = H * i / 12; secs.push({ y, pts: plan(y) }); }
g.add(loft(secs, m(P.glass)));
for (let y = 4; y < H - 2; y += 6.2) {
  const p = plan(y).map(([x, z]) => [x * 1.02, z * 1.02]);
  g.add(loft([{ y, pts: p }, { y: y + 1.0, pts: p }], m(P.paleGlass), 0, 0, 0, false, false));
}

// --- white diagrid exoskeleton: a diamond lattice on all four faces ---------------
const NODE = 11, ST = H / NODE;
const half = y => [15.5 * sAt(y) + 1.4, 12.5 * sAt(y) + 1.4];
for (let i = 0; i < NODE; i++) {
  const ya = i * ST, yb = (i + 1) * ST;
  const [ax, az] = half(ya), [bx, bz] = half(yb);
  // the four corners of the node ring at each level
  const cA = [[-ax, -az], [ax, -az], [ax, az], [-ax, az]];
  const cB = [[-bx, -bz], [bx, -bz], [bx, bz], [-bx, bz]];
  const mA = cA.map((p, k) => [(p[0] + cA[(k + 1) % 4][0]) / 2, (p[1] + cA[(k + 1) % 4][1]) / 2]);
  const mB = cB.map((p, k) => [(p[0] + cB[(k + 1) % 4][0]) / 2, (p[1] + cB[(k + 1) % 4][1]) / 2]);
  for (let k = 0; k < 4; k++) {
    // two diagonals per face, meeting at the mid points -> diamond pattern
    g.add(strut([cA[k][0], ya, cA[k][1]], [mB[k][0], yb, mB[k][1]], 0.8, m(P.steel), 5));
    g.add(strut([cA[(k + 1) % 4][0], ya, cA[(k + 1) % 4][1]], [mB[k][0], yb, mB[k][1]], 0.8, m(P.steel), 5));
    g.add(strut([mA[k][0], ya, mA[k][1]], [cB[k][0], yb, cB[k][1]], 0.8, m(P.steel), 5));
    g.add(strut([mA[k][0], ya, mA[k][1]], [cB[(k + 1) % 4][0], yb, cB[(k + 1) % 4][1]], 0.8, m(P.steel), 5));
  }
}

// crown + podium
g.add(loft([{ y: H, pts: plan(H) }, { y: H + 6, pts: plan(H).map(([x, z]) => [x * 0.85, z * 0.85]) }], m(P.alu)));
g.add(box(42, 8, 36, m(P.darkConcrete), 0, 0, 0));

await exportGLB(g, out('newfoundland'));
