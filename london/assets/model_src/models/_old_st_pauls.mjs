// Shared builder for Old St Paul's Cathedral (medieval, burnt 1666).
// CONVENTION: metres, ground y=0, footprint centred on origin, LONG axis along x
// (west front at -x, east end / great rose at +x).  "Front" = +z is the SOUTH
// flank -- the side seen from the river and from Ludgate Hill.
//
// True dimensions: 178 m long, nave+aisles 30 m wide, transepts ~90 m across,
// nave ridge ~45 m, central tower 87 m + lead spire to 149 m (to 1561).
import {
  M, mat, box, cyl, cone, dome, gableRoof, hipRoof, lathe, group, THREE,
  wall, archPath, rectPath, crenel, crenelRing, colonnade, pinnacle, turret,
  lancets, rose, profileWall,
} from './_lib_london.mjs';

export const L = {
  WX: -89, EX: 89,          // west front / east end
  CX: 2,                    // crossing centre (choir slightly shorter than nave)
  NAVE_HW: 15,              // half width over the aisles (z)
  CEN_HW: 7.5,              // half width of the central vessel
  AISLE_EAVES: 19, AISLE_TOP: 24,
  CLER_EAVES: 34, RIDGE: 45,
  TR_HW: 45,                // transept half length (z)
  TR_HD: 11,                // transept half depth (x)
};

