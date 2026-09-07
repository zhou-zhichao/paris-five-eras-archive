// Harrods, Knightsbridge — C. W. Stephens' buff terracotta department store, 1901-05.
// Six selling floors behind a heavy modillion cornice, an attic storey, a balustraded
// skyline, and the famous Brompton Road front with its big central dome and the smaller
// domed pavilions stepping away from it.
// Orientation: the ~150 m BROMPTON ROAD front faces +Z, long axis along X.  Ground y=0.
import { exportGLB, box, cyl, cone, lathe, THREE,
  P, M, column, parapet, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const tc = M(0xc9a071),      // Harrods' buff terracotta
  tcd = M(0xb0885c),         // shaded terracotta (pilasters, reveals)
  pale = M(P.pale), dk = M(P.dstone), slate = M(P.slate), lead = M(P.lead),
  dark = M(0x3a352e), glass = M(0x4a6274), gold = M(P.gold), plant = M(0x6f7378);

const W = 150, D = 98;
// storey datums
const Y_PLINTH = 1.0;
const Y_G = Y_PLINTH, H_G = 6.2;          // ground floor shopfront
const Y_U = Y_G + H_G + 0.6;              // 7.8  first of five upper storeys
const SH = 3.6;                            // upper storey height
const Y_CORN = Y_U + 5 * SH;              // 26.3 main cornice springs
const Y_ATT = Y_CORN + 2.0;               // attic storey
const Y_ROOF = Y_ATT + 2.4;               // 30.2 roof deck / balustrade level

// ---------------------------------------------------------------- main block
g.add(box(W + 3, Y_PLINTH, D + 3, dk, 0, 0, 0));
g.add(box(W, Y_ROOF - Y_PLINTH, D, tc, 0, Y_PLINTH, 0));
g.add(box(W + 2.6, 2.0, D + 2.6, pale, 0, Y_CORN, 0));            // heavy modillion cornice
g.add(box(W + 1.4, 0.9, D + 1.4, pale, 0, Y_ROOF - 0.9, 0));      // attic coping
g.add(box(W - 1, 0.8, D - 1, slate, 0, Y_ROOF - 0.8, 0));         // roof deck
g.add(parapet(W + 1.4, D + 1.4, 1.7, pale, 0, Y_ROOF, 0, 1.0));   // balustraded skyline

// the Brompton Road front is broken into bays by giant pilasters flanking each dome;
// only the cornice and attic project, so the window rhythm stays legible.
const BAYX = [[-62, 12.0], [-31, 7.5], [0, 21.0], [31, 7.5], [62, 12.0]];
for (const [bx, bh] of BAYX) {
  for (const sx of [-1, 1]) {
    g.add(box(2.8, Y_CORN - Y_U + 1.2, 1.6, tcd, bx + sx * bh, Y_U - 0.6, D / 2 + 0.8));
    g.add(box(3.4, 1.0, 2.2, pale, bx + sx * bh, Y_CORN - 1.0, D / 2 + 1.1));
  }
  g.add(box(bh * 2 + 6.0, 2.2, 2.4, pale, bx, Y_CORN - 0.1, D / 2 + 1.9));     // projecting cornice
  g.add(box(bh * 2 + 4.0, Y_ROOF - Y_ATT, 1.6, tc, bx, Y_ATT, D / 2 + 1.5));   // attic panel
  g.add(box(bh * 2 + 5.4, 1.0, 2.4, pale, bx, Y_ROOF - 1.0, D / 2 + 1.9));
}

// ---------------------------------------------------------------- ground-floor shopfront
g.add(box(W + 0.6, H_G, D + 0.6, tcd, 0, Y_G, 0));
for (const sz of [1, -1]) g.add(box(W - 8, 3.6, 0.8, glass, 0, Y_G + 1.4, sz * (D / 2 + 0.5)));
for (const sx of [-1, 1]) g.add(box(0.8, 3.6, D - 8, glass, sx * (W / 2 + 0.5), Y_G + 1.4, 0));
g.add(box(W + 4.0, 0.7, D + 4.0, tcd, 0, Y_G + H_G, 0));          // shopfront canopy / band
g.add(box(W + 0.4, 0.5, D + 0.4, pale, 0, Y_G + H_G + 0.7, 0));

// ---------------------------------------------------------------- upper storeys
const NB = 29;                                    // bays along the long fronts
const NBD = 19;                                   // bays along the ends
for (let s = 0; s < 5; s++) {
  const y = Y_U + s * SH + 0.5;
  const wh = s === 4 ? 2.2 : 2.7;                 // top storey a little shorter
  for (let i = 0; i < NB; i++) {
    const x = -W / 2 + 3.4 + i * (W - 6.8) / (NB - 1);
    for (const sz of [1, -1]) g.add(box(2.7, wh, 0.6, dark, x, y, sz * (D / 2 + 0.15)));
  }
  for (let i = 0; i < NBD; i++) {
    const z = -D / 2 + 3.4 + i * (D - 6.8) / (NBD - 1);
    for (const sx of [-1, 1]) g.add(box(0.6, wh, 2.7, dark, sx * (W / 2 + 0.15), y, z));
  }
}
// pilaster strips between the bays
for (let i = 0; i <= NB; i++) {
  const x = -W / 2 + 1.7 + i * (W - 3.4) / NB;
  for (const sz of [1, -1]) g.add(box(1.5, Y_CORN - Y_U + 0.4, 1.0, tcd, x, Y_U - 0.2, sz * (D / 2 + 0.2)));
}
for (let i = 0; i <= NBD; i++) {
  const z = -D / 2 + 1.7 + i * (D - 3.4) / NBD;
  for (const sx of [-1, 1]) g.add(box(1.0, Y_CORN - Y_U + 0.4, 1.5, tcd, sx * (W / 2 + 0.2), Y_U - 0.2, z));
}
// attic storey windows
for (let i = 0; i < NB; i += 1) {
  const x = -W / 2 + 3.4 + i * (W - 6.8) / (NB - 1);
  for (const sz of [1, -1]) g.add(box(2.0, 1.5, 0.5, dark, x, Y_ATT + 0.5, sz * (D / 2 + 0.12)));
}

// ---------------------------------------------------------------- domes
function pavilion(cx, hStage, r, hDrum, hDome, lant, nWin = 12, front = true) {
  const half = r * 1.25;
  const cz = front ? (D / 2 - half - 0.6) : -(D / 2 - half - 0.6);
  const yb = Y_ROOF - 5.0;                       // the stage grows out of the top storeys
  g.add(box(half * 2, hStage + 5.0, half * 2, tc, cx, yb, cz));
  g.add(box(half * 2 + 1.0, 0.7, half * 2 + 1.0, pale, cx, Y_ROOF - 0.4, cz));
  for (let i = 0; i < 4; i++) {                  // a window in each face of the stage
    const a = i / 4 * Math.PI * 2;
    const b = box(half * 1.0, hStage * 0.5, 0.5, dark,
      cx + Math.sin(a) * half, Y_ROOF + hStage * 0.28, cz + Math.cos(a) * half);
    b.rotation.y = a; g.add(b);
  }
  g.add(box(half * 2 + 1.6, 1.0, half * 2 + 1.6, pale, cx, Y_ROOF + hStage, cz));
  const yd = Y_ROOF + hStage + 1.0;
  g.add(cyl(r, r * 1.04, hDrum, tc, cx, yd, cz, 16));
  for (let i = 0; i < nWin; i++) {
    const a = i / nWin * Math.PI * 2;
    const b = box(r * 0.3, hDrum * 0.6, 0.5, dark,
      cx + Math.cos(a) * r * 1.01, yd + hDrum * 0.2, cz + Math.sin(a) * r * 1.01);
    b.rotation.y = -a; g.add(b);
  }
  g.add(cyl(r * 1.15, r * 1.15, 0.7, pale, cx, yd + hDrum, cz, 16));
  const y0 = yd + hDrum + 0.7;
  g.add(lathe([[r * 1.06, 0], [r * 1.0, hDome * 0.22], [r * 0.87, hDome * 0.45],
  [r * 0.66, hDome * 0.66], [r * 0.4, hDome * 0.85], [r * 0.16, hDome * 0.95], [0, hDome]],
    lead, cx, y0, cz, 16));
  g.add(cyl(lant * 0.75, lant, lant * 1.5, pale, cx, y0 + hDome - 0.4, cz, 10));
  g.add(cone(lant * 1.05, lant * 1.2, lead, cx, y0 + hDome + lant * 1.1, cz, 10));
  g.add(cyl(0.14, 0.14, lant * 1.1, gold, cx, y0 + hDome + lant * 2.3, cz, 6));
}
pavilion(0, 5.0, 8.4, 2.6, 3.6, 0.95);                    // the great central dome (~46 m to the finial)
for (const sx of [-1, 1]) pavilion(sx * 62, 3.2, 4.8, 2.0, 2.6, 0.75, 10);
for (const sx of [-1, 1]) pavilion(sx * 31, 2.2, 3.0, 1.5, 1.8, 0.55, 8);
for (const sx of [-1, 1]) pavilion(sx * 62, 2.4, 3.6, 1.7, 2.1, 0.6, 8, false);

// ---------------------------------------------------------------- rooftop plant
for (const [px, pz, pw, pd, ph] of [[-24, -18, 16, 12, 4.0], [22, -20, 20, 14, 4.6],
[-46, 4, 12, 10, 3.2], [40, 8, 10, 9, 3.0], [4, -34, 22, 9, 2.6]]) {
  g.add(box(pw, ph, pd, plant, px, Y_ROOF, pz));
  g.add(box(pw + 0.8, 0.4, pd + 0.8, slate, px, Y_ROOF + ph, pz));
}
for (const [px, pz] of [[-30, -26], [30, -28], [0, -14]]) g.add(cyl(1.1, 1.1, 3.0, plant, px, Y_ROOF, pz, 8));

// ---------------------------------------------------------------- central entrance
g.add(box(24, 8.6, 3.2, tcd, 0, Y_PLINTH, D / 2 + 3.1));
for (let i = 0; i < 4; i++) g.add(column(0.85, H_G, pale, -5.4 + i * 3.6, Y_PLINTH, D / 2 + 4.4, 10));
g.add(box(23, 1.4, 4.2, pale, 0, Y_PLINTH + H_G, D / 2 + 4.0));
g.add(box(17, 2.6, 0.6, gold, 0, Y_PLINTH + H_G + 1.6, D / 2 + 4.4));   // the fascia sign
g.add(box(11, 4.6, 0.6, dark, 0, Y_PLINTH, D / 2 + 4.9));               // doors

await exportGLB(g, OUT + 'harrods.glb');
