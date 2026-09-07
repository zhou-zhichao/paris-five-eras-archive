// Shared builder for Westminster Abbey (Henry III's church of 1245 onwards, with
// Henry VII's Lady Chapel of 1503-19).
// CONVENTION: metres, ground y=0, centred on the origin, LONG axis along x
// (west front at -x, Henry VII chapel at +x).  "Front" = +z is the SOUTH side,
// where the cloister and chapter house stand.
//
// True dimensions: 156 m long, nave + aisles 26 m wide, vault 31 m / roof ridge
// ~45 m, transepts 62 m across, Hawksmoor's west towers (1745) 69 m.
import {
  M, mat, box, cyl, cone, dome, gableRoof, hipRoof, lathe, group, THREE,
  wall, archPath, crenel, crenelRing, colonnade, pinnacle, turret,
  lancets, rose, profileWall,
} from './_lib_london.mjs';

export function buildWestminsterAbbey({ westTowers = true } = {}) {
  const g = new THREE.Group();
  const stone = M.pale, trim = M.portland, lead = M.lead, dark = M.dark;

  const WX = -78, EX = 78;
  const HW = 13, CW = 6.5;                 // half width over aisles / central vessel
  const AE = 15, AT = 20.5;                // aisle eaves / aisle ridge
  const CE = 36, RIDGE = 45;               // clerestory eaves / nave ridge
  const TR = 31, TD = 10;                  // transept half length / half depth
  const CX = -8;                           // crossing centre

  // ------------------------------------------------------------- main vessel
  function body(x0, x1, bays) {
    const gg = new THREE.Group();
    const len = x1 - x0, cx = (x0 + x1) / 2, ad = HW - CW;
    for (const s of [-1, 1]) {
      const az = s * (HW + CW) / 2;
      gg.add(box(len, AE, ad, stone, cx, 0, az));
      const slab = box(len, 0.7, Math.hypot(ad, AT - AE) * 1.05, lead, 0, 0, 0);
      slab.rotation.x = -s * Math.atan2(AT - AE, ad);
      slab.position.set(cx, AE + (AT - AE) / 2, az);
      gg.add(slab);
      gg.add(lancets(bays, len / bays, 3.2, 7.0, 0.5, dark, cx, 5.5, s * HW, true));
      // aisle buttress piers + flying buttresses to the clerestory
      for (let i = 0; i <= bays; i++) {
        const bx = x0 + i * len / bays;
        gg.add(box(1.8, AE + 3.0, 3.6, trim, bx, 0, s * (HW + 1.6)));
        gg.add(pinnacle(1.5, 7.0, trim, bx, AE + 3.0, s * (HW + 1.6)));
        if (i > 0 && i < bays) {
          const reach = HW + 1.6 - CW, topY = CE - 5;
          const strut = box(0.9, 1.4, Math.hypot(reach, topY - 15.5), trim, 0, 0, 0);
          strut.rotation.x = -s * Math.atan2(topY - 15.5, reach);
          strut.position.set(bx, 15.5 + (topY - 15.5) / 2, s * (CW + reach / 2));
          gg.add(strut);
        }
      }
    }
    gg.add(box(len, CE, CW * 2, stone, cx, 0, 0));
    for (const s of [-1, 1]) gg.add(lancets(bays, len / bays, 3.0, 6.5, 0.45, dark, cx, CE - 9.5, s * CW, true));
    gg.add(box(len + 0.6, 1.0, CW * 2 + 1.4, trim, cx, CE - 0.9, 0));
    gg.add(gableRoof(len, CW * 2, RIDGE - CE, lead, cx, CE, 0, true, 0.6));
    return gg;
  }
  g.add(body(WX + 8, CX - TD, 11));              // nave
  g.add(body(CX + TD, 34, 7));                   // choir & presbytery

  // ------------------------------------------------------------- apse / chevet
  {
    const ax = 34;
    g.add(cyl(CW + 0.4, CW + 0.4, CE, stone, ax + 4, 0, 0, 12));
    g.add(cone(CW + 1.6, 9.0, lead, ax + 4, CE, 0, 12));
    g.add(cyl(HW, HW, AE, stone, ax + 4, 0, 0, 12));
    g.add(cone(HW + 1.0, 5.0, lead, ax + 4, AE, 0, 12));
    for (let i = 0; i < 5; i++) {                  // radiating chapels
      const a = -Math.PI / 2 + (i + 0.5) * Math.PI / 5;
      const rx = ax + 4 + (HW + 3.5) * Math.sin(a), rz = (HW + 3.5) * Math.cos(a);
      g.add(cyl(4.0, 4.0, 11, stone, rx, 0, rz, 8));
      g.add(cone(4.6, 3.5, lead, rx, 11, rz, 8));
    }
  }

  // ------------------------------------------------------------- transepts
  g.add(box(TD * 2, CE, TR * 2, stone, CX, 0, 0));
  g.add(box(TD * 2 + 0.6, 1.0, TR * 2 + 1.4, trim, CX, CE - 0.9, 0));
  g.add(gableRoof(TR * 2, TD * 2, RIDGE - CE, lead, CX, CE, 0, false, 0.6));
  for (const s of [-1, 1]) {
    // transept aisles
    for (const sx of [-1, 1]) {
      const az = s * (HW + (TR - HW) / 2), armLen = TR - HW;
      g.add(box(6, AE, armLen, stone, CX + sx * (TD + 3), 0, az));
      const slab = box(6, 0.7, 7.5, lead, 0, 0, 0);
      slab.rotation.z = sx * 0.58;
      slab.position.set(CX + sx * (TD + 3), AE + 2.2, az); g.add(slab);
      for (const t of [0.3, 0.72]) {
        g.add(box(1.8, AE + 3.0, 3.6, trim, CX + sx * (TD + 4.6), 0, s * (HW + t * (TR - HW))));
        g.add(pinnacle(1.5, 7.0, trim, CX + sx * (TD + 4.6), AE + 3.0, s * (HW + t * (TR - HW))));
      }
    }
    // gable end with the great rose window
    const ez = s * TR;
    g.add(rose(6.4, 1.0, trim, dark, CX, 27, ez + s * 0.4, 0, 12));
    g.add(box(13.0, 9.0, 0.6, dark, CX, 9, ez + s * 0.3));
    for (const sx of [-1, 1]) g.add(turret(2.2, CE + 4, trim, trim, CX + sx * (TD + 0.8), 0, ez, 8, 5.0));
  }
  // Solomon's Porch on the north transept
  g.add(box(13, 13, 8, trim, CX, 0, -TR - 4));
  g.add(gableRoof(13, 8, 6.0, lead, CX, 13, -TR - 4, true, 0.5));
  for (const s of [-1, 1]) g.add(pinnacle(1.4, 6.0, trim, CX + s * 6.0, 13, -TR - 4));
  g.add(box(5.5, 8.0, 0.8, dark, CX, 0, -TR - 8.1));

  // ------------------------------------------------------------- central lantern
  {
    const tw = 19;
    g.add(box(tw, 47, tw, stone, CX, 0, 0));
    for (const s of [-1, 1]) {
      g.add(box(11, 8.0, 0.6, dark, CX, 34, s * (tw / 2 + 0.1)));
      g.add(box(0.6, 8.0, 11, dark, CX + s * (tw / 2 + 0.1), 34, 0));
    }
    for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
      g.add(box(3.0, 47, 3.0, trim, CX + a[0] * (tw / 2 - 0.3), 0, a[1] * (tw / 2 - 0.3)));
    g.add(box(tw + 1.8, 1.4, tw + 1.8, trim, CX, 47, 0));
    g.add(crenelRing(tw + 1.8, tw + 1.8, 0.9, trim, CX, 48.4, 0, 1.5, 1.6, 1.4));
    for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
      g.add(pinnacle(1.7, 8.0, trim, CX + a[0] * (tw / 2 + 0.4), 48.4, a[1] * (tw / 2 + 0.4)));
    g.add(hipRoof(tw, tw, 5.0, lead, CX, 48.4, 0, 0.15));
  }

  // ------------------------------------------------------------- Henry VII Lady Chapel (east)
  {
    const x0 = 52, x1 = 68, cw = 9.0, aw = 13.5;
    const cx = (x0 + x1 - 8) / 2;
    g.add(box(x1 - x0 - 8, 26, cw * 2, stone, cx, 0, 0));
    g.add(box(x1 - x0 - 8, 17, aw * 2, stone, cx, 0, 0));            // aisles/chapel bays
    g.add(box(x1 - x0 - 7.4, 1.0, aw * 2 + 1.0, trim, cx, 17, 0));
    g.add(box(x1 - x0 - 7.4, 1.0, cw * 2 + 1.0, trim, cx, 26, 0));
    g.add(hipRoof(x1 - x0 - 8, cw * 2, 4.0, lead, cx, 27, 0, 0.7));
    // polygonal apsidal east end
    g.add(cyl(cw, cw, 26, stone, x1 - 4, 0, 0, 10));
    g.add(cyl(aw, aw, 17, stone, x1 - 4, 0, 0, 10));
    g.add(cone(cw + 1.2, 5.0, lead, x1 - 4, 27, 0, 10));
    // big traceried windows all round + the famous octagonal turrets
    for (const s of [-1, 1]) {
      g.add(box((x1 - x0 - 12), 8.0, 0.5, dark, cx, 6.5, s * aw));
      g.add(box((x1 - x0 - 12), 6.0, 0.5, dark, cx, 18.5, s * cw));
    }
    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4;
      const tx = x1 - 4 + (aw + 0.6) * Math.cos(a), tz = (aw + 0.6) * Math.sin(a);
      if (Math.cos(a) < -0.3) continue;
      g.add(cyl(2.1, 2.3, 24, trim, tx, 0, tz, 8));
      g.add(lathe([[2.4, 0], [2.6, 1.2], [1.7, 3.4], [0.7, 5.2], [0.2, 6.4]], trim, tx, 24, tz, 8));
    }
    for (const s of [-1, 1]) for (const bx of [x0 + 2, x0 + 12, x0 + 22]) {
      g.add(cyl(2.1, 2.3, 24, trim, bx, 0, s * (aw + 0.6), 8));
      g.add(lathe([[2.4, 0], [2.6, 1.2], [1.7, 3.4], [0.7, 5.2], [0.2, 6.4]], trim, bx, 24, s * (aw + 0.6), 8));
    }
  }

  // ------------------------------------------------------------- west front
  {
    const tw = 11.5, tz = 8.6;
    const th = westTowers ? 69 : 30;
    g.add(box(10, CE, HW * 2, stone, WX + 5, 0, 0));
    g.add(profileWall([[-CW, 0], [CW, 0], [0, RIDGE - CE]], 10, stone, WX + 5, CE, 0, Math.PI / 2));
    g.add(box(0.8, 14.0, 9.5, dark, WX + 0.1, 14, 0));            // great west window
    g.add(box(0.8, 8.0, 4.5, dark, WX + 0.1, 0, 0));
    for (const s of [-1, 1]) {
      g.add(box(tw, th, tw, stone, WX + tw / 2 - 1.5, 0, s * tz));
      for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])          // corner buttress strips
        g.add(box(2.6, th, 2.6, trim, WX + tw / 2 - 1.5 + a[0] * (tw / 2 - 0.4), 0, s * tz + a[1] * (tw / 2 - 0.4)));
      // window/belfry bands
      const bands = westTowers ? [0.30, 0.52, 0.70, 0.86] : [0.4, 0.72];
      for (const f of bands) {
        g.add(box(0.8, th * 0.10, tw * 0.5, dark, WX + 0.1, th * f, s * tz));
        for (const sz of [-1, 1]) g.add(box(tw * 0.5, th * 0.10, 0.8, dark, WX + tw / 2 - 1.5, th * f, s * tz + sz * (tw / 2)));
      }
      g.add(box(tw + 1.6, 1.3, tw + 1.6, trim, WX + tw / 2 - 1.5, th, s * tz));
      g.add(crenelRing(tw + 1.6, tw + 1.6, 0.9, trim, WX + tw / 2 - 1.5, th + 1.3, s * tz, 1.4, 1.5, 1.3));
      for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
        g.add(pinnacle(1.3, westTowers ? 7.5 : 5.5, trim,
          WX + tw / 2 - 1.5 + a[0] * (tw / 2 + 0.3), th + 1.3, s * tz + a[1] * (tw / 2 + 0.3)));
      if (westTowers) {
        // Hawksmoor's tall belfry stage reads as a slightly set-back upper block
        g.add(box(tw - 1.6, 9.0, tw - 1.6, stone, WX + tw / 2 - 1.5, th - 22, s * tz));
      }
    }
  }

  // ------------------------------------------------------------- cloister & chapter house (south, +z)
  {
    const clx = -30, clz = 30, sz = 33;
    for (const [ox, oz, w, d] of [[0, -sz / 2 + 4, sz, 8], [0, sz / 2 - 4, sz, 8], [-sz / 2 + 4, 0, 8, sz - 16], [sz / 2 - 4, 0, 8, sz - 16]]) {
      g.add(box(w, 9.5, d, stone, clx + ox, 0, clz + oz));
      g.add(gableRoof(Math.max(w, d), Math.min(w, d), 3.4, lead, clx + ox, 9.5, clz + oz, w >= d, 0.5));
    }
    g.add(box(sz - 16, 0.4, sz - 16, M.grass, clx, 0.2, clz));
    // octagonal chapter house on a vaulted undercroft
    const chx = clx + 26, chz = clz + 10;
    g.add(cyl(11.0, 11.4, 19.0, stone, chx, 0, chz, 8));
    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4 + Math.PI / 8;
      g.add(box(1.6, 21.0, 1.6, trim, chx + 10.9 * Math.cos(a), 0, chz + 10.9 * Math.sin(a)));
      g.add(pinnacle(1.2, 5.0, trim, chx + 10.9 * Math.cos(a), 21.0, chz + 10.9 * Math.sin(a)));
      const b = box(6.5, 8.5, 0.5, dark, chx + 10.2 * Math.cos(a - Math.PI / 8), 8.0, chz + 10.2 * Math.sin(a - Math.PI / 8));
      b.rotation.y = Math.PI / 2 - (a - Math.PI / 8); g.add(b);
    }
    g.add(cone(12.2, 9.0, lead, chx, 19.0, chz, 8));
    g.add(cone(1.2, 3.5, M.gold, chx, 28.0, chz, 6));
  }

  return g;
}
