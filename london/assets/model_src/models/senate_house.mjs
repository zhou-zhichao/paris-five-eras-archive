// Senate House, University of London, Bloomsbury (1937, Charles Holden) - 64 m,
// a Portland stone stepped tower rising from a long north-south wing.
// Convention: metres, ground y=0, footprint centred on origin, long axis x (the
//             long wing), front +z.
import { THREE, group, m, P, box, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const S = m(P.stone), G = m(P.glass), DC = m(P.darkConcrete);

// helper: a stone block with recessed window bands on all four sides
function blk(w, h, d, x, y, z, floorH = 4.0) {
  g.add(box(w, h, d, S, x, y, z));
  for (let yy = y + 2.4; yy < y + h - 1.6; yy += floorH) {
    g.add(box(w - 3.0, 2.2, d + 0.4, G, x, yy, z));
    g.add(box(w + 0.4, 2.2, d - 3.0, G, x, yy, z));
  }
  g.add(box(w + 1.4, 1.2, d + 1.4, S, x, y + h, z));       // cornice
}

// --- the long wing (Library / Chancellor's Hall ranges) ---------------------------
blk(96, 24, 26, 0, 0, 0);
blk(30, 20, 44, -40, 0, -30);
blk(30, 20, 44, 40, 0, -30);
// pavilion end blocks
blk(24, 30, 24, -52, 0, 26);
blk(24, 30, 24, 52, 0, 26);

// --- the stepped tower --------------------------------------------------------------
blk(34, 40, 30, 0, 0, -6);
blk(28, 12, 24, 0, 41.2, -6);
blk(22, 8, 19, 0, 54.4, -6);
g.add(box(15, 2.2, 13, S, 0, 63, -6));
g.add(box(6, 3, 6, S, 0, 65.2, -6));

// forecourt
g.add(box(150, 0.8, 110, DC, 0, 0, 8));

await exportGLB(g, out('senate_house'));
