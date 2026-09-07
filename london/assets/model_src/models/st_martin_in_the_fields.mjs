// St Martin-in-the-Fields, James Gibbs 1726.  Portland stone.
// Long axis along X; the giant Corinthian PORTICO is the west front at -X and the
// steeple (59 m) rises through the roof just behind it.  South side faces +Z.
import { exportGLB, box, cyl, cone, lathe, THREE, P, M,
  column, pediment, balustrade, churchBody, OUT } from './_lib_church.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), lead = M(P.lead),
  gold = M(P.gold), dark = M(0x4a463d);

const L = 40, W = 24, H = 16;
const X0 = -L / 2 + 4;                        // west end of the nave body
churchBody(g, X0, L, W, H, { bays: 5 });

// ---------------------------------------------------------------- west portico (6 columns)
{
  const PX = X0 - 8.5;
  for (let i = 0; i < 6; i++) g.add(box(1.05, 0.63, W + 4 - i * 1.0, dk, PX - 5.0 + i * 1.05, i * 0.63, 0));
  for (let i = 0; i < 6; i++) {
    const z = -9.0 + i * 3.6;
    g.add(column(1.15, 13.5, pale, PX, 3.8, z, 12));
    if (i === 0 || i === 5) g.add(column(1.15, 13.5, pale, PX + 4.6, 3.8, z, 12));
  }
  g.add(box(9.0, 3.0, 24, pale, PX + 1.2, 17.3, 0));
  { const pd = new THREE.Group(); pd.add(pediment(24, 5.4, 9.0, pale, 0, 0, 0)); pd.rotation.y = -Math.PI / 2; pd.position.set(PX + 1.2, 20.3, 0); g.add(pd); }
  g.add(box(1.2, 13.5, 18, dark, X0 - 0.8, 3.8, 0));
}

// ---------------------------------------------------------------- steeple, 59 m
{
  const TX = X0 + 6.5;
  const T = new THREE.Group();
  T.add(box(12.5, 22, 12.5, st, 0, 1.0, 0));
  T.add(box(13.6, 1.4, 13.6, pale, 0, 23.0, 0));
  // clock stage
  T.add(box(11.0, 7.0, 11.0, st, 0, 24.4, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const d = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2.5, 0.8, 16), M(0xe8e4d8));
    if (dz) d.rotation.x = Math.PI / 2; else d.rotation.z = Math.PI / 2;
    d.position.set(dx * 5.7, 28.0, dz * 5.7); T.add(d);
  }
  T.add(box(12.2, 1.2, 12.2, pale, 0, 31.4, 0));
  // belfry with pilasters
  T.add(box(10.2, 9.0, 10.2, st, 0, 32.6, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.6 : 4.4, 6.2, dz ? 0.6 : 4.4, dark, dx * 5.2, 33.8, dz * 5.2));
  T.add(box(11.6, 1.4, 11.6, pale, 0, 41.6, 0));
  T.add(balustrade(11.6, 11.6, 1.6, pale, 0, 43.0, 0));
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    T.add(cyl(0.7, 0.9, 2.6, pale, dx * 5.4, 44.6, dz * 5.4, 8));
  // octagonal lantern + obelisk spire
  T.add(cyl(3.4, 3.8, 6.5, st, 0, 44.6, 0, 8));
  for (let i = 0; i < 8; i++) {
    const a = (i + 0.5) / 8 * Math.PI * 2;
    T.add(box(1.5, 4.4, 0.6, dark, Math.cos(a) * 3.6, 45.6, Math.sin(a) * 3.6));
  }
  T.add(cyl(4.4, 4.4, 1.0, pale, 0, 51.1, 0, 8));
  T.add(lathe([[3.2, 0], [3.0, 1.0], [2.2, 2.2], [1.4, 3.2]], lead, 0, 52.1, 0, 8));
  T.add(cone(1.4, 3.6, lead, 0, 55.3, 0, 8));
  T.add(cyl(0.22, 0.22, 1.6, gold, 0, 57.4, 0, 6));
  T.position.set(TX, 0, 0);
  g.add(T);
}

await exportGLB(g, OUT + 'st_martin_in_the_fields.glb');
