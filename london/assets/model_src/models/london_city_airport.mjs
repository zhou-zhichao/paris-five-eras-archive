// London City Airport, Royal Docks (1987) - the single 150 x 40 m terminal shed
// with a curved roof, the control tower, and the apron beside the dock water.
// Convention: metres, ground y=0, footprint centred on origin, long axis x,
//             front (apron / runway) +z.
import { THREE, group, m, P, box, cyl, exportGLB, out, loft, roundRect } from '../london_lib.mjs';

const g = new THREE.Group();
const GL = m(P.paleGlass), AL = m(P.alu), DC = m(P.darkConcrete), STL = m(P.steel);

// --- terminal shed with a shallow curved roof ------------------------------------
g.add(box(150, 11, 40, GL, 0, 0, 0));
for (let y = 3; y < 11; y += 3.4) g.add(box(151, 1.2, 41, AL, 0, y, 0));
g.add(loft([{ y: 11, pts: roundRect(152, 42, 6, 4) },
            { y: 14.5, pts: roundRect(146, 30, 6, 4) },
            { y: 16.5, pts: roundRect(132, 16, 6, 4) }], STL));
// the departures pier reaching along the apron
g.add(box(110, 7, 14, GL, 20, 0, 34));
g.add(loft([{ y: 7, pts: roundRect(112, 16, 4, 3) }, { y: 9.6, pts: roundRect(104, 6, 3, 3) }], STL, 20, 0, 34));

// --- control tower ------------------------------------------------------------------
g.add(cyl(2.6, 3.6, 24, AL, -88, 0, 6, 12));
g.add(cyl(6.0, 4.6, 6, GL, -88, 24, 6, 12));
g.add(cyl(6.8, 6.8, 1.2, DC, -88, 30, 6, 12));
g.add(cyl(0.35, 0.6, 6, STL, -88, 31.2, 6, 6));

// --- apron, dock water and the DLR station -----------------------------------------
g.add(box(260, 0.8, 120, DC, 0, 0, 30));
g.add(box(300, 0.5, 70, m(P.glass), 0, 0, -70));         // the Royal Albert Dock
g.add(box(46, 9, 12, AL, -40, 0, -30));                  // DLR station
g.add(box(50, 1.2, 15, DC, -40, 9, -30));

await exportGLB(g, out('london_city_airport'));
