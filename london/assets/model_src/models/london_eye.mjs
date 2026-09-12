// The London Eye (2000) - 135 m tall observation wheel, 120 m rim, 32 capsules.
// Wheel plane is x-y (faces +z, the river); A-frame legs and backstays on the -z side.
// Convention: metres, ground y=0, hub on the axis at 67.5 m, long axis x.
import { THREE, group, m, P, cyl, torus, strut, exportGLB, out } from '../london_lib.mjs';

const g = new THREE.Group();
const HUB = 67.5, R = 60;                 // rim radius; top of wheel 127.5 m

// --- rim: twin tubular chords + lacing --------------------------------------------
for (const dz of [-1.9, 1.9]) g.add(torus(R, 0.75, m(P.steel), 0, HUB, dz, 64, 6));
for (let i = 0; i < 64; i++) {
  const a = i * 2 * Math.PI / 64;
  const P0 = [R * Math.cos(a), HUB + R * Math.sin(a), -1.9];
  const a2 = (i + 1) * 2 * Math.PI / 64;
  const P1 = [R * Math.cos(a2), HUB + R * Math.sin(a2), 1.9];
  g.add(strut(P0, P1, 0.22, m(P.steel), 4));
}

// --- hub and spindle ---------------------------------------------------------------
const hub = cyl(2.4, 2.4, 22, m(P.steel), 0, 0, 0, 16); hub.rotation.x = Math.PI / 2;
hub.position.set(0, HUB, 0); g.add(hub);
const rim2 = cyl(6.5, 6.5, 8, m(P.alu), 0, 0, 0, 16); rim2.rotation.x = Math.PI / 2;
rim2.position.set(0, HUB, 0); g.add(rim2);

// --- spoke cables: 64 to each side of the hub --------------------------------------
for (let i = 0; i < 64; i++) {
  const a = i * 2 * Math.PI / 64, dz = (i % 2) ? 5 : -5;
  g.add(strut([0, HUB, dz], [R * Math.cos(a), HUB + R * Math.sin(a), (i % 2) ? 1.9 : -1.9], 0.16, m(P.steel), 4));
}

// --- 32 capsules, sitting outboard of the rim --------------------------------------
for (let i = 0; i < 32; i++) {
  const a = i * 2 * Math.PI / 32, rr = R + 3.4;
  const c = new THREE.Mesh(new THREE.SphereGeometry(2.1, 10, 6), m(P.paleGlass));
  c.scale.set(2.0, 1.0, 1.15);
  c.position.set(rr * Math.cos(a), HUB + rr * Math.sin(a), 0);
  c.rotation.z = a;
  g.add(c);
}

// --- A-frame legs on the -z side ---------------------------------------------------
for (const sx of [-1, 1]) {
  g.add(strut([sx * 24, 0, -48], [sx * 5.5, HUB, -1], 1.6, m(P.steel), 8));
  g.add(strut([sx * 24, 0, -48], [sx * 12, HUB * 0.5, -24], 0.9, m(P.steel), 6));   // stiffener
}
g.add(strut([-24, 4, -48], [24, 4, -48], 1.0, m(P.steel), 6));                      // tie beam

// --- backstay cables to the ground anchor ------------------------------------------
for (const sx of [-1, 1]) g.add(strut([sx * 4, HUB, 2], [sx * 9, 1, -92], 0.4, m(P.steel), 5));
g.add(cyl(5, 5, 2.5, m(P.concrete), 0, 0, -92, 10));

// --- boarding platform (river side, +z) --------------------------------------------
g.add(new THREE.Mesh(new THREE.BoxGeometry(60, 1.6, 14), m(P.concrete)).translateY(0.8).translateZ(2));
for (const sx of [-1, 1]) g.add(cyl(3.5, 3.5, 4, m(P.concrete), sx * 24, 0, -48, 10));

await exportGLB(g, out('london_eye'));
