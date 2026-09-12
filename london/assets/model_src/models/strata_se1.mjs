// Strata SE1, Elephant & Castle (2010, BFLS) - 148 m, 43 storeys, with three 9 m
// wind turbines set in scoops cut into the crown. Dark/white striped facade.
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, strut, exportGLB, out, loft, roundRect } from '../london_lib.mjs';

const g = new THREE.Group();
const H = 130;                            // top of the shaft; crown + turbines above

const planAt = y => roundRect(34 - 2 * y / H, 26 - 1.5 * y / H, 9, 6);

// --- shaft: strongly banded dark/pale facade -------------------------------------
g.add(loft([{ y: 0, pts: planAt(0) }, { y: H, pts: planAt(H) }], m(P.darkGlass), 0, 0, 0, false, true));
for (let y = 0; y < H; y += 6.4) {
  const p = planAt(y).map(([x, z]) => [x * 1.012, z * 1.012]);
  g.add(loft([{ y: y + 3.2, pts: p }, { y: y + 6.2, pts: p }], m(P.paleGlass), 0, 0, 0, false, false));
}

// --- crown: three open turbine ducts sitting proud above the shaft ----------------
const CT = 4, YT = H + CT + 6.2;           // turbine axis height
g.add(loft([{ y: H, pts: planAt(H) }, { y: H + CT, pts: planAt(H) }], m(P.alu), 0, 0, 0, false, false));
// side cheeks of the cowl (the scoop walls), leaving the ducts open to the sky
for (const sx of [-1, 1])
  g.add(box(1.6, 14, 15, m(P.alu), sx * 15.3, H + CT - 1, 0));
for (let i = 0; i < 3; i++) {
  const x = (i - 1) * 9.4;
  const ring = cyl(5.6, 5.6, 12, m(P.steel), 0, 0, 0, 16);
  ring.rotation.x = Math.PI / 2; ring.position.set(x, YT, 0); g.add(ring);
  const inner = cyl(4.8, 4.8, 12.6, m(P.darkGlass), 0, 0, 0, 16);
  inner.rotation.x = Math.PI / 2; inner.position.set(x, YT, 0); g.add(inner);
  const hub = cyl(1.0, 1.0, 3.4, m(P.black), 0, 0, 0, 8);
  hub.rotation.x = Math.PI / 2; hub.position.set(x, YT, 0); g.add(hub);
  for (let b = 0; b < 3; b++) {            // blades sweep in the x-y plane
    const a = b * 2 * Math.PI / 3 + i * 0.5;
    g.add(strut([x, YT, 1.2], [x + 4.5 * Math.sin(a), YT + 4.5 * Math.cos(a), 1.2], 0.5, m(P.steel), 4));
  }
}

// podium
g.add(box(46, 9, 38, m(P.darkConcrete), 0, 0, 0));

await exportGLB(g, out('strata_se1'));
