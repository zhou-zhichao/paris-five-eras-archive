// Shared builder for Old London Bridge (Peter de Colechurch, 1176-1209).
// CONVENTION: metres, WATER SURFACE AT y=0, centred on origin, long axis x:
// -x = the Southwark (south) end with the Great Stone Gate, +x = the City end.
// "Front" = +z is the DOWNSTREAM / east side, where the Chapel of St Thomas stood.
//
// True dimensions: ~280 m between abutments, 19 pointed arches on massive
// boat-shaped starlings, roadway ~8 m wide about 10 m above the water, houses of
// 3-4 storeys (some 7) crowding both sides with fire-break gaps.
import {
  M, mat, box, cyl, cone, dome, gableRoof, hipRoof, lathe, group, THREE,
  wall, archPath, crenel, crenelRing, turret, pinnacle, ellipseRing, profileWall,
} from './_lib_london.mjs';

const LEN = 280, N = 19, PITCH = LEN / N;     // 14.74 m pier-to-pier
const X0 = -LEN / 2;
const DECK = 10;                              // roadway level above the water
const SPINE = 9;                              // masonry width (z)

function rnd(i) { const v = Math.sin(i * 127.13 + i * i * 0.37 + 1.7) * 43758.5453; return v - Math.floor(v); }

export function buildLondonBridge({ houses = true } = {}) {
  const g = new THREE.Group();
  const rag = M.rag, med = M.medieval, dark = M.dark, lead = M.lead;
  const road = mat(0x8f8776);
  const timb = M.darkTimber, plaster = M.whitewash, tile = M.tile, thatch = M.thatch;
  const wide = houses ? SPINE : 14;           // 1762: houses cleared, deck widened

  // ------------------------------------------------------------ arcade
  // One long masonry wall pierced by 19 pointed arches.
  const holes = [];
  const bigArch = !houses;                    // 1759-62: two arches thrown into one
  for (let i = 0; i < N; i++) {
    const cx = X0 + PITCH * (i + 0.5);
    if (bigArch && (i === 9 || i === 10)) continue;
    holes.push(archPath(cx, 8.4, 0.6, 5.6, 5.2, 1, 7));
  }
  if (bigArch) holes.push(archPath(X0 + PITCH * 10, 21.0, 0.6, 4.6, 6.6, 1, 10));
  // the arcade wall runs from 3 m below the water line up to the deck; hole
  // coordinates are local to that wall (y 0 = -3 m world).
  g.add(wall(LEN, DECK + 3, wide, rag, holes, 0, -3, 0));

  // pier faces / cutwaters + starlings
  for (let i = 0; i <= N; i++) {
    const px = X0 + PITCH * i;
    if (bigArch && i === 10) continue;
    // boat-shaped starling (elliptical timber-and-rubble island)
    g.add(ellipseRing(8.6, 7.0, 0, 0, 3.0, med, px, -1.4, 0, 12));
    g.add(ellipseRing(7.4, 6.0, 0, 0, 1.2, mat(0x6b6250), px, 1.6, 0, 12));
    // pointed cutwaters up the pier face
    for (const s of [-1, 1]) {
      const c = cyl(2.2, 2.6, DECK - 1, rag, px, 1.0, s * (wide / 2), 4);
      c.rotation.y = Math.PI / 4; g.add(c);
    }
  }

  // ------------------------------------------------------------ deck
  g.add(box(LEN, 1.2, wide + 1.2, rag, 0, DECK - 1.2, 0));          // cornice
  g.add(box(LEN, 0.4, houses ? 8 : 12.5, road, 0, DECK, 0));        // roadway

  if (!houses) {
    // 1762 rebuild: open deck, stone balustrade and domed pedestrian alcoves
    for (const s of [-1, 1]) {
      g.add(box(LEN, 0.5, 1.0, M.portland, 0, DECK + 0.4, s * 6.6));
      g.add(crenel(LEN, 1.0, M.portland, 0, DECK + 0.9, s * 6.6, true, 1.1, 0.35, 0.5));
      g.add(box(LEN, 0.4, 1.2, M.portland, 0, DECK + 2.0, s * 6.6));
      for (let i = 1; i < N; i += 2) {
        const px = X0 + PITCH * i;
        g.add(cyl(1.9, 2.0, 3.0, M.portland, px, DECK + 0.4, s * 7.2, 8));
        g.add(dome(2.0, M.portland, px, DECK + 3.4, s * 7.2, 8, 0.7));
      }
    }
  } else {
    // ---------------------------------------------------------- houses
    // Ranges of jettied timber houses on both sides, gable ends to the river,
    // broken by fire gaps, the gates, the chapel and Nonsuch House.
    const blocked = [[-142, -124], [-73, -59], [-3, 19], [45, 62], [131, 142],
      [-33, -27], [92, 98]];                       // gates, chapel, Nonsuch, fire breaks
    const free = x => !blocked.some(b => x > b[0] - 1 && x < b[1] + 1);
    for (const s of [-1, 1]) {
      let x = X0 + 4;
      let k = s > 0 ? 0 : 500;
      while (x < X0 + LEN - 8) {
        const w = 4.6 + rnd(k) * 2.6;
        if (free(x) && free(x + w)) {
          const st = 3 + Math.round(rnd(k + 7));           // 3 or 4 storeys
          const sh = 3.0 + rnd(k + 13) * 0.5;
          const cx = x + w / 2;
          const body = rnd(k + 3) > 0.5 ? plaster : mat(0xdcd3bc);
          for (let f = 0; f < st; f++) {
            const d = 6.2 + f * 0.55;                      // jettied storeys oversail the river
            const zc = s * (3.9 + d / 2);
            g.add(box(w, sh, d, f === 0 ? med : body, cx, DECK + f * sh, zc));
            if (f > 0) {                                    // dark frame band + window band
              g.add(box(w + 0.1, 0.35, d + 0.1, timb, cx, DECK + f * sh, zc));
              g.add(box(w * 0.66, sh * 0.42, 0.4, dark, cx, DECK + f * sh + sh * 0.3, s * (3.9 + d)));
            }
          }
          const d = 6.2 + (st - 1) * 0.55, zc = s * (3.9 + d / 2);
          // timber brackets carrying the oversailing houses out over the water
          g.add(box(w, 1.4, 5.6, timb, cx, DECK - 1.4, s * 6.4));
          for (const bo of [-w / 2 + 0.5, w / 2 - 0.5]) {
            const br = box(0.5, 0.5, 5.0, timb, 0, 0, 0);
            br.rotation.x = s * 0.62; br.position.set(cx + bo, DECK - 3.0, s * 6.0); g.add(br);
          }
          const rh = 2.2 + rnd(k + 21) * 1.2;
          g.add(gableRoof(d, w, rh, rnd(k + 5) > 0.35 ? tile : thatch, cx, DECK + st * sh, zc, false, 0.35));
          if (rnd(k + 11) > 0.62) g.add(box(0.9, 2.6, 0.9, M.brick, cx, DECK + st * sh + rh * 0.5, zc));
          x += w + 0.25;
        } else {
          x += 2.0;
        }
        k++;
      }
      // parapet where the houses leave gaps
      g.add(box(LEN, 1.1, 0.6, rag, 0, DECK, s * 4.2));
    }

    // ---------------------------------------------------------- Chapel of St Thomas
    {
      const cx = X0 + PITCH * 10;                    // on a pier, downstream side
      g.add(box(19, 22, 10, rag, cx, -2, 9.5));      // undercroft down to the starling
      g.add(box(20, 1.0, 11, med, cx, 20, 9.5));
      g.add(gableRoof(19, 10, 5.5, lead, cx, 21, 9.5, true, 0.5));
      for (const t of [-8, 8]) g.add(box(1.6, 24, 1.8, med, cx + t, -2, 14.4));
      g.add(box(12, 6.0, 0.5, dark, cx, 11, 14.6));  // big traceried window
      g.add(box(4.0, 7.0, 0.5, dark, cx, 2.5, 14.6));
      // stair turret + spirelet
      g.add(cyl(2.0, 2.2, 30, med, cx - 10.5, -2, 9.5, 8));
      g.add(cone(2.4, 8.0, lead, cx - 10.5, 28, 9.5, 8));
      g.add(cyl(1.6, 1.8, 5.0, med, cx + 5, 26.5, 9.5, 8));
      g.add(cone(2.0, 9.0, lead, cx + 5, 31.5, 9.5, 8));
    }

    // ---------------------------------------------------------- Nonsuch House (1577)
    {
      const cx = 53;
      for (let f = 0; f < 4; f++) {
        const d = 17 + f * 0.7, w = 15 + f * 0.5;
        g.add(box(w, 3.3, d, f === 0 ? med : plaster, cx, DECK + f * 3.3, 0));
        if (f > 0) {
          g.add(box(w + 0.15, 0.4, d + 0.15, timb, cx, DECK + f * 3.3, 0));
          for (const s of [-1, 1]) g.add(box(w * 0.7, 1.5, 0.4, dark, cx, DECK + f * 3.3 + 1.1, s * (d / 2)));
        }
      }
      g.add(box(6.5, 8.0, 5.0, dark, cx, DECK, 0));       // the archway through it
      const top = DECK + 4 * 3.3;
      g.add(hipRoof(16.5, 18.5, 3.4, lead, cx, top, 0, 0.45));
      for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]]) {
        const tx = cx + a[0] * 7.6, tz = a[1] * 8.6;
        g.add(cyl(2.0, 2.0, 5.0, plaster, tx, top - 1.0, tz, 8));
        g.add(dome(2.2, lead, tx, top + 4.0, tz, 8, 1.25));
        g.add(cone(0.5, 2.4, M.gold, tx, top + 6.6, tz, 6));
      }
    }

    // ---------------------------------------------------------- Drawbridge Tower
    {
      const cx = X0 + PITCH * 5;
      g.add(box(11, 22, 15, rag, cx, DECK - 1.2, 0));
      g.add(box(5.0, 9.0, 16, dark, cx, DECK, 0));                   // gate passage
      for (const s of [-1, 1]) g.add(box(11.8, 1.4, 1.4, med, cx, DECK + 10, s * 7.9));
      g.add(box(12.4, 1.3, 16.6, med, cx, DECK + 20.8, 0));
      g.add(crenelRing(12.4, 16.6, 0.9, med, cx, DECK + 22.1, 0, 1.5, 1.5, 1.4));
      for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
        g.add(turret(1.7, 6.0, med, med, cx + a[0] * 6.0, DECK + 22.1, a[1] * 8.0, 8, 4.0));
      // the drawbridge arch just north of it, with a raisable timber leaf
      const lf = box(9.0, 0.6, 7.0, timb, 0, 0, 0);
      lf.rotation.z = -0.62; lf.position.set(cx + 10.5, DECK + 3.0, 0); g.add(lf);
    }

    // ---------------------------------------------------------- Great Stone Gate (Southwark, -x)
    {
      const cx = X0 + 6;
      g.add(box(14, 26, 17, rag, cx, DECK - 1.2, 0));
      g.add(box(5.4, 10.0, 18, dark, cx, DECK, 0));
      g.add(box(15.0, 1.4, 18.0, med, cx, DECK + 24.6, 0));
      g.add(crenelRing(15.0, 18.0, 1.0, med, cx, DECK + 26.0, 0, 1.7, 1.7, 1.5));
      for (const a of [[-1, -1], [-1, 1], [1, -1], [1, 1]])
        g.add(turret(2.1, 7.5, med, med, cx + a[0] * 7.5, DECK + 26.0, a[1] * 9.0, 8, 5.0));
      // the traitors' heads on poles over the gate
      for (let i = 0; i < 7; i++) {
        const px = cx - 6 + i * 2.0;
        g.add(box(0.16, 4.0, 0.16, timb, px, DECK + 27.7, 0));
        g.add(dome(0.3, mat(0x5a4a3a), px, DECK + 31.6, 0, 6, 1.3));
      }
    }
  }

  // ------------------------------------------------------------ abutments
  for (const s of [-1, 1]) g.add(box(14, DECK + 1.4, wide + 12, med, s * (LEN / 2 + 6), -1.5, 0));
  return g;
}
