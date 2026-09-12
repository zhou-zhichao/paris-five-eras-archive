// Smithfield Central Markets, Sir Horace Jones, 1866-68.  A ~190 x 75 m Italianate meat
// market: two great arcaded halls of red brick with Portland stone dressings under glazed
// ridge-and-furrow roofs, split down the middle by the GRAND AVENUE — a covered roadway
// crossing the short axis under a tall glazed arch — with octagonal domed towers at the
// four corners.
// Orientation: long axis along X; the +Z front (Charterhouse Street) carries the Grand
// Avenue's main portal.  Ground y=0, footprint centred on the origin.
import { exportGLB, box, cyl, cone, lathe, gableRoof, prism, THREE,
  P, M, openWall, arcade, pediment, pinnacle, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const bk = M(P.brick), bkd = M(0x83483a), st = M(P.stone), pale = M(P.pale),
  dk = M(P.dstone), slate = M(P.slate), lead = M(P.lead), iron = M(P.iron),
  glass = M(P.glassroof), cop = M(P.copper), gold = M(P.gold), dark = M(0x2f3134);

const W = 190, D = 74;
const AV = 8;                 // half-width of the Grand Avenue
const PL = 1.0;               // plinth
const EAVE = 15.0;            // hall eaves / main cornice
const HW = W / 2 - AV;        // width of each hall
const HCX = AV + HW / 2;      // hall centre x

// ---------------------------------------------------------------- plinth
g.add(box(W + 3, PL, D + 3, dk, 0, 0, 0));

// ---------------------------------------------------------------- the two market halls
for (const sx of [-1, 1]) {
  const cx = sx * HCX;
  // solid core, set back so the arcaded screens read as a real arcade
  g.add(box(HW - 2.0, EAVE - PL, D - 2.6, bk, cx, PL, 0));
  // long arcaded fronts (+z and -z)
  const NA = 10;
  for (const sz of [1, -1]) {
    g.add(arcade(HW, EAVE - PL, 1.3, bk, NA, 6.0, 5.6, cx, PL, sz * (D / 2 - 0.65), 2.0, 8));
    // stone pilasters between the arches
    for (let i = 0; i <= NA; i++) {
      const x = cx - HW / 2 + i * HW / NA;
      g.add(box(2.0, EAVE - PL, 1.9, st, x, PL, sz * (D / 2 - 0.5)));
      g.add(box(2.6, 0.9, 2.4, pale, x, EAVE - 1.6, sz * (D / 2 - 0.5)));
    }
    // iron gates inside the arches
    for (let i = 0; i < NA; i++) {
      const x = cx - HW / 2 + (i + 0.5) * HW / NA;
      g.add(box(5.4, 5.0, 0.4, dark, x, PL + 2.0, sz * (D / 2 - 1.5)));
    }
  }
  // gable ends (x = +-W/2)
  const end = openWall(D, EAVE - PL, 1.3, bk,
    [{ cx: -18, y0: 2.0, w: 6.0, h: 5.6 }, { cx: 0, y0: 2.0, w: 7.0, h: 6.6 }, { cx: 18, y0: 2.0, w: 6.0, h: 5.6 }],
    0, 0, 0, 8);
  const endG = new THREE.Group(); endG.add(end); endG.rotation.y = Math.PI / 2;
  endG.position.set(sx * (W / 2 - 0.65), PL, 0); g.add(endG);

  // stone banding and main cornice
  g.add(box(HW + 1.2, 0.8, D + 1.2, st, cx, PL + 8.4, 0));
  g.add(box(HW + 2.0, 1.4, D + 2.0, pale, cx, EAVE - 1.4, 0));
  g.add(box(HW + 1.0, 1.2, D + 1.0, st, cx, EAVE, 0));            // parapet band

  // ---- roof: two glazed ridge-and-furrow spans running along X
  for (const sz2 of [-1, 1]) {
    const zc = sz2 * (D / 4);
    const span = D / 2 - 1.0;
    g.add(gableRoof(HW - 1, span, 6.2, slate, cx, EAVE + 1.2, zc, true, 0.5));
    // glazed ridge lantern
    g.add(box(HW - 5, 2.4, 5.2, glass, cx, EAVE + 5.9, zc));
    for (let i = 0; i <= 20; i++) {                 // glazing bars in the lantern
      const x = cx - (HW - 5) / 2 + i * (HW - 5) / 20;
      g.add(box(0.3, 2.4, 5.4, iron, x, EAVE + 5.9, zc));
    }
    g.add(box(HW - 4.4, 0.6, 6.0, lead, cx, EAVE + 8.3, zc));
    // iron cresting along the ridge
    for (let i = 0; i < 26; i++) {
      const x = cx - HW / 2 + 3 + i * (HW - 6) / 25;
      g.add(box(0.3, 0.9, 0.3, iron, x, EAVE + 8.9, zc));
    }
    // glazing bars down the slopes
    for (let i = 0; i < 18; i++) {
      const x = cx - HW / 2 + 2 + i * (HW - 4) / 17;
      for (const s2 of [-1, 1]) {
        const b = box(0.3, 0.35, span / 2 + 0.9, iron, x, EAVE + 4.0, zc + s2 * (span / 4 + 0.2));
        b.rotation.x = s2 * Math.atan2(6.2, span / 2);
        g.add(b);
      }
    }
  }
  // valley gutter between the two spans
  g.add(box(HW, 1.0, 2.4, lead, cx, EAVE + 1.0, 0));
  // louvred dormers on the outer slopes
  for (let i = 0; i < 6; i++) {
    const x = cx - HW / 2 + 8 + i * (HW - 16) / 5;
    for (const sz2 of [-1, 1]) {
      g.add(box(4.0, 2.6, 3.0, slate, x, EAVE + 2.6, sz2 * (D / 2 - 5.0)));
      g.add(box(3.2, 1.6, 0.4, dark, x, EAVE + 3.0, sz2 * (D / 2 - 3.6)));
    }
  }
}

// ---------------------------------------------------------------- the Grand Avenue
// a covered roadway on x in [-AV, AV] running the full depth, under a taller glazed arch
const GA_EAVE = 17.0, GA_RISE = 8.0;
for (const sx of [-1, 1]) {
  // the arcaded walls that flank the avenue
  g.add(box(2.2, GA_EAVE - PL, D, st, sx * (AV - 1.1), PL, 0));
  g.add(box(3.0, 1.2, D, pale, sx * (AV - 1.5), GA_EAVE - 1.2, 0));
  for (let i = 0; i < 9; i++) {
    const z = -D / 2 + 4.5 + i * (D - 9) / 8;
    g.add(box(1.2, 6.4, 4.2, dark, sx * (AV - 1.7), PL + 2.0, z));
  }
}
// glazed segmental vault over the avenue
{
  const r = AV - 0.6, s = new THREE.Shape(), n = 12;
  s.moveTo(-r, 0);
  for (let i = 0; i <= n; i++) { const a = Math.PI - Math.PI * i / n; s.lineTo(Math.cos(a) * r, Math.sin(a) * GA_RISE); }
  s.closePath();
  const m = new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: D, bevelEnabled: false }), glass);
  m.position.set(0, GA_EAVE, -D / 2); g.add(m);
  // iron ribs
  for (let k = 0; k <= 10; k++) {
    const z = -D / 2 + k * D / 10;
    for (let i = 0; i < n; i++) {
      const a0 = Math.PI - Math.PI * i / n, a1 = Math.PI - Math.PI * (i + 1) / n;
      const x0 = Math.cos(a0) * r, y0 = Math.sin(a0) * GA_RISE, x1 = Math.cos(a1) * r, y1 = Math.sin(a1) * GA_RISE;
      const b = box(Math.hypot(x1 - x0, y1 - y0), 0.45, 0.55, iron,
        (x0 + x1) / 2, GA_EAVE + (y0 + y1) / 2 - 0.22, z);
      b.rotation.z = Math.atan2(y1 - y0, x1 - x0); g.add(b);
    }
  }
  g.add(box(1.2, 0.6, D, lead, 0, GA_EAVE + GA_RISE - 0.3, 0));
}
// the two great portals at the ends of the avenue
for (const sz of [1, -1]) {
  const z = sz * (D / 2 + 0.9);
  g.add(openWall(2 * AV + 8, 24.0, 1.8, st,
    [{ cx: 0, y0: 1.0, w: 12.0, h: 9.0, arch: true }], 0, PL, z, 12));
  g.add(box(2 * AV + 10, 1.4, 3.0, pale, 0, PL + 24.0, z));
  g.add(pediment(2 * AV + 10, 5.0, 2.6, st, 0, PL + 25.4, z));
  g.add(box(6.0, 1.2, 0.5, gold, 0, PL + 20.0, z + sz * 1.0));       // name panel
  g.add(box(11.0, 5.0, 0.4, dark, 0, PL + 1.0, z + sz * 0.9));       // iron gates
  for (const sx of [-1, 1]) g.add(pinnacle(1.3, 5.0, st, sx * (AV + 3.2), PL + 24.0, z, 8));
}

