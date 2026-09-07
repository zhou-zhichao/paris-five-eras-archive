// Old St Paul's Cathedral, 1240-1561 (with the great lead spire, 149 m).
// CONVENTION: metres, ground y=0, centred on origin, long axis x (west front -x,
// east end +x); +z = the SOUTH flank, the side facing the river.
import { exportGLB, out } from './_lib_london.mjs';
import { buildOldStPauls } from './_old_st_pauls.mjs';

await exportGLB(buildOldStPauls({ spire: true, towerTop: 87 }), out('old_st_pauls_spire'));
