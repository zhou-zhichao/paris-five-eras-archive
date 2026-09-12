// The Eleanor Cross at Charing, 1291-94 - the grandest of the twelve crosses
// Edward I raised where Queen Eleanor's body rested; destroyed 1647.
// CONVENTION: metres, ground y=0, centred on the origin.  Octagonal, so every
// face is a "front"; the statue stage faces all eight ways.
//
// True dimensions: about 21 m high on a stepped octagonal base ~7 m across,
// three diminishing stages of Caen stone with statues of the queen.
import {
  exportGLB, out, M, mat, box, cyl, cone, dome, lathe, group, THREE, pinnacle, profileWall,
} from './_lib_london.mjs';

const g = new THREE.Group();
const stone = M.pale, trim = M.portland, dark = M.dark, gold = M.gold;

// ---- stepped octagonal base
for (let i = 0; i < 3; i++) g.add(cyl(4.4 - i * 0.7, 4.7 - i * 0.7, 0.42, trim, 0, i * 0.42, 0, 8));
let y = 1.26;
g.add(cyl(2.9, 3.1, 1.1, stone, 0, y, 0, 8)); y += 1.1;

// ---- stage 1: solid octagon with blind arcading and angle buttresses
{
  const h = 6.0, r = 2.85;
  g.add(cyl(r, r, h, stone, 0, y, 0, 8));
  for (let i = 0; i < 8; i++) {
    const a = i * Math.PI / 4;                                   // buttresses on the angles
    const b = box(0.7, h + 0.8, 0.9, trim, (r + 0.15) * Math.cos(a), y, (r + 0.15) * Math.sin(a));
    b.rotation.y = Math.PI / 2 - a; g.add(b);
    const w = box(1.5, 3.4, 0.35, dark, (r - 0.05) * Math.cos(a + Math.PI / 8), y + 1.4, (r - 0.05) * Math.sin(a + Math.PI / 8));
    w.rotation.y = Math.PI / 2 - (a + Math.PI / 8); g.add(w);
  }
  g.add(cyl(r + 0.45, r + 0.45, 0.55, trim, 0, y + h, 0, 8));
  y += h + 0.55;
}

// ---- stage 2: open canopied stage with the statues of Queen Eleanor
{
  const h = 5.4, r = 2.35;
  g.add(cyl(r * 0.72, r * 0.72, h, stone, 0, y, 0, 8));           // the core
  for (let i = 0; i < 8; i++) {
    const a = i * Math.PI / 4;
    const cx = r * Math.cos(a), cz = r * Math.sin(a);
    g.add(cyl(0.3, 0.34, h, trim, cx, y, cz, 8));                 // shafts between the niches
    // statue niche between each pair of shafts
    const na = a + Math.PI / 8, nx = (r - 0.5) * Math.cos(na), nz = (r - 0.5) * Math.sin(na);
    const nb = box(1.25, h * 0.72, 0.5, dark, nx, y + 0.5, nz);
    nb.rotation.y = Math.PI / 2 - na; g.add(nb);
    g.add(cyl(0.28, 0.34, h * 0.6, stone, nx * 0.94, y + 0.6, nz * 0.94, 6));   // the figure
    g.add(dome(0.3, stone, nx * 0.94, y + 0.6 + h * 0.6, nz * 0.94, 6, 1.2));
    // crocketed gable over each niche
    const gb = profileWall([[-0.85, 0], [0.85, 0], [0, 1.5]], 0.35, trim, nx, y + h * 0.78, nz, Math.PI / 2 - na);
    g.add(gb);
  }
  g.add(cyl(r + 0.5, r + 0.5, 0.5, trim, 0, y + h, 0, 8));
  for (let i = 0; i < 8; i++) {
    const a = i * Math.PI / 4;
    g.add(pinnacle(0.34, 2.1, trim, (r + 0.3) * Math.cos(a), y + h + 0.5, (r + 0.3) * Math.sin(a)));
  }
  y += h + 0.5;
}

// ---- stage 3: a small octagon of traceried panels
{
  const h = 3.4, r = 1.55;
  g.add(cyl(r, r, h, stone, 0, y, 0, 8));
  for (let i = 0; i < 8; i++) {
    const a = i * Math.PI / 4 + Math.PI / 8;
    const w = box(0.8, 2.0, 0.3, dark, (r - 0.05) * Math.cos(a), y + 0.7, (r - 0.05) * Math.sin(a));
    w.rotation.y = Math.PI / 2 - a; g.add(w);
  }
  g.add(cyl(r + 0.35, r + 0.35, 0.4, trim, 0, y + h, 0, 8));
  y += h + 0.4;
}

// ---- crowning pinnacle and cross
g.add(lathe([[1.35, 0], [1.15, 0.9], [0.75, 2.4], [0.38, 3.6], [0.14, 4.4]], stone, 0, y, 0, 8));
g.add(cyl(0.14, 0.16, 0.7, gold, 0, y + 4.4, 0, 6));
g.add(box(0.18, 1.5, 0.18, gold, 0, y + 5.1, 0));
g.add(box(0.85, 0.18, 0.18, gold, 0, y + 6.0, 0));

g.scale.setScalar(21 / 25.2);   // true height ~21 m to the tip of the cross
await exportGLB(g, out('eleanor_cross_charing'));
