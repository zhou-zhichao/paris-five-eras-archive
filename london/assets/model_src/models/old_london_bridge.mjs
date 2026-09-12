// Old London Bridge with its houses (1209-1758).
// CONVENTION: metres, water surface y=0, centred on origin, long axis x
// (-x = Southwark / Great Stone Gate, +x = the City); +z = downstream/east side,
// where the Chapel of St Thomas stands.
import { exportGLB, out } from './_lib_london.mjs';
import { buildLondonBridge } from './_old_london_bridge.mjs';

await exportGLB(buildLondonBridge({ houses: true }), out('old_london_bridge'));
