// Shared body for the London church models (Wren / Gibbs / Hawksmoor).
// CONVENTION for all of these: liturgical long axis along X, WEST front (portico / tower)
// at -X, east end at +X; the long south side faces +Z.  Ground y=0, footprint centred on x,z.
import { THREE, box, cyl, cone, gableRoof, P, M, column, pediment, balustrade } from './_lib_wren_edwardian.mjs';
export * from './_lib_wren_edwardian.mjs';

// Rectangular aisled church body with a parapet, round-headed windows and a lead roof.
// x0 = west end of the body, L = length, W = width, H = eaves height.
export function churchBody(g, x0, L, W, H, opts = {}) {
  const st = M(opts.stone || P.stone), pale = M(P.pale), dk = M(P.dstone),
    lead = M(P.lead), dark = M(0x4a463d);
  const xc = x0 + L / 2;
  g.add(box(L + 2, 1.0, W + 2, dk, xc, 0, 0));
  g.add(box(L, H, W, st, xc, 1.0, 0));
  g.add(box(L + 1.2, 1.2, W + 1.2, pale, xc, 1.0 + H, 0));
  g.add(balustrade(L + 1.2, W + 1.2, 1.6, pale, xc, 2.2 + H, 0));
  g.add(box(L - 3, 0.8, W - 3, lead, xc, 2.2 + H, 0));
  g.add(gableRoof(L - 3, W - 5, 2.6, lead, xc, 3.0 + H, 0, true, 0));
  const n = opts.bays || Math.max(4, Math.round(L / 6));
  for (let i = 0; i < n; i++) {
    const x = x0 + L / (2 * n) + i * L / n;
    for (const zs of [1, -1]) {
      // round-headed window: a dark box with a semicircular head
      g.add(box(2.6, 5.0, 0.6, dark, x, 4.5, zs * (W / 2 + 0.1)));
      const hd = new THREE.Mesh(new THREE.CylinderGeometry(1.3, 1.3, 0.6, 12, 1, false, 0, Math.PI), dark);
      hd.rotation.x = zs > 0 ? -Math.PI / 2 : Math.PI / 2;
      hd.position.set(x, 9.5, zs * (W / 2 + 0.1));
      g.add(hd);
      g.add(box(1.4, H - 1, 1.0, pale, x + L / (2 * n), 1.0, zs * (W / 2 + 0.2)));
    }
  }
  // east end
  g.add(box(1.2, H, W, pale, x0 + L, 1.0, 0));
  return 2.2 + H;
}
