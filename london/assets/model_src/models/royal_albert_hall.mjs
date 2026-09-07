// Royal Albert Hall, Fowke & Scott, 1871.  Red brick and buff terracotta, elliptical.
// Orientation: the long axis of the ellipse runs along X (83 m); minor axis 72 m along Z.
// The SOUTH porch (main entrance, towards the Albert Memorial) faces +Z.  Ground y=0.
// Wall/frieze cornice ~ 30 m, glass-and-iron elliptical dome to 41 m.
// Also exports albert_memorial.glb: Scott's Gothic canopy, 54 m, steps ~ 30 x 30 m.
import { exportGLB, box, cyl, cone, dome, lathe, gableRoof, hipRoof, THREE,
  P, M, column, ringColonnade, pediment, pinnacle, balustrade, steps, OUT } from './_lib_wren_edwardian.mjs';

// =========================================================== ROYAL ALBERT HALL
{
  const g = new THREE.Group();
  const tc = M(P.vred), tcd = M(0x8d5040), buff = M(0xc9a071), pale = M(P.pale),
    glass = M(P.glassroof), iron = M(P.iron), dark = M(0x4a3c33), slate = M(P.slate);

  const A = 41.5, B = 36;              // semi-axes  (83 x 72 m)
  const H = 26;                        // main wall height to the frieze
  const N = 32;                        // ellipse facets

  function ell(rx, rz, h, m, y, seg = N) {
    const c = cyl(1, 1, h, m, 0, y, 0, seg);
    c.scale.set(rx, 1, rz);
    return c;
  }
  // plinth & steps
  g.add(ell(A + 5, B + 5, 2.0, M(P.dstone), 0));
  g.add(ell(A + 3, B + 3, 1.4, M(P.dstone), 2.0));

  // main elliptical drum
  g.add(ell(A, B, H, tc, 3.4));
  // pilaster strips
  for (let i = 0; i < N; i++) {
    const a = i / N * Math.PI * 2;
    const px = Math.cos(a) * A, pz = Math.sin(a) * B;
    const p = box(2.4, H, 1.6, tcd, px, 3.4, pz);
    p.rotation.y = -Math.atan2(pz * A * A, px * B * B);
    g.add(p);
  }
  // two tiers of arched window bands + the terracotta mosaic frieze
  for (const [y, hh, m] of [[9, 6.5, dark], [17.5, 5.5, dark], [24.0, 2.4, buff]]) {
    for (let i = 0; i < N; i++) {
      const a = (i + 0.5) / N * Math.PI * 2;
      const px = Math.cos(a) * (A + 0.2), pz = Math.sin(a) * (B + 0.2);
      const p = box(4.2, hh, 1.0, m, px, y, pz);
      p.rotation.y = -Math.atan2(pz * A * A, px * B * B);
      g.add(p);
    }
  }
  g.add(ell(A + 1.2, B + 1.2, 2.2, buff, 3.4 + H));        // big projecting cornice
  g.add(ell(A + 0.4, B + 0.4, 2.0, tc, 5.6 + H));          // parapet -> 33.6

  // the glass-and-iron elliptical dome (springs behind the parapet, crown 41 m)
  {
    const prof = [];
    const steps2 = 8, R0 = 0.86, HH = 12.5;
    for (let i = 0; i <= steps2; i++) {
      const t = i / steps2;
      prof.push([R0 * Math.cos(t * Math.PI / 2), HH * Math.sin(t * Math.PI / 2)]);
    }
    const d = lathe(prof, glass, 0, 28.5, 0, N);
    d.scale.set(A, 1, B);
    g.add(d);
    // radial iron ribs
    for (let i = 0; i < 16; i++) {
      const a = i / 16 * Math.PI * 2;
      for (let k = 0; k < prof.length - 1; k++) {
        const r0 = prof[k], r1 = prof[k + 1];
        const p0 = [r0[0] * A * Math.cos(a), 28.5 + r0[1], r0[0] * B * Math.sin(a)];
        const p1 = [r1[0] * A * Math.cos(a), 28.5 + r1[1], r1[0] * B * Math.sin(a)];
        const len = Math.hypot(p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]);
        const b = box(len, 0.6, 0.7, iron, (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 0.3, (p0[2] + p1[2]) / 2);
        b.rotation.y = -a;
        b.rotation.z = Math.atan2(p1[1] - p0[1], Math.hypot(p1[0] - p0[0], p1[2] - p0[2]));
        g.add(b);
      }
    }
    g.add(cyl(3.2, 3.6, 1.6, iron, 0, 40.0, 0, 16));       // crown lantern
  }

  // four porches (N/S/E/W); the south one (+z) is the main entrance
  for (const [dx, dz, w] of [[0, 1, 24], [0, -1, 22], [1, 0, 18], [-1, 0, 18]]) {
    const px = dx * (A - 2), pz = dz * (B - 2);
    const pr = new THREE.Group();
    pr.add(box(w, 15, 12, tc, 0, 3.4, 0));
    pr.add(box(w + 1.6, 1.6, 13.6, buff, 0, 18.4, 0));
    pr.add(pediment(w + 1.6, w * 0.16, 13.6, buff, 0, 20.0, 0));
    for (let i = 0; i < 4; i++) pr.add(column(1.0, 11.0, buff, (i - 1.5) * (w / 4.6), 3.4, 6.4, 8));
    pr.add(box(w - 4, 9, 1.0, dark, 0, 5.0, 6.0));
    pr.rotation.y = dx ? -dx * Math.PI / 2 : (dz > 0 ? 0 : Math.PI);
    pr.position.set(px * 0.96, 0, pz * 0.96);
    g.add(pr);
  }
  await exportGLB(g, OUT + 'royal_albert_hall.glb');
}

