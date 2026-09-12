// A great timber hall of Lundenwic, the Middle Saxon trading settlement in the
// Strand/Aldwych (c. AD 650-850), with two ancillary buildings.
// CONVENTION: metres, ground y=0, footprint centred on the origin, LONG axis
// along x.  "Front" = +z is the long side with the main doorway.
//
// True dimensions: hall about 25 x 10 m, walls ~3 m to the eaves, a hipped
// thatched roof rising to ~8 m; earth-fast posts and wattle-and-daub panels.
import {
  exportGLB, out, M, mat, box, cyl, cone, gableRoof, hipRoof, group, THREE, prism,
} from './_lib_london.mjs';

const g = new THREE.Group();
const daub = mat(0xd8cdb2), post = M.darkTimber, oak = M.timber, thatch = M.thatch;
const dark = M.dark;

// ---- the great hall
{
  const w = 25, d = 10, eaves = 3.2, ridge = 8.0;
  g.add(box(w, eaves, d, daub, 0, 0, 0));
  // earth-fast wall posts
  for (let i = 0; i <= 12; i++) for (const s of [-1, 1])
    g.add(box(0.42, eaves + 0.3, 0.55, post, -w / 2 + i * w / 12, 0, s * d / 2));
  for (const s of [-1, 1]) for (const bz of [-3.2, 0, 3.2])
    g.add(box(0.55, eaves + 0.3, 0.42, post, s * w / 2, 0, bz));
  g.add(box(w + 0.5, 0.35, d + 0.5, oak, 0, eaves, 0));               // wall plate
  // hipped thatched roof
  g.add(hipRoof(w + 1.6, d + 1.6, ridge - eaves - 0.35, thatch, 0, eaves + 0.35, 0, 0.55));
  // the ridge and the raking timbers of the gable hips
  g.add(box(w * 0.55, 0.35, 0.5, oak, 0, ridge - 0.35, 0));
  for (const s of [-1, 1]) {
    const r = box(0.3, 0.3, 7.0, oak, 0, 0, 0);
    r.rotation.x = 0.55; r.position.set(s * (w / 2 - 0.5), ridge - 1.8, 0);
    g.add(r);
  }
  // doorway with a small porch hood on the +z side
  g.add(box(2.6, 2.6, 0.5, dark, -2.0, 0, d / 2));
  g.add(box(3.6, 0.4, 1.6, oak, -2.0, 2.6, d / 2 + 0.6));
  for (const s of [-1, 1]) g.add(cyl(0.22, 0.26, 2.6, post, -2.0 + s * 1.6, 0, d / 2 + 1.2, 6));
  g.add(box(2.2, 2.4, 0.5, dark, 6.5, 0, -d / 2));                    // back door
  // a louvre / smoke hole in the ridge
  g.add(box(1.8, 0.9, 2.2, oak, 3.0, ridge - 0.5, 0));
  g.add(gableRoof(2.6, 2.6, 0.9, thatch, 3.0, ridge + 0.4, 0, true, 0.2));
}

// ---- two ancillary buildings (sunken-featured huts / a byre)
function hut(w, d, eaves, ridge, x, z, rot = 0) {
  const gg = new THREE.Group();
  gg.add(box(w, eaves, d, daub, 0, 0, 0));
  for (let i = 0; i <= 4; i++) for (const s of [-1, 1])
    gg.add(box(0.32, eaves + 0.25, 0.42, post, -w / 2 + i * w / 4, 0, s * d / 2));
  gg.add(box(w + 0.4, 0.3, d + 0.4, oak, 0, eaves, 0));
  gg.add(gableRoof(w + 1.0, d + 1.2, ridge - eaves - 0.3, thatch, 0, eaves + 0.3, 0, true, 0.5));
  gg.add(box(1.6, 2.0, 0.4, dark, 0, 0, d / 2));
  gg.position.set(x, 0, z); gg.rotation.y = rot;
  return gg;
}
g.add(hut(9.5, 5.5, 2.4, 5.4, -16.0, -13.0, 0.18));
g.add(hut(7.0, 4.5, 2.2, 4.8, 13.5, 13.5, -0.25));

// ---- wattle fence enclosing the yard
{
  const pts = [[-23, -20], [23, -20], [26, 18], [-24, 20]];
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i], b = pts[(i + 1) % pts.length];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const f = box(len, 1.4, 0.28, mat(0x8a7550), 0, 0, 0);
    f.position.set((a[0] + b[0]) / 2, 0.7, (a[1] + b[1]) / 2);
    f.rotation.y = -Math.atan2(b[1] - a[1], b[0] - a[0]);
    g.add(f);
  }
}

await exportGLB(g, out('saxon_hall'));
