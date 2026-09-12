// Old St Paul's after the 1561 lightning strike: the spire is gone, the central
// tower stands truncated at ~85 m, and Inigo Jones' giant Corinthian west portico
// (1633-42) and Portland re-casing are added.
// CONVENTION: metres, ground y=0, centred on origin, long axis x (west front -x,
// east end +x); +z = the SOUTH flank, the side facing the river.
import { exportGLB, out } from './_lib_london.mjs';
import { buildOldStPauls } from './_old_st_pauls.mjs';

const g = buildOldStPauls({ spire: false, portico: true, towerTop: 78 });
g.position.x = 10;   // re-centre now that the portico extends the west front
await exportGLB(g, out('old_st_pauls_nospire'));
