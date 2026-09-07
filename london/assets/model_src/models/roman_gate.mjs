// A gate of the Roman city wall of Londinium (c. AD 200) - the type of Newgate
// and Aldgate: a double carriageway arch between two projecting rectangular
// towers, in a 40 m stretch of ragstone wall with red tile bonding courses.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x (the run of the wall).  "Front" = +z is OUTSIDE the city, the side the
// towers project towards.
//
// True dimensions: wall ~6 m to the walkway with a crenellated parapet on a
// plinth, gate towers ~9 m, carriageways ~3.6 m wide.
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, hipRoof, group, THREE,
  wall, archPath, crenel, crenelRing,
} from './_lib_london.mjs';

const g = new THREE.Group();
const rag = M.rag, tileB = M.tile, dark = M.dark, plaster = M.whitewash, timb = M.timber;
const T = 2.6;                       // wall thickness
const H = 6.0;                       // to the walkway
const LEN = 40;

// bonding courses of red tile every ~1 m, on both faces of a wall run
function bonded(w, h, d, x, y, z, alongX = true) {
  const gg = new THREE.Group();
  gg.add(box(w, h, d, rag, 0, 0, 0));
  for (let i = 1; i * 1.15 < h; i++) gg.add(box(w + 0.12, 0.22, d + 0.12, tileB, 0, i * 1.15, 0));
  gg.position.set(x, y, z);
  return gg;
}

// ---------------------------------------------------------------- wall runs either side
for (const s of [-1, 1]) {
  const runLen = (LEN - 14) / 2;
  const cx = s * (7 + runLen / 2);
  g.add(box(runLen, 1.0, T + 1.6, rag, cx, 0, 0));                   // plinth
  g.add(bonded(runLen, H - 1.0, T, cx, 1.0, 0));
  g.add(box(runLen, 0.4, T + 0.6, rag, cx, H, 0));                   // walkway
  g.add(box(runLen, 0.5, 0.7, rag, cx, H + 0.4, -T / 2));            // inner kerb
  g.add(crenel(runLen, 0.8, rag, cx, H + 0.4, T / 2, true, 1.5, 1.5, 1.1));
  // earth rampart banked against the inside face (-z)
  const bank = box(runLen, 0.6, 5.0, M.grass, 0, 0, 0);
  bank.rotation.x = -0.42; bank.position.set(cx, 2.2, -T / 2 - 2.2); g.add(bank);
}

// ---------------------------------------------------------------- the double gate
{
  const holes = [archPath(-3.1, 3.6, 0, 3.2, 1.9, 0, 8), archPath(3.1, 3.6, 0, 3.2, 1.9, 0, 8)];
  g.add(box(14, 1.0, T + 3.4, rag, 0, 0, 0));
  g.add(wall(14, 9.5, T + 2.6, rag, holes, 0, 1.0, 0));
  for (let i = 1; i * 1.15 < 9.5; i++) {                             // tile courses on the gate block
    for (const s of [-1, 1]) g.add(box(14.1, 0.22, 0.3, tileB, 0, 1.0 + i * 1.15, s * (T + 2.6) / 2));
  }
  // voussoir rings of red tile round each arch
  for (const cx of [-3.1, 3.1]) for (const s of [-1, 1]) {
    for (let i = 0; i <= 8; i++) {
      const a = Math.PI * i / 8;
      const b = box(0.85, 0.45, 0.3, tileB, cx + 2.05 * Math.cos(a), 1.0 + 3.2 + 2.3 * Math.sin(a), s * (T + 2.7) / 2);
      b.rotation.z = a - Math.PI / 2; g.add(b);
    }
  }
  g.add(box(15, 0.5, T + 3.4, rag, 0, 10.5, 0));
  g.add(crenelRing(15, T + 3.4, 0.8, rag, 0, 11.0, 0, 1.5, 1.5, 1.2));
  // the roadway through the gate
  g.add(box(24, 0.3, 12, mat(0x8d8574), 0, 0, 0));
}

// ---------------------------------------------------------------- the two projecting towers
for (const s of [-1, 1]) {
  const tx = s * 9.5, tz = 3.4;
  g.add(box(6.5, 1.0, 8.5, rag, tx, 0, tz));
  g.add(bonded(6.0, 8.2, 8.0, tx, 1.0, tz));
  for (const f of [0.42, 0.72]) {
    g.add(box(1.0, 1.8, 0.35, dark, tx, 1.0 + 8.2 * f, tz + 4.0));   // arrow slits
    g.add(box(0.35, 1.8, 1.0, dark, tx + s * 3.0, 1.0 + 8.2 * f, tz));
  }
  g.add(box(7.2, 0.6, 9.2, rag, tx, 9.2, tz));
  g.add(crenelRing(7.2, 9.2, 0.8, rag, tx, 9.8, tz, 1.5, 1.5, 1.2));
}

await exportGLB(g, out('roman_gate'));
