// SIS Building, Vauxhall Cross (1994, Terry Farrell) - the cream-and-green
// ziggurat: two flanking stepped towers with a lower central range, deep terraces
// and dark green glazing, facing the river on +z.
// Convention: metres, ground y=0, footprint centred on origin, long axis x,
//             front (river) +z.
import { THREE, group, m, P, box, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const CR = m(P.stone), GR = m(P.greenGlass), DG = m(P.copper);

// a stepped stack: each tier smaller than the one below, with a green glazed band
function ziggurat(x, z, w0, d0, tiers, tierH, shrinkW, shrinkD) {
  let w = w0, d = d0, y = 0;
  for (let i = 0; i < tiers; i++) {
    g.add(box(w, tierH, d, CR, x, y, z));
    g.add(box(w - 4, tierH * 0.55, d + 0.8, GR, x, y + tierH * 0.2, z));
    g.add(box(w + 0.8, tierH * 0.55, d - 4, GR, x, y + tierH * 0.2, z));
    g.add(box(w + 1.6, 1.0, d + 1.6, DG, x, y + tierH, z));      // terrace parapet
    y += tierH; w -= shrinkW; d -= shrinkD;
  }
  return y;
}

// the two flanking towers
for (const sx of [-1, 1]) ziggurat(sx * 44, 0, 40, 52, 6, 8.5, 5.5, 6.5);
// the lower central range, set back
ziggurat(0, -8, 52, 40, 4, 8.5, 6, 5);
// the drum-topped corner turrets
for (const sx of [-1, 1]) {
  g.add(box(14, 62, 14, CR, sx * 44, 0, 26));
  g.add(box(16, 3, 16, DG, sx * 44, 62, 26));
}
// river frontage terraces and the boat pier
g.add(box(150, 6, 16, CR, 0, 0, 34));
g.add(box(160, 1.2, 20, DG, 0, 6, 34));
g.add(box(180, 1.0, 110, m(P.darkConcrete), 0, 0, -4));

await exportGLB(g, out('sis_building'));