// ---------------------------------------------------------------- octagonal corner towers
function cornerTower(cx, cz) {
  const R = 6.2;
  const t = new THREE.Group();
  t.add(cyl(R, R * 1.06, 18.0, bk, 0, 0, 0, 8));
  // stone quoin bands
  for (const yy of [4.2, 9.0, 13.8]) t.add(cyl(R * 1.05, R * 1.05, 1.0, st, 0, yy, 0, 8));
  // arched openings on each storey
  for (const yy of [3.0, 10.2]) for (let i = 0; i < 8; i++) {
    const a = (i + 0.5) / 8 * Math.PI * 2;
    const b = box(2.4, 3.4, 0.6, dark, Math.cos(a) * R * 0.98, yy, Math.sin(a) * R * 0.98);
    b.rotation.y = -a; t.add(b);
  }
  t.add(cyl(R * 1.22, R * 1.22, 1.6, pale, 0, 18.0, 0, 8));           // cornice
  // belfry stage
  t.add(cyl(R * 0.82, R * 0.86, 4.2, st, 0, 19.6, 0, 8));
  for (let i = 0; i < 8; i++) {
    const a = (i + 0.5) / 8 * Math.PI * 2;
    const b = box(2.6, 3.0, 0.6, dark, Math.cos(a) * R * 0.83, 20.0, Math.sin(a) * R * 0.83);
    b.rotation.y = -a; t.add(b);
  }
  t.add(cyl(R * 1.02, R * 1.02, 1.1, pale, 0, 23.8, 0, 8));
  // ogee cupola + finial
  t.add(lathe([[R * 0.92, 0], [R * 0.9, 0.9], [R * 0.74, 2.2], [R * 0.5, 3.4],
  [R * 0.26, 4.3], [R * 0.1, 4.9], [0, 5.2]], cop, 0, 24.9, 0, 8));
  t.add(cyl(0.9, 1.1, 1.3, pale, 0, 29.6, 0, 8));
  t.add(cone(1.0, 1.4, cop, 0, 30.9, 0, 8));
  t.add(cyl(0.12, 0.12, 1.4, gold, 0, 32.3, 0, 6));
  t.position.set(cx, PL, cz);
  g.add(t);
}
for (const sx of [-1, 1]) for (const sz of [-1, 1])
  cornerTower(sx * (W / 2 - 4.2), sz * (D / 2 - 4.2));

// ---------------------------------------------------------------- pavement detail
for (let i = 0; i < 14; i++) {
  const x = -W / 2 + 8 + i * (W - 16) / 13;
  if (Math.abs(x) < AV + 10) continue;
  for (const sz of [-1, 1]) {
    g.add(cyl(0.34, 0.42, 1.1, iron, x, 0, sz * (D / 2 + 3.2), 6));
    g.add(cyl(0.0, 0.34, 0.32, iron, x, 1.1, sz * (D / 2 + 3.2), 6));
  }
}

await exportGLB(g, OUT + 'smithfield_market.glb');
