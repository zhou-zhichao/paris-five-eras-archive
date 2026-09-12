// The Natural History Museum, Alfred Waterhouse 1873-81.  Romanesque, buff and blue-grey
// terracotta.  ~200 m Cromwell Road front with twin towers ~ 60 m flanking a great
// round-arched central entrance; the main hall and galleries run back behind it.
// Orientation: long axis along X, the FRONT faces +Z.  Ground y=0, centred on the origin.
import { exportGLB, box, cyl, cone, lathe, gableRoof, hipRoof, THREE,
  P, M, pinnacle, openWall, arcade, balustrade, OUT } from './_lib_wren_edwardian.mjs';
const g = new THREE.Group();
const buff = M(0xc9ac82), blue = M(0x8f9a97), buffd = M(0xb08f66), pale = M(P.pale),
  slate = M(P.slate), lead = M(P.lead), dark = M(0x413a30), glass = M(P.glassroof);

const W = 200, FD = 22, H = 24, FZ = 46;    // front range depth / cornice height / front plane

// ---------------------------------------------------------------- front range
g.add(box(W + 4, 1.6, FD + 4, buffd, 0, 0, FZ - FD / 2));
g.add(box(W, H, FD, buff, 0, 1.6, FZ - FD / 2));
g.add(box(W + 1.6, 1.6, FD + 1.6, blue, 0, 1.6 + H, FZ - FD / 2));
g.add(gableRoof(W, FD, 7.5, slate, 0, 3.2 + H, FZ - FD / 2, true, 0.5));
// horizontal blue-grey banding (the striped terracotta)
for (let s = 0; s < 6; s++) g.add(box(W + 0.6, 0.8, FD + 0.8, blue, 0, 3.5 + s * 4.0, FZ - FD / 2));
// two tiers of round-arched windows
for (const zz of [FZ + 0.1, FZ - FD - 0.1]) {
  for (let i = 0; i < 44; i++) {
    const x = -W / 2 + 4 + i * (W - 8) / 43;
    if (Math.abs(x) < 22) continue;
    g.add(box(2.2, 5.0, 0.6, dark, x, 4.0, zz));
    const h1 = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.1, 0.6, 10, 1, false, 0, Math.PI), dark);
    h1.rotation.x = zz > 0 ? -Math.PI / 2 : Math.PI / 2; h1.position.set(x, 9.0, zz); g.add(h1);
    g.add(box(2.0, 4.4, 0.6, dark, x, 13.5, zz));
    g.add(box(1.4, H - 1, 0.9, buffd, x + (W - 8) / 86, 1.6, zz));
  }
}
// small turrets punctuating the front
for (let i = 0; i < 9; i++) {
  const x = -W / 2 + 10 + i * (W - 20) / 8;
  if (Math.abs(x) < 24) continue;
  g.add(cyl(2.2, 2.4, H + 8, buff, x, 1.6, FZ + 1.0, 8));
  g.add(cyl(2.8, 2.8, 0.9, blue, x, 1.6 + H + 8, FZ + 1.0, 8));
  g.add(cone(2.7, 6.0, slate, x, 2.5 + H + 8, FZ + 1.0, 8));
}

// ---------------------------------------------------------------- galleries running back (-z)
for (const sx of [-1, 1]) {
  g.add(box(24, 20, 78, buff, sx * 66, 1.6, FZ - FD - 39));
  g.add(box(25.4, 1.4, 79.4, blue, sx * 66, 21.6, FZ - FD - 39));
  g.add(gableRoof(24, 78, 6.0, slate, sx * 66, 23.0, FZ - FD - 39, false, 0.4));
}
// the great central hall behind the entrance
g.add(box(34, 26, 90, buff, 0, 1.6, FZ - FD - 45));
g.add(box(35.4, 1.4, 91.4, blue, 0, 27.6, FZ - FD - 45));
g.add(gableRoof(30, 88, 9.0, glass, 0, 29.0, FZ - FD - 45, false, 0.3));
g.add(box(112, 18, 22, buff, 0, 1.6, FZ - FD - 88));                // rear cross range
g.add(box(113, 1.4, 23, blue, 0, 19.6, FZ - FD - 88));
g.add(gableRoof(112, 22, 6.0, slate, 0, 21.0, FZ - FD - 88, true, 0.4));

// ---------------------------------------------------------------- the great central entrance
{
  g.add(box(44, H + 6, FD + 6, buff, 0, 1.6, FZ - FD / 2 + 2));
  g.add(box(45.6, 1.6, FD + 7.6, blue, 0, 1.6 + H + 6, FZ - FD / 2 + 2));
  // the deep round-arched portal
  g.add(openWall(30, 24, 4.0, buff, [{ cx: 0, y0: 0, w: 11.5, h: 8.5, arch: true }], 0, 1.6, FZ + 2.0, 14));
  g.add(box(13, 20, 1.0, dark, 0, 1.6, FZ - 0.5));
  for (let r = 0; r < 3; r++) {                 // recessed orders of the arch
    const rr = 5.75 + r * 1.3;
    const t = new THREE.Mesh(new THREE.TorusGeometry(rr, 0.55, 6, 14, Math.PI), buffd);
    t.position.set(0, 11.7, FZ + 2.0 - r * 1.3);
    g.add(t);
  }
  // gable over the entrance
  g.add(box(30, 3.0, 5.0, blue, 0, 27.6, FZ + 1.5));
  g.add(gableRoof(5.0, 30, 9.0, buff, 0, 30.6, FZ + 1.5, false, 0.2));
  g.add(box(20, 6, 0.6, buffd, 0, 31.5, FZ + 3.9));
}

// ---------------------------------------------------------------- the twin towers (~60 m)
for (const sx of [-1, 1]) {
  const tx = sx * 26;
  const T = new THREE.Group();
  T.add(box(13, 42, 13, buff, 0, 1.6, 0));
  for (let s = 0; s < 5; s++) {
    T.add(box(13.4, 0.8, 13.4, blue, 0, 6 + s * 7.5, 0));
    for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
      T.add(box(dx ? 0.6 : 2.6, 4.2, dz ? 0.6 : 2.6, dark, dx * 6.6, 8 + s * 7.5, dz * 6.6));
  }
  T.add(box(14.6, 1.4, 14.6, blue, 0, 43.6, 0));
  // arcaded belfry
  T.add(box(12.0, 8.5, 12.0, buff, 0, 45.0, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 8.0, 6.0, dz ? 0.6 : 8.0, dark, dx * 6.1, 46.2, dz * 6.1));
  T.add(box(13.8, 1.4, 13.8, blue, 0, 53.5, 0));
  T.add(hipRoof(12.5, 12.5, 5.5, slate, 0, 54.9, 0, 0.15));
  T.add(cyl(0.9, 1.2, 1.4, lead, 0, 60.4, 0, 8));
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    T.add(pinnacle(1.2, 5.0, blue, dx * 5.6, 53.5, dz * 5.6, 6));
  T.position.set(tx, 0, FZ - 8);
  g.add(T);
}

await exportGLB(g, OUT + 'natural_history_museum.glb');
