// A generic large medieval priory / abbey of the kind that ringed London
// (St Mary Spital, Holy Trinity Aldgate, Bermondsey, St Bartholomew's):
// a cruciform church with a squat central tower, a cloister with chapter house,
// dormitory range and refectory.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x (west front at -x, presbytery at +x).  "Front" = +z is the CLOISTER
// side (conventionally the south side of the church).
//
// True dimensions: church 75 x 20 m, nave ridge ~24 m, central tower 35 m,
// cloister garth ~30 m square.
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, hipRoof, group, THREE,
  crenel, crenelRing, pinnacle, turret, lancets, rose, profileWall,
} from './_lib_london.mjs';

const g = new THREE.Group();
const stone = M.medieval, trim = M.rag, lead = M.lead, dark = M.dark, tile = M.tile;
const WX = -37.5, EX = 37.5, HW = 10, CW = 5, AE = 9.5, AT = 13, CE = 18, RIDGE = 24;
const TR = 18, TD = 7.5, CX = -2;

function body(x0, x1, bays) {
  const gg = new THREE.Group();
  const len = x1 - x0, cx = (x0 + x1) / 2, ad = HW - CW;
  for (const s of [-1, 1]) {
    const az = s * (HW + CW) / 2;
    gg.add(box(len, AE, ad, stone, cx, 0, az));
    const slab = box(len, 0.6, Math.hypot(ad, AT - AE) * 1.05, lead, 0, 0, 0);
    slab.rotation.x = -s * Math.atan2(AT - AE, ad);
    slab.position.set(cx, AE + (AT - AE) / 2, az); gg.add(slab);
    gg.add(lancets(bays, len / bays, 2.2, 4.6, 0.45, dark, cx, 3.0, s * HW, true));
    for (let i = 0; i <= bays; i++) {
      const bx = x0 + i * len / bays;
      gg.add(box(1.3, AE + 1.4, 2.2, trim, bx, 0, s * (HW + 0.8)));
      gg.add(cone(0.95, 2.0, trim, bx, AE + 1.4, s * (HW + 0.8), 4));
    }
  }
  gg.add(box(len, CE, CW * 2, stone, cx, 0, 0));
  for (const s of [-1, 1]) gg.add(lancets(bays, len / bays, 1.9, 3.8, 0.4, dark, cx, CE - 6.0, s * CW, true));
  gg.add(box(len + 0.5, 0.8, CW * 2 + 1.0, trim, cx, CE - 0.8, 0));
  gg.add(gableRoof(len, CW * 2, RIDGE - CE, lead, cx, CE, 0, true, 0.5));
  return gg;
}
g.add(body(WX + 3, CX - TD, 7));                 // nave
g.add(body(CX + TD, EX - 3, 6));                 // presbytery

// transepts
g.add(box(TD * 2, CE, TR * 2, stone, CX, 0, 0));
g.add(box(TD * 2 + 0.5, 0.8, TR * 2 + 1.0, trim, CX, CE - 0.8, 0));
g.add(gableRoof(TR * 2, TD * 2, RIDGE - CE, lead, CX, CE, 0, false, 0.5));
for (const s of [-1, 1]) {
  g.add(box(9.0, 4.6, 0.5, dark, CX, 11.5, s * TR + s * 0.3));
  g.add(box(3.4, 5.4, 0.5, dark, CX, 3.5, s * TR + s * 0.3));
  for (const sx of [-1, 1]) {
    g.add(box(1.5, CE + 1.6, 2.2, trim, CX + sx * (TD + 0.7), 0, s * TR));
    g.add(pinnacle(1.1, 4.0, trim, CX + sx * (TD + 0.7), CE + 1.6, s * TR));
  }
  // eastern transept chapels
  g.add(box(6, AE, 10, stone, CX + TD + 3, 0, s * (TR - 5)));
  g.add(gableRoof(10, 6, 3.0, lead, CX + TD + 3, AE, s * (TR - 5), false, 0.4));
}

// squat central tower, 35 m
{
  const tw = 13.5;
  g.add(box(tw, 35, tw, stone, CX, 0, 0));
  for (const f of [0.66, 0.86]) for (const s of [-1, 1]) {
    g.add(box(6.0, 3.6, 0.5, dark, CX, 35 * f, s * (tw / 2 + 0.1)));
    g.add(box(0.5, 3.6, 6.0, dark, CX + s * (tw / 2 + 0.1), 35 * f, 0));
  }
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
    g.add(box(2.4, 35, 2.4, trim, CX + a[0] * (tw / 2 - 0.2), 0, a[1] * (tw / 2 - 0.2)));
  g.add(box(tw + 1.4, 1.1, tw + 1.4, trim, CX, 35, 0));
  g.add(crenelRing(tw + 1.4, tw + 1.4, 0.8, trim, CX, 36.1, 0, 1.3, 1.4, 1.2));
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
    g.add(pinnacle(1.2, 5.0, trim, CX + a[0] * (tw / 2 + 0.4), 36.1, a[1] * (tw / 2 + 0.4)));
  g.add(hipRoof(tw, tw, 3.5, lead, CX, 36.1, 0, 0.2));
}

