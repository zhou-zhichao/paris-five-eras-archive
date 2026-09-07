import { exportGLB, mat, box, cyl, cone, dome, gableRoof, hipRoof, prism, lathe, group } from './export_glb.mjs';
const stone = mat(0xd8cfb8), roof = mat(0x5a5a60), gold = mat(0xd4a83a);
const g = group(
  box(40, 20, 20, stone),
  gableRoof(40, 20, 6, roof, 0, 20, 0, true),
  cyl(6, 6, 30, stone, 25, 0, 0), cone(7, 12, roof, 25, 30, 0),
  dome(8, gold, -25, 15, 0), box(16, 15, 16, stone, -25, 0, 0),
  hipRoof(20, 12, 5, roof, 0, 0, 25),
  prism([[-5,-5],[5,-5],[5,5],[0,8],[-5,5]], 10, stone, 0, 0, -30),
  lathe([[0,0],[3,0],[3,10],[1,12],[0.2,20],[0,22]], gold, 40, 0, 0),
);
await exportGLB(g, 'out/test.glb');