// =========================================================== ALBERT MEMORIAL
{
  const g = new THREE.Group();
  const gran = M(0x7a6a5c), pale = M(P.pale), gold = M(P.gold), lead = M(P.lead),
    dk = M(P.dstone), marble = M(0xe6e0d2), slate = M(P.slate);

  // stepped granite base, ~ 30 x 30 m
  for (let i = 0; i < 5; i++) g.add(box(30 - i * 2.6, 0.85, 30 - i * 2.6, gran, 0, i * 0.85, 0));
  // corner marble groups
  for (const [sx, sz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    g.add(box(5.0, 3.2, 5.0, marble, sx * 11.0, 4.25, sz * 11.0));
  // podium with the Frieze of Parnassus
  g.add(box(17, 3.4, 17, pale, 0, 4.25, 0));
  g.add(box(15.5, 2.4, 15.5, marble, 0, 7.65, 0));
  g.add(box(16.6, 0.9, 16.6, pale, 0, 10.05, 0));
  // four clustered piers carrying the canopy
  for (const [sx, sz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) {
    const px = sx * 5.6, pz = sz * 5.6;
    g.add(box(3.4, 15, 3.4, pale, px, 10.95, pz));
    for (const [ox, oz] of [[1, 0], [-1, 0], [0, 1], [0, -1]])
      g.add(cyl(0.62, 0.66, 13.5, M(0x6f5a4a), px + ox * 1.9, 11.4, pz + oz * 1.9, 8));
    g.add(pinnacle(1.5, 8.0, pale, px, 25.95, pz, 6));
  }
  // seated gilt Albert under the canopy
  g.add(box(3.2, 1.2, 3.2, pale, 0, 10.95, 0));
  g.add(box(2.2, 4.6, 2.0, gold, 0, 12.15, 0));
  // the canopy: gables and vault
  g.add(box(16, 2.4, 16, pale, 0, 25.95, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const pd = new THREE.Group();
    pd.add(box(13.5, 9.0, 1.4, pale, 0, 0, 0));
    pd.add(cone(7.4, 7.5, pale, 0, 9.0, 0, 3));
    pd.rotation.y = dx ? dx * Math.PI / 2 : (dz > 0 ? 0 : Math.PI);
    pd.position.set(dx * 7.3, 28.35, dz * 7.3);
    g.add(pd);
  }
  g.add(box(13, 3.0, 13, pale, 0, 37.5, 0));
  // the spire
  g.add(cyl(5.6, 6.6, 5.0, pale, 0, 40.5, 0, 8));
  for (let i = 0; i < 8; i++) {
    const a = i / 8 * Math.PI * 2;
    g.add(pinnacle(0.9, 5.0, pale, Math.cos(a) * 6.2, 45.5, Math.sin(a) * 6.2, 6));
  }
  g.add(cone(5.2, 11.0, lead, 0, 45.5, 0, 8));
  g.add(cyl(0.9, 1.2, 1.6, gold, 0, 50.5, 0, 8));
  g.add(cone(1.2, 2.0, gold, 0, 51.4, 0, 8));
  g.add(box(0.35, 2.4, 0.35, gold, 0, 51.4, 0));
  g.add(box(1.5, 0.35, 0.35, gold, 0, 52.6, 0));

  await exportGLB(g, OUT + 'albert_memorial.glb');
}
