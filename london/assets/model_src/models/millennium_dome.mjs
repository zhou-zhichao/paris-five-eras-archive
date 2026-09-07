// The Millennium Dome / O2 Arena, Greenwich (1999) - 365 m diameter PTFE tent,
// 52 m high, pierced by 12 yellow 100 m masts with cable stays. Richard Rogers.
// Convention: metres, ground y=0, centred on the origin, long axis x, front +z.
import { THREE, group, m, P, cyl, box, strut, lathe, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const RD = 182.5, RISE = 52;
const SR = (RD * RD + RISE * RISE) / (2 * RISE);      // sphere radius of the cap
const capY = r => Math.sqrt(SR * SR - r * r) - (SR - RISE);

// --- the tent: shallow spherical cap ----------------------------------------------
const prof = [];
for (let i = 0; i <= 14; i++) { const r = RD * (1 - i / 14); prof.push([r, capY(r)]); }
g.add(lathe(prof, m(P.steel), 0, 0, 0, 36));
// radial seam ribs, slightly proud, so the fabric panels read
for (let k = 0; k < 24; k++) {
  const a = k * 2 * Math.PI / 24, c = Math.cos(a), s = Math.sin(a);
  for (let i = 0; i < 8; i++) {
    const r0 = RD * (1 - i / 8), r1 = RD * (1 - (i + 1) / 8);
    g.add(strut([r0 * c, capY(r0) + 0.6, r0 * s], [r1 * c, capY(r1) + 0.6, r1 * s], 0.5, m(P.alu), 4));
  }
}
// perimeter wall + ring beam
g.add(cyl(RD, RD, 9.0, m(P.paleGlass), 0, 0, 0, 48));
g.add(cyl(RD + 1.5, RD + 1.5, 2.0, m(P.alu), 0, 9.0, 0, 48));

// --- 12 yellow masts, 100 m, on a 100 m radius ring, leaning slightly out ---------
const RM = 100, MH = 100;
for (let k = 0; k < 12; k++) {
  const a = k * 2 * Math.PI / 12, c = Math.cos(a), s = Math.sin(a);
  const foot = [RM * c, 0, RM * s], top = [RM * 1.10 * c, MH, RM * 1.10 * s];
  g.add(strut(foot, top, 1.5, m(P.yellow), 8));
  g.add(strut(top, [RD * 0.99 * c, 9.5, RD * 0.99 * s], 0.42, m(P.steel), 4));
  g.add(strut(top, [22 * c, capY(22) + 1, 22 * s], 0.42, m(P.steel), 4));
  for (const dd of [-1, 1]) {
    const a2 = a + dd * 2 * Math.PI / 12, rr = RD * 0.72;
    g.add(strut(top, [rr * Math.cos(a2), capY(rr) + 1, rr * Math.sin(a2)], 0.35, m(P.steel), 4));
  }
}

// --- inner arena drum and the entrance block --------------------------------------
g.add(cyl(56, 58, 20, m(P.alu), 0, 0, 0, 24));
g.add(cyl(52, 52, 2, m(P.darkConcrete), 0, 20, 0, 24));
g.add(box(70, 14, 30, m(P.paleGlass), 0, 0, RD - 22));

await exportGLB(g, out('millennium_dome'));
