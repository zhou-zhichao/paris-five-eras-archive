// Christ Church, Spitalfields, Nicholas Hawksmoor 1714-29.  Portland stone.
// Long axis along X; the great Tuscan PORTICO with its central arch is the west front at -X
// and the tower and 68 m spire rise directly behind it.  South side faces +Z.
import { exportGLB, box, cyl, cone, lathe, THREE, P, M,
  column, pediment, balustrade, openWall, churchBody, OUT } from './_lib_church.mjs';
const g = new THREE.Group();
const st = M(P.stone), pale = M(P.pale), dk = M(P.dstone), lead = M(P.lead),
  gold = M(P.gold), dark = M(0x4a463d);

const L = 42, W = 24, H = 17;
const X0 = -L / 2 + 5;
churchBody(g, X0, L, W, H, { bays: 5 });

// ---------------------------------------------------------------- Tuscan portico with a central arch
{
  const PX = X0 - 8.0;
  for (let i = 0; i < 5; i++) g.add(box(1.1, 0.6, 20 - i * 1.4, dk, PX - 5.0 + i * 1.1, i * 0.6, 0));
  // the arched screen: four Tuscan columns carrying an arch over the centre
  for (const z of [-7.4, -3.4, 3.4, 7.4]) g.add(column(1.25, 11.0, pale, PX, 3.0, z, 12));
  // the entablature is broken up over the centre by a semicircular arch
  g.add(box(4.0, 2.4, 7.0, pale, PX, 14.0, -8.0));
  g.add(box(4.0, 2.4, 7.0, pale, PX, 14.0, 8.0));
  const arc = new THREE.Mesh(new THREE.TorusGeometry(5.0, 1.2, 6, 12, Math.PI), pale);
  arc.rotation.y = Math.PI / 2; arc.position.set(PX, 14.0, 0);
  g.add(arc);
  g.add(box(4.2, 2.6, 22, pale, PX, 19.0, 0));
  g.add(box(4.4, 2.0, 20, pale, PX, 21.6, 0));
  g.add(box(1.4, 12, 16, dark, X0 - 0.7, 3.0, 0));
}

// ---------------------------------------------------------------- tower and 68 m spire
{
  const TX = X0 + 7.0;
  const T = new THREE.Group();
  T.add(box(14.5, 24, 15.5, st, 0, 1.0, 0));
  for (const [dx, dz] of [[0, 1], [0, -1]])
    T.add(box(4.0, 8.0, 0.6, dark, 0, 12.0, dz * 7.9));
  T.add(box(15.8, 1.6, 16.8, pale, 0, 25.0, 0));
  // belfry stage with tall round-headed openings
  T.add(box(13.0, 12.0, 14.0, st, 0, 26.6, 0));
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]])
    T.add(box(dx ? 0.7 : 4.8, 8.5, dz ? 0.7 : 4.8, dark, dx * 6.6, 28.6, dz * 7.1));
  T.add(box(14.6, 1.6, 15.6, pale, 0, 38.6, 0));
  // the octagonal broach base and the tall pyramidal spire
  T.add(box(12.2, 4.0, 12.2, st, 0, 40.2, 0));
  for (const [dx, dz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]])
    T.add(cone(2.4, 5.0, pale, dx * 5.0, 44.2, dz * 5.0, 4));
  T.add(cyl(5.4, 6.1, 3.0, st, 0, 44.2, 0, 8));
  T.add(cyl(6.4, 6.4, 1.0, pale, 0, 47.2, 0, 8));
  T.add(cone(5.6, 18.0, pale, 0, 48.2, 0, 8));
  T.add(cyl(0.5, 0.7, 1.4, gold, 0, 66.2, 0, 6));
  T.add(cone(0.6, 1.2, gold, 0, 67.6, 0, 6));
  T.position.set(TX, 0, 0);
  g.add(T);
}

await exportGLB(g, OUT + 'christ_church_spitalfields.glb');
