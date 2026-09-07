// Southwark Cathedral (the priory church of St Mary Overie, 13th c., Early English).
// CONVENTION: metres, ground y=0, centred on the origin, LONG axis along x (west
// front at -x, retrochoir at +x).  "Front" = +z is the NORTH side, the side that
// faces the river and the approach from London Bridge.
//
// True dimensions: ~80 m long, nave + aisles ~22 m wide, nave ridge ~26 m,
// transepts ~38 m across, central tower with four pinnacles to ~50 m.
import {
  exportGLB, out, M, box, cyl, cone, gableRoof, hipRoof, group, THREE,
  crenel, crenelRing, pinnacle, turret, lancets, rose, profileWall,
} from './_lib_london.mjs';

const g = new THREE.Group();
const stone = M.rag, trim = M.medieval, lead = M.lead, dark = M.dark;
const WX = -40, EX = 40, HW = 11, CW = 5.5, AE = 10.5, AT = 14.5, CE = 20, RIDGE = 26;
const TR = 19, TD = 8, CX = 0;

function body(x0, x1, bays) {
  const gg = new THREE.Group();
  const len = x1 - x0, cx = (x0 + x1) / 2, ad = HW - CW;
  for (const s of [-1, 1]) {
    const az = s * (HW + CW) / 2;
    gg.add(box(len, AE, ad, stone, cx, 0, az));
    const slab = box(len, 0.6, Math.hypot(ad, AT - AE) * 1.05, lead, 0, 0, 0);
    slab.rotation.x = -s * Math.atan2(AT - AE, ad);
    slab.position.set(cx, AE + (AT - AE) / 2, az); gg.add(slab);
    gg.add(lancets(bays, len / bays, 2.4, 5.0, 0.45, dark, cx, 3.4, s * HW, true));
    for (let i = 0; i <= bays; i++) {
      const bx = x0 + i * len / bays;
      gg.add(box(1.4, AE + 1.6, 2.4, trim, bx, 0, s * (HW + 0.9)));
      gg.add(cone(1.0, 2.2, trim, bx, AE + 1.6, s * (HW + 0.9), 4));
    }
  }
  gg.add(box(len, CE, CW * 2, stone, cx, 0, 0));
  for (const s of [-1, 1]) gg.add(lancets(bays, len / bays, 2.0, 4.2, 0.4, dark, cx, CE - 6.5, s * CW, true));
  gg.add(box(len + 0.5, 0.8, CW * 2 + 1.0, trim, cx, CE - 0.8, 0));
  gg.add(gableRoof(len, CW * 2, RIDGE - CE, lead, cx, CE, 0, true, 0.5));
  return gg;
}
g.add(body(WX + 4, CX - TD, 6));                    // nave
g.add(body(CX + TD, EX - 12, 5));                   // choir

// retrochoir: a low four-chapel block across the east end
g.add(box(12, 12.5, HW * 2, stone, EX - 6, 0, 0));
g.add(box(12.6, 0.9, HW * 2 + 1.0, trim, EX - 6, 12.5, 0));
g.add(hipRoof(12, HW * 2, 3.6, lead, EX - 6, 13.4, 0, 0.7));
for (const s of [-1, 1]) for (const bz of [-7.5, -2.5, 2.5, 7.5])
  g.add(box(0.5, 5.5, 2.2, dark, EX + 0.1, 4.0, bz));
for (const s of [-1, 1]) for (let i = 0; i < 3; i++)
  g.add(box(2.4, 5.5, 0.5, dark, EX - 11 + i * 5, 4.0, s * HW));

// transepts
g.add(box(TD * 2, CE, TR * 2, stone, CX, 0, 0));
g.add(box(TD * 2 + 0.5, 0.8, TR * 2 + 1.0, trim, CX, CE - 0.8, 0));
g.add(gableRoof(TR * 2, TD * 2, RIDGE - CE, lead, CX, CE, 0, false, 0.5));
for (const s of [-1, 1]) {
  g.add(box(11.0, 5.0, 0.5, dark, CX, 13, s * TR + s * 0.3));
  g.add(box(4.0, 6.0, 0.5, dark, CX, 4, s * TR + s * 0.3));
  for (const sx of [-1, 1]) {
    g.add(box(1.6, CE + 2, 2.4, trim, CX + sx * (TD + 0.8), 0, s * TR));
    g.add(pinnacle(1.2, 4.5, trim, CX + sx * (TD + 0.8), CE + 2, s * TR));
    g.add(box(1.4, AE + 1.6, 2.2, trim, CX + sx * (TD + 0.8), 0, s * (HW + 4)));
  }
}

// central tower, ~42 m to the parapet, four corner pinnacles to 50 m
{
  const tw = 12.5;
  g.add(box(tw, 42, tw, stone, CX, 0, 0));
  for (const f of [0.62, 0.82]) for (const s of [-1, 1]) {
    g.add(box(6.0, 42 * 0.10, 0.5, dark, CX, 42 * f, s * (tw / 2 + 0.1)));
    g.add(box(0.5, 42 * 0.10, 6.0, dark, CX + s * (tw / 2 + 0.1), 42 * f, 0));
  }
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
    g.add(box(2.4, 42, 2.4, trim, CX + a[0] * (tw / 2 - 0.2), 0, a[1] * (tw / 2 - 0.2)));
  g.add(box(tw + 1.4, 1.1, tw + 1.4, trim, CX, 42, 0));
  g.add(crenelRing(tw + 1.4, tw + 1.4, 0.8, trim, CX, 43.1, 0, 1.3, 1.4, 1.2));
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
    g.add(pinnacle(1.5, 7.0, trim, CX + a[0] * (tw / 2 + 0.4), 43.1, a[1] * (tw / 2 + 0.4)));
}

// west front
g.add(box(6, CE, HW * 2, stone, WX + 3, 0, 0));
g.add(profileWall([[-CW, 0], [CW, 0], [0, RIDGE - CE]], 6, stone, WX + 3, CE, 0, Math.PI / 2));
g.add(box(0.6, 9.0, 6.5, dark, WX + 0.1, 8, 0));
g.add(box(0.6, 5.0, 3.0, dark, WX + 0.1, 0, 0));
for (const s of [-1, 1]) g.add(turret(1.8, CE + 5, trim, lead, WX + 1.0, 0, s * (HW - 1.5), 8, 4.0));
// north porch on the +z side
g.add(box(7, 8, 5, trim, -18, 0, HW + 3.4));
g.add(gableRoof(7, 5, 3.2, lead, -18, 8, HW + 3.4, true, 0.4));
g.add(box(3.2, 5.0, 0.5, dark, -18, 0, HW + 5.9));

await exportGLB(g, out('southwark_cathedral'));
