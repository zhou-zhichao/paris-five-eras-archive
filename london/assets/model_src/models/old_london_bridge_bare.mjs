// Old London Bridge after the 1758-62 improvement: houses demolished, the deck
// widened, a balustrade and domed stone alcoves added and the two centre arches
// thrown into one Great Arch.
// CONVENTION: metres, water surface y=0, centred on origin, long axis x
// (-x = Southwark, +x = the City); +z = downstream/east side.
import { exportGLB, out } from './_lib_london.mjs';
import { buildLondonBridge } from './_old_london_bridge.mjs';

await exportGLB(buildLondonBridge({ houses: false }), out('old_london_bridge_bare'));
