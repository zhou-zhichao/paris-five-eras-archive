// St George Wharf Tower / Vauxhall Tower (2014, Broadway Malyan) - 181 m, 50
// storeys. Circular plan ~25 m across, scalloped into petal-shaped bays by full
// height fins, with a wind turbine in the open crown.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, strut, exportGLB, out, bandedCyl } from '../london_lib.mjs';

const g = new THREE.Group();
const R = 12.5, H = 148;

// --- shaft: banded glass drum with a slight taper --------------------------------
g.add(bandedCyl(R, H, P.glass, P.paleGlass, 0, 0, 0, 3.3, 24, 0.32));
// six full-height fins that scallop the plan
for (let i = 0; i < 6; i++) {
  const a = i * Math.PI / 3;
  g.add(cyl(2.6, 2.9, H, m(P.paleGlass), (R - 0.6) * Math.cos(a), 0, (R - 0.6) * Math.sin(a), 10));
}
// central core expressed above the last residential floor
g.add(cyl(R * 0.92, R * 0.96, 6, m(P.alu), 0, H, 0, 24));

// --- open crown with the wind turbine ---------------------------------------------
for (let i = 0; i < 6; i++) {
  const a = i * Math.PI / 3;
  g.add(cyl(1.3, 1.3, 8, m(P.alu), (R - 1.5) * Math.cos(a), H + 6, (R - 1.5) * Math.sin(a), 8));
}
g.add(cyl(R * 0.9, R * 0.9, 1.6, m(P.alu), 0, H + 14, 0, 24));
const nac = cyl(1.2, 1.2, 4, m(P.steel), 0, 0, 0, 8);
nac.rotation.x = Math.PI / 2; nac.position.set(0, H + 20, 0); g.add(nac);
g.add(cyl(1.0, 1.4, 5, m(P.alu), 0, H + 15.6, 0, 10));
for (let b = 0; b < 3; b++) {
  const a = b * 2 * Math.PI / 3;
  g.add(strut([0, H + 20, 0], [0.3, H + 20 + 8 * Math.cos(a), 8 * Math.sin(a)], 0.45, m(P.steel), 4));
}

// podium / riverside base
g.add(cyl(19, 21, 12, m(P.paleGlass), 0, 0, 0, 20));
g.add(box(64, 5, 34, m(P.darkConcrete), 0, 0, 6));

await exportGLB(g, out('st_george_wharf_tower'));
