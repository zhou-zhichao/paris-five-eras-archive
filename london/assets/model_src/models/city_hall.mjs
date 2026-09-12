// City Hall, More London (2002, Foster + Partners) - the 45 m glass "egg", ten
// storeys, leaning towards the river (+z) so the upper floors shade the lower ones.
// Convention: metres, ground y=0, footprint centred on origin, long axis x,
//             front (river) +z.
import { THREE, group, m, P, box, exportGLB, out, loft, ellipse } from '../london_lib.mjs';

const g = new THREE.Group();
const H = 45;

// radius swells to a maximum around a third of the way up, then pinches to the top;
// the section centre slides +z with height, which produces the lean and the overhang.
// [t, radius, centre-z] - a bulbous egg whose centre slides +z as it rises
const PROF = [[0, 15.0, 0], [0.15, 19.5, 1.4], [0.30, 22.0, 3.4], [0.45, 22.6, 5.6],
              [0.60, 21.6, 7.6], [0.75, 19.2, 9.3], [0.90, 15.8, 10.7], [1.0, 12.0, 11.5]];
function sec(y) {
  const t = y / H;
  let r = 12, cz = 11.5;
  for (let i = 0; i < PROF.length - 1; i++) {
    const [t0, r0, z0] = PROF[i], [t1, r1, z1] = PROF[i + 1];
    if (t <= t1) { const u = (t - t0) / (t1 - t0); r = r0 + (r1 - r0) * u; cz = z0 + (z1 - z0) * u; break; }
  }
  return ellipse(r, r * 0.94, 24, 0, cz);
}
const secs = [];
for (let i = 0; i <= 14; i++) { const y = H * i / 14; secs.push({ y, pts: sec(y) }); }
g.add(loft(secs, m(P.glass)));

// glazed floor bands: the stepped, shingled skin
for (let i = 0; i < 13; i++) {
  const y = H * (i + 0.82) / 14;
  const p = sec(y).map(([x, z]) => [x * 1.03, z * 1.03]);
  g.add(loft([{ y, pts: p }, { y: y + 0.9, pts: p }], m(P.paleGlass), 0, 0, 0, false, false));
}
// the roof-top "London's Living Room" gallery
g.add(loft([{ y: H, pts: sec(H).map(([x, z]) => [x * 0.85, z * 0.85]) },
            { y: H + 2.5, pts: sec(H).map(([x, z]) => [x * 0.6, z * 0.6]) }], m(P.alu)));

// the sunken amphitheatre / plaza
g.add(box(70, 1.0, 62, m(P.darkConcrete), 0, 0, 4));

await exportGLB(g, out('city_hall'));