// west front and east end
g.add(box(6, CE, HW * 2, stone, WX + 3, 0, 0));
g.add(profileWall([[-CW, 0], [CW, 0], [0, RIDGE - CE]], 6, stone, WX + 3, CE, 0, Math.PI / 2));
g.add(box(0.6, 8.0, 5.5, dark, WX + 0.1, 7, 0));
g.add(box(0.6, 4.5, 2.8, dark, WX + 0.1, 0, 0));
for (const s of [-1, 1]) g.add(turret(1.7, CE + 5, trim, lead, WX + 1.0, 0, s * (HW - 1.5), 8, 4.0));
g.add(profileWall([[-CW, 0], [CW, 0], [0, RIDGE - CE]], 6, stone, EX - 3, CE, 0, Math.PI / 2));
g.add(box(0.6, 9.0, 6.0, dark, EX - 0.1, 5, 0));
for (const s of [-1, 1]) g.add(box(1.4, AE + 2, 2.2, trim, EX + 0.5, 0, s * (HW - 3)));

// ---------------------------------------------------------------- cloister (+z)
{
  const clx = -12, clz = 26, S = 34, walk = 6.5;
  for (const [ox, oz, w, d, alongX] of [
    [0, -S / 2 + walk / 2, S, walk, true],
    [0, S / 2 - walk / 2, S, walk, true],
    [-S / 2 + walk / 2, 0, walk, S - 2 * walk, false],
    [S / 2 - walk / 2, 0, walk, S - 2 * walk, false],
  ]) {
    g.add(box(w, 6.5, d, stone, clx + ox, 0, clz + oz));
    g.add(gableRoof(Math.max(w, d), Math.min(w, d), 2.6, lead, clx + ox, 6.5, clz + oz, alongX, 0.5));
    const n = Math.floor(Math.max(w, d) / 3.2);
    for (let i = 0; i < n; i++) {
      const u = -Math.max(w, d) / 2 + (i + 0.5) * Math.max(w, d) / n;
      const inner = alongX ? [clx + ox + u, clz + oz - Math.sign(oz) * walk / 2] : [clx + ox - Math.sign(ox) * walk / 2, clz + oz + u];
      g.add(box(alongX ? 1.9 : 0.4, 3.0, alongX ? 0.4 : 1.9, dark, inner[0], 1.6, inner[1]));
    }
  }
  g.add(box(S - 2 * walk, 0.4, S - 2 * walk, M.grass, clx, 0.2, clz));

  // east range: chapter house below, dormitory above, running back from the transept
  g.add(box(12, 12, 34, stone, clx + S / 2 + 6, 0, clz));
  g.add(gableRoof(34, 12, 5.0, tile, clx + S / 2 + 6, 12, clz, false, 0.5));
  for (let i = 0; i < 7; i++) for (const s of [-1, 1])
    g.add(box(0.4, 2.4, 1.8, dark, clx + S / 2 + 6 + s * 6, 7.5, clz - 14 + i * 4.6));
  // the chapter house itself, polygonal, projecting east
  const chx = clx + S / 2 + 17, chz = clz - 8;
  g.add(cyl(7.5, 7.8, 11, stone, chx, 0, chz, 8));
  for (let i = 0; i < 8; i++) {
    const a = i * Math.PI / 4;
    g.add(box(1.0, 12.5, 1.0, trim, chx + 7.6 * Math.cos(a), 0, chz + 7.6 * Math.sin(a)));
    const w = box(2.4, 4.6, 0.4, dark, chx + 7.4 * Math.cos(a + Math.PI / 8), 3.5, chz + 7.4 * Math.sin(a + Math.PI / 8));
    w.rotation.y = Math.PI / 2 - (a + Math.PI / 8); g.add(w);
  }
  g.add(cone(8.4, 6.0, lead, chx, 11, chz, 8));
  g.add(cone(0.9, 2.6, M.gold, chx, 17, chz, 6));

  // south range: the refectory over an undercroft
  g.add(box(36, 12.5, 12, stone, clx, 0, clz + S / 2 + 6));
  g.add(gableRoof(36, 12, 5.5, tile, clx, 12.5, clz + S / 2 + 6, true, 0.6));
  for (let i = 0; i < 7; i++) for (const s of [-1, 1])
    g.add(box(2.2, 4.4, 0.45, dark, clx - 15 + i * 5, 6.5, clz + S / 2 + 6 + s * 6));
  for (let i = 0; i <= 7; i++)
    g.add(box(1.1, 12.5, 1.5, trim, clx - 17.5 + i * 5, 0, clz + S / 2 + 12.6));
  // west range: cellarer's range and the guest hall
  g.add(box(12, 10, 34, stone, clx - S / 2 - 6, 0, clz));
  g.add(gableRoof(34, 12, 4.6, tile, clx - S / 2 - 6, 10, clz, false, 0.5));
  for (let i = 0; i < 7; i++)
    g.add(box(0.4, 2.2, 1.8, dark, clx - S / 2 - 12.2, 5.5, clz - 14 + i * 4.6));
}

// infirmary
g.add(box(28, 9.5, 11, stone, 34, 0, 40));
g.add(gableRoof(28, 11, 4.6, tile, 34, 9.5, 40, true, 0.5));

g.position.z = -18;
await exportGLB(g, out('medieval_abbey'));
