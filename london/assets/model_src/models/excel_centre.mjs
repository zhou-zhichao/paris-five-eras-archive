// ExCeL London, Royal Victoria Dock (2000, ext. 2010) - a 500 x 150 m exhibition
// shed: two ranks of halls either side of a central boulevard, under a stepped
// roof punctuated by the row of curved "pods".
// Convention: metres, ground y=0, footprint centred on origin, long axis x, front +z.
import { THREE, group, m, P, box, cyl, exportGLB, out, loft, roundRect } from '../london_lib.mjs';

const g = new THREE.Group();
const AL = m(P.alu), STL = m(P.steel), GL = m(P.paleGlass), DC = m(P.darkConcrete), BL = m(P.glass);

// --- the two hall ranks -------------------------------------------------------------
for (const sz of [-1, 1]) {
  const z = sz * 46;
  g.add(box(500, 18, 58, AL, 0, 0, z));
  for (let y = 4; y < 18; y += 4.5) g.add(box(501, 1.2, 59, STL, 0, y, z));
  // stepped roof: a raised centre band
  g.add(box(490, 4, 44, STL, 0, 18, z));
  g.add(box(470, 3, 30, AL, 0, 22, z));
}

// --- the central boulevard, glazed and lower ---------------------------------------
g.add(box(500, 14, 34, GL, 0, 0, 0));
g.add(loft([{ y: 14, pts: roundRect(502, 36, 8, 4) }, { y: 20, pts: roundRect(490, 14, 6, 4) }], STL));

// --- the row of curved roof pods over the boulevard --------------------------------
for (let i = 0; i < 7; i++) {
  const x = -210 + i * 70;
  const pod = cyl(11, 11, 30, BL, 0, 0, 0, 14);
  pod.rotation.z = Math.PI / 2; pod.scale.set(0.85, 1, 1); pod.position.set(x, 22.5, 0);
  g.add(pod);
  g.add(box(30, 1.4, 32, STL, x, 21, 0));
}

// --- entrance drums at both ends ----------------------------------------------------
for (const sx of [-1, 1]) {
  g.add(cyl(22, 22, 20, GL, sx * 256, 0, 0, 20));
  g.add(cyl(24, 24, 1.6, STL, sx * 256, 20, 0, 20));
}

// --- dockside apron and water --------------------------------------------------------
g.add(box(600, 1.0, 200, DC, 0, 0, 0));
g.add(box(620, 0.6, 90, m(P.glass), 0, 0, 152));       // Royal Victoria Dock

await exportGLB(g, out('excel_centre'));
