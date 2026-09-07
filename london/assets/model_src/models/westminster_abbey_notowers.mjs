// Westminster Abbey before 1745: the west front stops at stub towers barely
// above the nave roof; everything else (Henry VII chapel, flying buttresses,
// north rose, chapter house) as built.
// CONVENTION: metres, ground y=0, centred on the origin, long axis x (west front
// -x, Henry VII chapel +x); +z = the SOUTH side with the cloister & chapter house.
import { exportGLB, out } from './_lib_london.mjs';
import { buildWestminsterAbbey } from './_westminster_abbey.mjs';

await exportGLB(buildWestminsterAbbey({ westTowers: false }), out('westminster_abbey_notowers'));
