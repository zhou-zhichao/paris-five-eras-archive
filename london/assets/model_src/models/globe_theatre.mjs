// The Globe playhouse, Bankside, 1599 (rebuilt 1614): a twenty-sided
// timber-framed amphitheatre with three galleries round an open yard.
// CONVENTION: metres, ground y=0, footprint centred on the origin.  "Front" = +z
// is the main entrance; the tiring house and stage stand opposite, at -x.
//
// True dimensions: ~30 m across the twenty sides, yard ~21 m, three galleries
// about 11 m to the eaves, thatched ring roof, stage cover ("the heavens").
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, hipRoof, lathe, group, THREE,
} from './_lib_london.mjs';

const g = new THREE.Group();
const plaster = M.whitewash, timb = M.darkTimber, thatch = M.thatch, dark = M.dark;
const oak = M.timber, tile = M.tile;
const N = 20, RO = 15.0, RI = 10.4, H = 11.0;

// ---- outer polygonal wall, storey by storey, with its timber framing
for (let f = 0; f < 3; f++) {
  const y = f * (H / 3), ro = RO - f * 0.25;
  const seg = 2 * RO * Math.sin(Math.PI / N) + 0.15;
  for (let i = 0; i < N; i++) {
    const a = (i + 0.5) * Math.PI * 2 / N;
    const cx = Math.cos(a), cz = Math.sin(a);
    const p = box(seg, H / 3, 0.5, f === 0 ? mat(0xd9cfb6) : plaster, ro * cx, y, ro * cz);
    p.rotation.y = Math.PI / 2 - a; g.add(p);
    const r1 = box(seg, 0.42, 0.62, timb, ro * cx, y, ro * cz); r1.rotation.y = Math.PI / 2 - a; g.add(r1);
    if (f === 2) { const r2 = box(seg, 0.42, 0.62, timb, ro * cx, y + H / 3 - 0.42, ro * cz); r2.rotation.y = Math.PI / 2 - a; g.add(r2); }
    if (f > 0) {
      const w = box(seg * 0.62, H / 3 * 0.5, 0.35, dark, (ro - 0.2) * cx, y + 0.9, (ro - 0.2) * cz);
      w.rotation.y = Math.PI / 2 - a; g.add(w);
    }
  }
  for (let i = 0; i < N; i++) {
    const a = i * Math.PI * 2 / N;
    const post = box(0.55, H / 3, 0.7, timb, (ro + 0.1) * Math.cos(a), y, (ro + 0.1) * Math.sin(a));
    post.rotation.y = Math.PI / 2 - a; g.add(post);
  }
}
// ---- inner gallery wall facing the yard
for (let i = 0; i < N; i++) {
  const a = (i + 0.5) * Math.PI * 2 / N;
  const seg = 2 * RI * Math.sin(Math.PI / N) + 0.15;
  const p = box(seg, H, 0.45, oak, RI * Math.cos(a), 0, RI * Math.sin(a));
  p.rotation.y = Math.PI / 2 - a; g.add(p);
  for (let f = 1; f < 3; f++) {
    const r = box(seg, 0.4, 0.6, timb, RI * Math.cos(a), f * H / 3, RI * Math.sin(a));
    r.rotation.y = Math.PI / 2 - a; g.add(r);
  }
}
g.add(cyl(RI - 0.3, RI - 0.3, 0.3, mat(0x8a7f68), 0, 0, 0, N));      // the yard

// ---- thatched ring roof, sloping down from the outer wall in to the yard
g.add(lathe([[RI - 0.6, 0.9], [RO + 1.4, 3.1], [RO + 1.5, 2.2], [RI - 0.6, 0.0]], thatch, 0, H, 0, N));
g.add(lathe([[RI - 0.75, 0.9], [RI - 0.75, 0.0], [RI - 0.2, 0.0], [RI - 0.2, 0.9]], thatch, 0, H, 0, N));

// ---- tiring house, stage and the heavens (at -x, inside the ring)
{
  const bx = -12.0;
  g.add(box(4.2, H + 2.0, 13.0, plaster, bx, 0, 0));                       // tiring house
  for (let f = 1; f < 4; f++) g.add(box(4.5, 0.45, 13.2, timb, bx, f * H / 3, 0));
  for (const o of [-4.0, 4.0]) g.add(box(0.5, 5.0, 2.6, dark, bx + 2.1, 0, o));   // stage doors
  g.add(box(0.5, 3.0, 6.5, dark, bx + 2.1, H / 3 + 0.6, 0));               // the gallery over the stage
  g.add(box(8.6, 1.5, 12.0, oak, bx + 6.2, 0, 0));                         // the thrust stage
  g.add(box(9.6, 0.9, 13.0, mat(0x3a4a6a), bx + 6.2, 8.2, 0));             // "the heavens"
  for (const o of [-5.2, 5.2]) g.add(cyl(0.42, 0.48, 8.2, oak, bx + 10.0, 1.5, o, 8));
  g.add(gableRoof(13.0, 9.8, 2.8, thatch, bx + 6.2, 9.1, 0, false, 0.4));
  g.add(box(4.0, 4.2, 6.5, plaster, bx, H + 2.0, 0));                      // the hut
  g.add(gableRoof(6.5, 4.0, 2.0, thatch, bx, H + 6.2, 0, false, 0.35));
  g.add(box(0.2, 4.5, 0.2, oak, bx, H + 8.2, 0));
  g.add(box(0.1, 1.8, 3.0, mat(0xe8e2d0), bx, H + 11.0, 1.5));             // the flag
}

// ---- main entrance on +z
g.add(box(4.4, 6.0, 3.0, plaster, 0, 0, RO + 1.2));
g.add(gableRoof(4.4, 3.0, 1.8, tile, 0, 6.0, RO + 1.2, true, 0.3));
g.add(box(2.2, 4.2, 0.5, dark, 0, 0, RO + 2.6));
for (const s of [-1, 1]) g.add(box(0.4, 6.0, 3.2, timb, s * 2.2, 0, RO + 1.2));

await exportGLB(g, out('globe_theatre'));