export function buildOldStPauls({ spire = true, portico = false, towerTop = 87 } = {}) {
  const g = new THREE.Group();
  const stone = portico ? M.pale : M.medieval;   // Jones re-cased the nave in Portland
  const trim = M.rag;
  const lead = M.lead;
  const dark = M.dark;
  const port = M.portland;

  const { WX, EX, CX, NAVE_HW, CEN_HW, AISLE_EAVES, AISLE_TOP, CLER_EAVES, RIDGE, TR_HW, TR_HD } = L;
  const AISLE_D = NAVE_HW - CEN_HW;           // 7.5 m per aisle

  // ---------------------------------------------------------------- main vessel
  // A nave/choir body running from x0 to x1: aisles + lean-to roofs + clerestory
  // + steep lead gable roof, buttresses at every bay.
  function body(x0, x1, bays, flying) {
    const gg = new THREE.Group();
    const len = x1 - x0, cx = (x0 + x1) / 2;
    for (const s of [-1, 1]) {
      const az = s * (NAVE_HW + CEN_HW) / 2;
      gg.add(box(len, AISLE_EAVES, AISLE_D, stone, cx, 0, az));
      // lean-to lead roof over the aisle
      const rise = AISLE_TOP - AISLE_EAVES;
      const slab = box(len, 0.7, Math.hypot(AISLE_D, rise) * 1.04, lead, 0, 0, 0);
      slab.rotation.x = -s * Math.atan2(rise, AISLE_D);
      slab.position.set(cx, AISLE_EAVES + rise / 2, az);
      gg.add(slab);
      // aisle windows (tall pointed lancets, dark)
      gg.add(lancets(bays, len / bays, 3.4, 8.5, 0.5, dark, cx, 7.5, s * NAVE_HW, true));
      // aisle buttresses between the bays
      for (let i = 0; i <= bays; i++) {
        const bx = x0 + i * len / bays;
        gg.add(box(1.9, AISLE_EAVES + 1.5, 2.4, trim, bx, 0, s * (NAVE_HW + 1.0)));
        gg.add(cone(1.3, 2.6, trim, bx, AISLE_EAVES + 1.5, s * (NAVE_HW + 1.0), 4));
      }
    }
    // clerestory + high roof
    gg.add(box(len, CLER_EAVES, CEN_HW * 2, stone, cx, 0, 0));
    for (const s of [-1, 1])
      gg.add(lancets(bays, len / bays, 3.0, 6.0, 0.45, dark, cx, CLER_EAVES - 8.5, s * CEN_HW, true));
    gg.add(box(len + 0.6, 1.0, CEN_HW * 2 + 1.2, trim, cx, CLER_EAVES - 0.9, 0));  // cornice
    gg.add(gableRoof(len, CEN_HW * 2, RIDGE - CLER_EAVES, lead, cx, CLER_EAVES, 0, true, 0.6));
    // flying buttresses springing from the aisle piers to the clerestory
    if (flying) {
      for (let i = 1; i < bays; i++) {
        const bx = x0 + i * len / bays;
        for (const s of [-1, 1]) {
          const reach = NAVE_HW + 1.0 - CEN_HW, topY = CLER_EAVES - 4;
          const strut = box(1.0, 1.1, Math.hypot(reach, topY - 15), trim, 0, 0, 0);
          strut.rotation.x = -s * Math.atan2(topY - 15, reach);
          strut.position.set(bx, 15 + (topY - 15) / 2, s * (CEN_HW + reach / 2));
          gg.add(strut);
        }
      }
    }
    return gg;
  }

  const naveX0 = WX + 8, naveX1 = CX - TR_HD;      // nave
  const choirX0 = CX + TR_HD, choirX1 = EX - 4;    // choir / "New Work"
  g.add(body(naveX0, naveX1, 12, false));
  g.add(body(choirX0, choirX1, 10, true));

  // ---------------------------------------------------------------- transepts
  // Full-height transept block across the crossing, ridge running along z.
  g.add(box(TR_HD * 2, CLER_EAVES, TR_HW * 2, stone, CX, 0, 0));
  g.add(box(TR_HD * 2 + 0.6, 1.0, TR_HW * 2 + 1.2, trim, CX, CLER_EAVES - 0.9, 0));
  g.add(gableRoof(TR_HW * 2, TR_HD * 2, RIDGE - CLER_EAVES, lead, CX, CLER_EAVES, 0, false, 0.6));
  // transept aisles flanking each arm
  for (const s of [-1, 1]) {
    for (const sx of [-1, 1]) {
      const az = s * (NAVE_HW + (TR_HW - NAVE_HW) / 2);
      const armLen = TR_HW - NAVE_HW;
      g.add(box(6, AISLE_EAVES, armLen, stone, CX + sx * (TR_HD + 3), 0, az));
      const slab = box(6, 0.7, Math.hypot(6, 4) * 1.04, lead, 0, 0, 0);
      slab.rotation.z = sx * Math.atan2(4, 6);
      slab.position.set(CX + sx * (TR_HD + 3), AISLE_EAVES + 2, az);
      g.add(slab);
    }
    // transept end: gable wall with a big pointed window, flanking turrets
    const ez = s * TR_HW;
    g.add(box(TR_HD * 2, 4.5, 1.0, dark, CX, 22, ez + s * 0.3));           // great window
    g.add(box(6.0, 12.0, 1.0, dark, CX, 9, ez + s * 0.3));
    for (const sx of [-1, 1]) g.add(turret(2.2, CLER_EAVES + 5, trim, trim, CX + sx * (TR_HD + 0.6), 0, ez, 8, 4.5));
    // clerestory-level buttresses on the arm flanks
    for (const sx of [-1, 1]) for (const t of [0.35, 0.75])
      g.add(box(2.2, CLER_EAVES, 1.9, trim, CX + sx * (TR_HD + 0.9), 0, s * (NAVE_HW + t * (TR_HW - NAVE_HW))));
  }
  // north transept porch (+ a modest one on the south)
  g.add(box(9, 11, 7, trim, CX, 0, -TR_HW - 3.5));
  g.add(gableRoof(9, 7, 4, lead, CX, 11, 0 - TR_HW - 3.5, true, 0.4));
  g.add(box(4.5, 7.5, 1.0, dark, CX, 0, -TR_HW - 7.0));

  // ---------------------------------------------------------------- east end
  {
    const ex = EX - 4;
    g.add(box(8, CLER_EAVES, NAVE_HW * 2, stone, ex + 4, 0, 0));
    g.add(profileWall([[-CEN_HW, 0], [CEN_HW, 0], [0, RIDGE - CLER_EAVES]], 8, stone, ex + 4, CLER_EAVES, 0, Math.PI / 2));
    g.add(rose(5.6, 0.8, trim, dark, EX + 0.2, 26, 0, Math.PI / 2, 10));
    g.add(box(1.0, 13.0, 12.0, dark, EX + 0.1, 8, 0));   // great east window below the rose
    for (const s of [-1, 1]) g.add(turret(2.4, CLER_EAVES + 6, trim, trim, EX - 1, 0, s * (NAVE_HW - 2), 8, 5));
    for (const s of [-1, 1]) g.add(box(2.0, AISLE_EAVES + 2, 2.4, trim, EX + 0.6, 0, s * (NAVE_HW - 6)));
  }

  // ---------------------------------------------------------------- west front
  {
    const wt = 12, tz = NAVE_HW - wt / 2 + 1.5;   // twin west towers
    g.add(box(10, CLER_EAVES, NAVE_HW * 2, stone, WX + 5, 0, 0));
    g.add(profileWall([[-CEN_HW, 0], [CEN_HW, 0], [0, RIDGE - CLER_EAVES]], 10, stone, WX + 5, CLER_EAVES, 0, Math.PI / 2));
    g.add(box(1.0, 16.0, 11.0, dark, WX + 0.1, 12, 0));            // great west window
    g.add(box(1.0, 8.0, 5.0, dark, WX + 0.1, 0, 0));               // west door
    for (const s of [-1, 1]) {
      g.add(box(wt, 33, wt, stone, WX + wt / 2 - 1, 0, s * tz));
      g.add(box(wt + 1.2, 1.2, wt + 1.2, trim, WX + wt / 2 - 1, 33, s * tz));
      for (const f of [0.45, 0.72]) g.add(box(1.0, 6.5, 5.0, dark, WX + 0.1, 33 * f, s * tz));
      g.add(hipRoof(wt, wt, 7, lead, WX + wt / 2 - 1, 34.2, s * tz, 0.1));
      for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
        g.add(pinnacle(1.0, 5.0, trim, WX + wt / 2 - 1 + a[0] * (wt / 2 - 0.6), 34.2, s * tz + a[1] * (wt / 2 - 0.6)));
    }
  }

  // ---------------------------------------------------------------- central tower
  const TW = 22;
  g.add(box(TW, towerTop, TW, stone, CX, 0, 0));
  // string courses + tall paired belfry openings
  for (const f of [0.42, 0.62, 0.80]) g.add(box(TW + 1.0, 1.0, TW + 1.0, trim, CX, towerTop * f, 0));
  for (const s of [-1, 1]) {
    g.add(box(9.0, towerTop * 0.15, 0.6, dark, CX, towerTop * 0.63, s * (TW / 2 + 0.1)));
    g.add(box(0.6, towerTop * 0.15, 9.0, dark, CX + s * (TW / 2 + 0.1), towerTop * 0.63, 0));
    g.add(box(7.0, towerTop * 0.10, 0.6, dark, CX, towerTop * 0.44, s * (TW / 2 + 0.1)));
    g.add(box(0.6, towerTop * 0.10, 7.0, dark, CX + s * (TW / 2 + 0.1), towerTop * 0.44, 0));
  }
  // corner buttress strips
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
    g.add(box(3.4, towerTop, 3.4, trim, CX + a[0] * (TW / 2 - 0.4), 0, a[1] * (TW / 2 - 0.4)));
  // parapet + corner turrets
  g.add(box(TW + 2.0, 1.6, TW + 2.0, trim, CX, towerTop, 0));
  g.add(crenelRing(TW + 2.0, TW + 2.0, 0.9, trim, CX, towerTop + 1.6, 0, 1.5, 1.6, 1.4));
  for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
    g.add(turret(1.9, 7.0, trim, trim, CX + a[0] * (TW / 2 + 0.2), towerTop + 1.6, a[1] * (TW / 2 + 0.2), 8, 5.0));

  if (spire) {
    // octagonal lead spire: 87 m -> 149 m
    const base = towerTop + 3.2;
    g.add(cyl(8.4, 9.2, 3.6, trim, CX, base, 0, 8));
    const SH = 51.4;                       // spire cone: tip of the cross at 149 m
    const prof = [[8.0, 0], [7.0, 5], [5.6, 13], [4.2, 23], [3.0, 33], [2.0, 42], [1.15, 50], [0.5, 57], [0.18, 60.5]]
      .map(([r, h]) => [r, h * SH / 60.5]);
    g.add(lathe(prof, lead, CX, base + 3.6, 0, 8));
    // crockets / bands to break the cone up
    for (const [r, h] of [[6.3, 8], [4.6, 20], [3.1, 32], [1.9, 43]])
      g.add(cyl(r * 0.98, r * 1.10, 0.9, trim, CX, base + 3.6 + h * SH / 60.5, 0, 8));
    // ball + cross finial
    g.add(dome(1.4, M.gold, CX, base + 3.6 + SH, 0, 8, 1.0));
    g.add(box(0.35, 3.6, 0.35, M.gold, CX, base + 3.9 + SH, 0));
    g.add(box(1.9, 0.35, 0.35, M.gold, CX, base + 5.6 + SH, 0));
  }

  // ---------------------------------------------------------------- chapter house + cloister (south of nave)
  {
    const cx = -46, cz = 30;
    g.add(box(34, 7.0, 30, stone, cx, 0, cz));                     // cloister range
    g.add(hipRoof(34, 30, 3.0, lead, cx, 7.0, cz, 0.6));
    g.add(box(24, 0.4, 20, M.grass, cx, 7.2, cz));                 // (hidden) garth
    g.add(cyl(9.0, 9.4, 15.0, trim, cx, 0, cz, 8));                // octagonal chapter house
    g.add(cone(9.8, 8.0, lead, cx, 15.0, cz, 8));
    g.add(cone(1.2, 3.0, M.gold, cx, 23.0, cz, 6));
    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4 + Math.PI / 8;
      g.add(box(1.1, 15.0, 1.1, trim, cx + 8.9 * Math.cos(a), 0, cz + 8.9 * Math.sin(a)));
    }
  }

  // ---------------------------------------------------------------- Inigo Jones west portico (1630s)
  if (portico) {
    const px = L.WX - 6.5, halfW = 17;
    g.add(box(15, 2.4, halfW * 2, port, px - 1.0, 0, 0));                  // stylobate
    g.add(colonnade(8, 4.4, 1.05, 14.0, port, px - 4.5, 2.4, 0, false, 10));
    for (const s of [-1, 1]) g.add(colonnade(2, 5.0, 1.05, 14.0, port, px + 0.5, 2.4, s * (halfW - 2.2), true, 10));
    g.add(box(15, 2.6, halfW * 2, port, px - 1.0, 16.4, 0));               // entablature
    g.add(box(15.6, 1.0, halfW * 2 + 0.8, port, px - 1.0, 19.0, 0));
    // balustrade + statues
    for (const s of [-1, 1]) g.add(crenel(halfW * 2, 1.0, port, px - 1.0, 20.0, s * (halfW - 0.5), true, 1.3, 1.0, 1.1));
    g.add(crenel(15, 1.0, port, px - 8.0, 20.0, 0, false, 1.3, 1.0, 1.1));
    for (const s of [-1, 0, 1]) {
      g.add(cyl(0.55, 0.7, 3.4, port, px - 4.5, 21.3, s * 11, 6));
      g.add(dome(0.6, port, px - 4.5, 24.7, s * 11, 6, 1.2));
    }
    // Jones also re-cased the nave/transept walls: a light Portland plinth band
    g.add(box(L.EX - L.WX - 20, 3.0, L.NAVE_HW * 2 + 1.6, port, (L.WX + L.EX) / 2 - 3, 0, 0));
  }

  return g;
}
