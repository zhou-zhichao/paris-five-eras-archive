# London timelapse (Blender)

Procedural 3-minute film of London growing from the pre-Roman Thames marshes to 2025, in the
format of the Paris replica (`../replica/`): an oblique low-poly map, era label bottom-left,
year counter + population bottom-right, 2560x1440 @ 30 fps, 180 s.

Compared with the Paris replica this version adds
* **real history driving the built-up area**: hand-authored + researched growth rings and village
  nuclei, dated destruction / rebuild events (Boudica 60, Roman abandonment 420 -> Alfred 886,
  Lundenwic abandoned 880, Great Fire 1666 -> brick rebuild 1667-82, Blitz 1940-41 -> post-war
  estates, Docklands clearance 1978 -> regeneration, estate regeneration), council estates and
  high-rise clusters with dates, replacement chains per building (timber -> brick -> Victorian ->
  modern), docks that are dug and later filled, lost rivers (Fleet, Walbrook, Tyburn, Effra ...) that
  vanish when culverted, the pre-embankment Thames foreshore, the Roman/medieval City wall and the
  1643 Civil War lines, park and railway opening dates;
* **one clean bridge per real Thames bridge** (58 entries with birth / rebuild / demolition years,
  parametric arch / iron / suspension / rail / concrete builders, GLB models for Old London Bridge,
  Tower Bridge, Hungerford), aligned by scanning the water raster for the shortest crossing —
  OSM `bridge=yes` road chunks are no longer drawn as bridges;
* **higher-fidelity landmarks**: ~120 three.js models (`assets/model_src/models/*.mjs`, exported to
  `assets/models/*.glb`) at true scale, drawn 1.25x in plan and **1.5x in height**; ~290 dated
  landmark entries (`scripts/landmark_table.py` + `data/history/landmarks.json`);
* **matte water** (no sun glint sweeping over the river as the camera moves — the "flicker");
* 12 building kits (celtic, roman, saxon, medieval, tudor, georgian, victorian, interwar, postwar,
  modern, estate, tower) and a population read-out per era.

## Pipeline

```
python scripts/fetch_osm.py                     # Overpass -> data/osm_raw.json (network; inner + outer street tiles)
python scripts/build_geo.py                     # -> data/geo.json (metres, origin St Paul's; non-overlapping water layers)
blender -b --python scripts/preview_kits.py -- <abs>/cache/kits.png    # exports data/kit_footprints.json
python scripts/growth.py                        # growth engine -> cache/scene_data.npz, rasters.npz, scene_meta.json (+ qa_*.png)
blender -b --python scripts/build_scene.py -- --out cache/london.blend [--subsample N]
blender -b cache/london.blend --python scripts/render.py -- --out renders/final [--step 30] [--res WxH] [--lens 120]
blender -b cache/london.blend --python scripts/render_blueprint.py -- --out renders/final/blueprint.png
python scripts/overlay.py --frames renders/final --out renders/london.mp4
```

Research inputs live in `data/history/` (landmarks, bridges, villages, population, water, transport,
landscape; compiled 2026-09-07 from Wikipedia / VCH / Historic England / PLA / Museum of London
sources by research agents, with `notes` flagging uncertain values). `scripts/history.py` merges them
with the hand-authored fallbacks so the pipeline also runs without them.

Landmark models: `assets/model_src/` holds the three.js sources (`node models/<id>.mjs` with
`three@0.170` installed next to `export_glb.mjs`); conventions: metres, ground y=0, centred, long axis x,
front towards +z (= Blender -y), flat vertex colours. `preview_glb.py` renders contact sheets.

Cluster rendering (minerva) works exactly as for Paris (`server/`, see `../replica/README.md`).
