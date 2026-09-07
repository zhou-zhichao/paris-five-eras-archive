# Paris fidelity work

V50 remote preview is complete and downloaded to `renders/paris_v50_720p.mp4`: 1280x720, 30 fps, 3600 frames, 120 seconds, 94,764,344 bytes, silent visual preview. Array 257406 and encode 257410 completed with exit 0. Local and remote SHA256 match (`1d79f460df78145f0c88c047fcecb76e663b15dbe8be2936e653e112136bedea`); a full local FFmpeg decode passed. Render delivery is complete; overall reference-fidelity work remains unfinished. Older submission status below is historical.

User direction: continue improving toward the reference film; use sampled frames only. Do not render the full animation locally.

2026-09-05 update: user explicitly requested a full preview on Minerva. V50 is uploaded with matching SHA256; active rendering array 257406 (4 L4 GPUs, 4 workers each) and dependent CPU encode 257410 are submitted. Initial 257401/257405 were cancelled after evidence that EEVEE's EGL display ignored CUDA_VISIBLE_DEVICES and all 16 processes used physical GPU 0. A process-scoped `egl_device_v2.so` now resolves EGL's display to CUDA-visible device 0 (Slurm's assigned physical GPU); factory-scene probe 1930106 verified physical GPU 3 usage. The initial broad-symbol shim hung two probe steps and was replaced by scoped dlsym interception; use the current `egl_device.c`, not the obsolete `egl_device.so`. Resume checks PNG chunk CRCs, retains completed frames, and publishes new frames atomically. There were 1,145 PNGs at cancellation. Inspect `minerva_render/v50_job.json` and the live scheduler/logs, then download and verify the final MP4. This authorizes the remote preview, not local full animation rendering. Another independent `paris_replica_v1` job 257392/257393 exists under the account; do not confuse it with this scene or alter it.

Reference: https://www.youtube.com/watch?v=IFhKB5zHWFg — CITY 3D TIMELAPSE, PARIS - 3D TIMELAPSE - 300 BCE to 2025 (No AI). Downloaded to `reference/PARIS-original-IFhKB5zHWFg.mp4`, 2560x1440, 30 fps, 180 seconds, audio included.

The previous project's scripts, data, assets and packed v44 Blender scene were copied from `C:/Users/sam/Documents/Codex/2026-07-31/https-www-youtube-com-watch-v/work/paris-five-eras-poc` into this workspace. Do not edit the old project. The archive README describes the prior published files, not the active working scene.

## Active iteration

- Baseline: `blender/paris_5_eras_roman_medieval_v44_temple_enclosure.blend`.
- Candidate: `blender/paris_v47_spatial_transition.blend`; v45/v46 are retained for comparison.
- Current remote review candidate: `blender/paris_v50_woodland.blend` (v48 timing plus v49/v50 vegetation changes).
- Data generator: `tools/generate_late_blocks.py --version v46`; Python 3.14 dependencies are in `tools/python_vendor` (Shapely 2.1.2).
- Scene builder: `blender/rebuild_late_blocks_v45.py -- --version v46`, run against the baseline, never against its own output.
- Still renderer: `blender/render_review_still.py -- --frame 3550 --output previews/<name>.png`. One frame only; default 960x540, 16 EEVEE samples.
- Early preservation check: `blender/check_early_preservation.py`. Records visible mesh signatures at frames 750, 1450 and 2100; does not establish pixel equivalence.

V45 replaces the scattered 1850 and modern mainland building layers with 5,818 road-aligned blocks containing 62,198 building parcels. Courtyards remain, major vacant cells receive street-aligned subdivision, and river/park/landmark/rail masks exclude development. The 1850 blocks persist into the modern era while outer blocks grow. Per-parcel wall heights and pitched roofs add relief. A ground color multiplier ramps in after frame 2174, leaving early material output unchanged at factor zero.

## Evidence and remaining gaps

- `reference/original-sheet.jpg`: sampled reference overview. The fps filter samples bin centers; the years printed in the image are authoritative, not row index times.
- `reference/original-modern.png`: source at 150 s, showing year 1960.
- `previews/v44-modern.png`: baseline frame 3550.
- `previews/v45-modern.png`: superseded first perimeter test, excessive vacant courtyards.
- `previews/v45-modern-dense.png`: superseded density test, overly flat unified roofs.
- `previews/v45-modern-parcels.png`: latest modern candidate, rendered and inspected. Density and rooftop relief improved; broad river exclusion bands, hard urban perimeter and exposed park roads remain visibly wrong.
- `previews/v44-v45-comparison.jpg`: same-camera baseline/candidate comparison.
- `previews/v45-1850-parcels.png`: latest 1850 candidate.
- `previews/v45-1850.png`: intermediate dense-ring version, not the final parcel version; regenerate before judging current 1850 quality.

The target is NOT achieved. Remaining work includes visual verification of the latest parcel scene, current 1850 review, transition frames around 2175/2850, roof/street contrast, riverbank and island treatment, landmark readability and proportions, camera framing, expansion pattern and 1700 quality. The modern OSM road network is a spatial proxy; phase assignment and invented minor streets are not verified historical reconstruction. Reference has more historical phases and a 3-minute timeline; current scene remains a five-era 2-minute approximation.

`reports/early-preservation-v45.json` passed: the visible mesh signatures match v44 at all three checked early frames. This is geometry/transform/material-assignment evidence only; pixel equivalence and transition behavior have not been established. The latest modern single frame took about 19.5 seconds after scene load at 960x540/16 samples; no animation render was used.

Do not infer smooth animation from endpoint stills. Review sampled onset/midpoint/end frames before claiming transitions work. Keep the active goal open until the actual visual fidelity and required checks support completion. No full render, publication, or GPU cluster job has been launched in this iteration.

## V46 environment correction

The broad shoreline voids were a coordinate mismatch, not merely a density issue. Actual scene Seine geometry is materially different from raw `paris_geodata.json` river centerlines. At x=-40, the actual water section spans y=6.41..8.05 while the former raw mask spans y=10.68..15.96. Export the scene surfaces with `blender/export_late_environment.py`; `data/scene_environment.json` is now authoritative for water/island masks. Regenerate this export if the river is edited.

V46 has 6,131 blocks. It excludes actual water plus a small quay setback, uses smaller oriented station exclusions, removes the obsolete medieval island-wall bounding-box exclusion, retires the old mainland road layers from frame 2175, and installs streets clipped to actual water and configured parks. Quays follow the same scene water boundary. Legacy bridge and landmark objects are retained.

Verification: `tools/check_late_environment.py` passed and wrote `reports/environment-check-v46.json`. Building footprint water overlap fell from 40.6311 scene-area units in v45 to zero in v46. New street triangle overlap with water is zero and with park masks is numerical zero. This checks the new generated geometry, not every legacy scene object. `reports/early-preservation-v46.json` also passed at 750/1450/2100.

Inspected frames:
- `previews/v46-modern.png`: 3550, 1280x720. Broad river voids resolved, buildings meet quays and park roads are removed. Still not equivalent to the reference: urban edge, landmark treatment, islands and camera composition need refinement.
- `previews/v46-transition-2180.png`: old city remains at the beginning of the 1850 replacement; no wholesale disappearance.
- `previews/v46-transition-2500.png`: reveals a real temporal defect. Red-roof old 1700 houses overlap the new perimeter blocks. Original removal order and new radial birth schedule differ. Align the two spatially; do not claim transition quality based on endpoint frames.
- `previews/v45-v46-comparison.jpg`: same-camera modern comparison (v45 upscaled only for layout).

Next priority: fix spatial replacement timing around 2175..2800, then sample current 1850 endpoint and modern onset. Old meshes may batch spatially separated houses; inspect before retiming each whole object's death by its centroid, which could create empty outer districts. Preserve pre-2175 behavior and keep all rendering to requested review stills.

## V47 spatial replacement

Run `blender/align_transition_v47.py` against v46 to produce `blender/paris_v47_spatial_transition.blend`. No source data regeneration is needed for this pass.

The final v47 pass also delays 279 outer road/quay surface patches until modern expansion (their patch centers lie outside the 1850 envelope). The initial 2800 review exposed a premature dense road grid in the forest; this timing correction removes it. The 2350/2500 transition images below predate this outer-surface timing correction, so their central building handoff is representative but the outer road timing is superseded. `previews/v47-1850.png` is regenerated for the final pass.

Inspection confirmed 1,259 of 1,532 old 1700 chunks span more than five scene units; the widest spans 55.8 units. The new script groups connected mesh components and nearby facade pieces into 7,515 spatial groups, max width 0.741 units, then assigns conservative retirement times based on nearby new block bounds. All 584,378 old visible faces are retained at the handoff from frame 2174 to 2175, in 248 retirement meshes. Original old mesh animation remains before 2175. Clones disappear from frame 2205 to 2490, ahead of nearby new construction. Roof/material geometry was not redesigned in this pass.

Evidence:
- `reports/transition-chunks.json`: original chunk dimensions and attributes; no UVs/custom shader attributes needed transfer.
- `reports/transition-v47.json`: regrouping and face count conservation.
- `reports/transition-visibility-v47.json`: 11 evaluated time samples. Original old objects are absent after handoff; temporary retirement geometry is absent before handoff and after 2490. New block count rises to 3,260 at 2800/2850 and 6,131 at 3550.
- `reports/early-preservation-v47.json`: early mesh signatures match v44 at 750/1450/2100, and modern 3550 signature matches v46. These are not pixel-equivalence or exhaustive collision tests.
- `previews/v47-transition-2350.png`: inspected; central new fabric and outer old fabric meet without the former scattered red roofs throughout new districts. The radial frontier is still stylized.
- `previews/v47-transition-2500.png`: inspected; former old/new overlap is gone and no large new void is visible.
- `previews/v46-v47-transition-comparison.jpg`: same-frame comparison.
- `previews/v47-1850.png`: current 1850 endpoint review.

The overall fidelity goal remains open. Next priorities: assess the current 1850 endpoint, reduce the artificial urban perimeter and improve suburban structure, improve reference camera/composition and landmark scale/readability, and review the 1700 state itself. Do not label the reference matched or all transitions validated from these few samples. Keep using single-frame renders only.

Final 2800 frame inspected after the road delay: `previews/v47-1850.png` no longer shows the premature dense forest road grid. The border remains conspicuously artificial. Next suburban pass should add/retain a sparse arterial connection to the countryside plus road-following settlements and varied open space; hiding the entire late outer grid is only a timing correction, not a finished rural-road design.

## V48 suburban timing

Candidate: `blender/paris_v48_spatial_transition.blend`. Build order: run `tools/plan_1850_fringe.py`, run `blender/retime_fringe_v48.py` against v46, then run `blender/align_transition_v47.py -- --version v48` against the intermediate `paris_v48_fringe_layout.blend`. The alignment script now reads actual block birth properties. Do not run it against an already spatially regrouped scene.

Reference `reference/original-1850-near.png` is source 125 seconds, printed year 1851. It shows a dense center surrounded by road-following settlements and open fields. V47 prematurely filled almost the entire 1850 envelope. V48 retains 1,585 dense blocks at frame 2800 and postpones 1,675 former phase-3 blocks to modern construction, using a central density falloff and primary-road proximity. Modern OSM remains only a spatial proxy, not verified historical mapping. Late modern geometry is intended to remain identical to v46.

Old-house retirement is recalculated against these births. All 584,378 faces transfer at 2175; 334 spatial retirement meshes disappear between 2205 and 2989. At 2800, 64,061 old faces remain as fringe housing. `reports/transition-visibility-v48.json` passed 14 evaluated samples including the face-count handoff and exact new-block visibility counts against birth properties. This is not an exhaustive collision or motion-quality check.

Inspected single-frame renders: `previews/v48-1850.png` (2800, 1280x720) and `previews/v48-transition-3000.png` (3000, 960x540). The central/outer density distinction improves, but the cleared fringe still exposes a modern street grid with sparse large block fragments and conspicuous patches of colorful old houses. The source has more finely distributed roadside settlement and field structure. Oversized sparse trees, simplified downstream river bend, hard forest clearing envelope, landmark proportions, lighting/color and the five-era timeline remain unfinished. Prioritize rural street hierarchy/settlement and late vegetation scale next. No full animation rendering was launched in this pass.

`reports/early-preservation-v48.json` passed: early visible mesh signatures match v44 at 750/1450/2100, and the modern 3550 signature matches v46. This covers mesh identity, topology counts, transforms and material assignments; it does not establish pixel equivalence or reference fidelity. Overall goal remains open.

## V49/V50 late vegetation

`blender/refine_late_vegetation_v49.py`, run against v48, produces `paris_v49_late_vegetation.blend`. It adds a late-only tree proportion shape key: XY 0.32, Z 0.30, blended after 2174 through 2500. Existing clearance is retained via `mix*(1-clearance)`. Persistent trunk/crown components use local trunk anchors; 13 unmatched remnants stay centered rather than being attached to unrelated trees. Evaluated vegetation vertex coordinates at 750/1450/2100/2174 remain exactly equal; see `reports/vegetation-v49.json`. Endpoint stills reveal that resizing alone makes the surrounding terrain too bare, so v49 is an intermediate test rather than the latest candidate.

`blender/densify_late_woodland_v50.py`, run against v49 after its modern landmark bbox JSON exists, adds 67,835 small woodland crowns around persistent forest anchors outside radius 28. Conservative block, water-face and landmark bbox masks and road-distance masks exclude conflicts. Trees near future blocks retire before construction; 64,766 added trees remain at 3550. New geometry is hidden through 2174. `reports/woodland-v50.json` samples visibility at 2100/2174/2800/3000/3550. The 2800 still `previews/v50-1850.png` was inspected: tree scale and peripheral density are improved, but the large empty fringe with modern road outlines, central roof texture, river bend and reference composition remain unresolved. Local render session 38678 was active at user interruption; inspect its live state or outputs before restarting anything. Do not treat the overall fidelity goal as complete.
