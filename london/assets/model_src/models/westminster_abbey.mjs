// Westminster Abbey with Hawksmoor's west towers (completed 1745), 69 m.
// CONVENTION: metres, ground y=0, centred on the origin, long axis x (west front
// -x, Henry VII chapel +x); +z = the SOUTH side with the cloister & chapter house.
import { exportGLB, out } from './_lib_london.mjs';
import { buildWestminsterAbbey } from './_westminster_abbey.mjs';

await exportGLB(buildWestminsterAbbey({ westTowers: true }), out('westminster_abbey'));
