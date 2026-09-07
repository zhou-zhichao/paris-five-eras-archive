// Buckingham House, William Winde for the Duke of Buckingham, 1703 — the red-brick house
// that Nash later swallowed up inside Buckingham Palace.
// Orientation: long axis along X; the ENTRANCE FRONT with its pilastered centre and
// pediment faces +Z, the quadrant colonnades sweeping forward to the flanking wings.
// Main house 40 x 30 m, three storeys ~16 m.  Ground y=0, whole composition centred on x,z.
import { exportGLB, box, cyl, cone, hipRoof, THREE,
  P, M, column, pediment, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const bk = M(0x9a5a48), pale = M(P.pale), st = M(P.stone), dk = M(P.dstone),
  slate = M(P.slate), lead = M(P.lead), dark = M(0x40382e), grav = M(0xa89b82);

const W = 40, D = 30, H = 16;
g.add(box(78, 0.4, 62, grav, 0, 0, 14));

// ---------------------------------------------------------------- the main house
g.add(box(W + 2, 1.0, D + 2, dk, 0, 0, 0));
g.add(box(W, H, D, bk, 0, 1.0, 0));
g.add(box(W + 1.4, 1.4, D + 1.4, pale, 0, 1.0 + H, 0));
g.add(balustrade(W + 1.4, D + 1.4, 1.8, pale, 0, 2.4 + H, 0));
g.add(hipRoof(W - 4, D - 4, 5.0, slate, 0, 2.4 + H, 0, 0.4));
// dormers
for (let i = 0; i < 5; i++) g.add(box(2.2, 2.6, 2.6, slate, -8 + i * 4, 2.4 + H, D / 2 - 6));
// giant pilaster order on the entrance front + pediment
for (let i = 0; i < 7; i++) {
  const x = -12 + i * 4;
  g.add(box(1.8, H - 3.5, 1.2, pale, x, 4.5, D / 2 + 0.2));
}
g.add(box(28, 1.6, 2.6, pale, 0, 1.0 + H, D / 2 + 0.4));
g.add(pediment(28, 5.2, 2.6, pale, 0, 2.6 + H, D / 2 + 0.4));
// windows, three storeys
for (const zs of [1, -1]) for (let i = 0; i < 9; i++) {
  const x = -W / 2 + 3 + i * (W - 6) / 8;
  g.add(box(2.2, 3.2, 0.6, dark, x, 3.0, zs * (D / 2 + 0.1)));
  g.add(box(2.2, 3.6, 0.6, dark, x, 8.0, zs * (D / 2 + 0.1)));
  g.add(box(2.0, 2.6, 0.6, dark, x, 13.0, zs * (D / 2 + 0.1)));
}
for (const sx of [-1, 1]) for (let i = 0; i < 6; i++) {
  const z = -D / 2 + 3 + i * (D - 6) / 5;
  g.add(box(0.6, 3.6, 2.2, dark, sx * (W / 2 + 0.1), 8.0, z));
  g.add(box(0.6, 2.6, 2.0, dark, sx * (W / 2 + 0.1), 13.0, z));
}

// ---------------------------------------------------------------- quadrant colonnades + wings
for (const sx of [-1, 1]) {
  // quarter-circle colonnade sweeping forward from the house to the wing
  const R = 20, cx = sx * (W / 2 - 2), cz = D / 2 + 18;
  for (let i = 0; i <= 7; i++) {
    const a = Math.PI / 2 * (i / 7);
    const px = cx - sx * R * Math.cos(a), pz = cz - R * Math.sin(a);
    g.add(column(0.6, 6.5, pale, px, 0.4, pz, 8));
  }
  for (let i = 0; i < 7; i++) {
    const a0 = Math.PI / 2 * (i / 7), a1 = Math.PI / 2 * ((i + 1) / 7);
    const p0 = [cx - sx * R * Math.cos(a0), cz - R * Math.sin(a0)];
    const p1 = [cx - sx * R * Math.cos(a1), cz - R * Math.sin(a1)];
    const len = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) + 1.4;
    const b = box(len, 1.6, 2.2, pale, (p0[0] + p1[0]) / 2, 6.9, (p0[1] + p1[1]) / 2);
    b.rotation.y = -Math.atan2(p1[1] - p0[1], p1[0] - p0[0]);
    g.add(b);
  }
  // the flanking service wing
  const wx = sx * 33, wz = D / 2 + 16;
  g.add(box(18, 10, 20, bk, wx, 0.4, wz));
  g.add(box(19.2, 1.2, 21.2, pale, wx, 10.4, wz));
  g.add(hipRoof(18, 20, 4.0, slate, wx, 11.6, wz, 0.4));
  for (let i = 0; i < 4; i++) g.add(box(1.9, 3.0, 0.6, dark, wx - 6 + i * 4, 3.0, wz + 10.1));
}

await exportGLB(g, OUT + 'buckingham_house.glb');
