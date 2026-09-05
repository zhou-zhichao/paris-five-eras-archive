# Paris reference reconstruction

Fresh branch: `codex/blender-reference-rebuild`.

Worktree: `C:/Users/sam/Documents/ChatGPT/3D-map-reference-rebuild`.

Only visual source: `reference/source.mp4` (copied from the original workspace's reference video). No old scene, house generator, camera path, city data or composition was used. The source SHA-256 is `BB5CF844EBBCC4231743F010161FF720B1CE1644D3E2C1B081DD63821CCA7D57`.

## Editable deliverables

- `output/paris_reference_rebuild.blend`: the complete 5,400-frame Blender scene, including geometry-node construction dates, animated camera, era labels, decimal year counter, ending grid and fades. Fonts and imported mesh data are packed.
- `output/original_building_library.blend`: inspection scene for the six main newly modeled house families.
- `review/original-building-library.png`: close inspection of modeled roofs, windows, cornices and chimneys.
- `review/final-*.jpg`: inspection frames extracted from the delivered movie.
- `review/rebuild-*.png`: earlier scene development frames; these are not the final color grade.
- `review/scene-validation.json`: timeline, packing and render-contract checks.
- `data/city.json`: reproducibly generated street parcels, building records, forest, railways and landmarks. Regenerate from the script below; this is intentionally not inherited city data.
- `data/water_surface.json`: river triangulation with shoreline distance attributes for the pale-shore-to-teal transition.

The main scene contains 72 new rectilinear house variants, six new Celtic huts, eight new tree variants, hand-built landmark silhouettes, six stations and railway approaches, gardens and bridges. About 197,000 house instances are visible at the end; replacement records are additional. Ordinary housing uses perimeter lots, interior wings and courtyards, with distinct red-tile, gabled, limestone, mansard and suburban forms. Notre Dame and the Eiffel Tower are the only reused meshes.

## Rebuild and inspect

Planner environment used: Python 3.14, NumPy 2.4.3, SciPy 1.18.1, Shapely 2.1.2, Pillow 12.1.0. Blender 4.5.10 includes its own runtime for scene authoring.

```powershell
python src/plan_city.py
python src/water_surface.py
blender -b --factory-startup -t 8 --python-exit-code 1 --python src/build_scene.py -- --preview 24 80 165 --width 1280
blender -b output/paris_reference_rebuild.blend --python-exit-code 1 --python src/verify_scene.py
python src/review_movie.py
```

The user explicitly allows **only individual inspection frames locally**. All full-film rendering and encoding must run on Minerva. Do not start a local animation render.

## Minerva production

Remote run directory: `/data/users/zhichaoz/blender-render/runs/reference_rebuild_20260905_r2`.

- Render array: `257531`, tasks `0-15`, one L4 per task, 2560 x 1440, native 30 fps, 64 EEVEE samples.
- Dependent CPU encode/validation job: `257547`, `afterok:257531`.
- Completed L4 environment probe: `257423`. At 1920 x 1080, the test frames took approximately 1.5-5.6 seconds including initial setup.
- Final remote movie: `output/paris_reference_rebuild_1440p.mp4`.
- Encode writes to a `.pending.mp4` filename and renames only after successful frame counting and full decode verification.
- The scene's SHA-256 is recorded in `RUN_STATUS.json`; compare before resuming a run.

The frozen production scene SHA-256 is `3991d3b26d97d2802e011950bf0c278419a6df509d72288fff5c161c8d774d19`. The remote encoder applies a gradual gamma/color-balance adjustment and a mild vignette, calibrated against source frames at 24 and 80 seconds. The Blender file contains the geometry, camera, typography and fades; the final movie's additional color grade is reproducible through `src/encode_l4_output.sbatch`.

Full-movie review of the first render identified excessive white water, an overly steep camera, insufficient miniature height, a visible river endpoint and a narrow ending grid. Revision 2 adds a triangulated shoreline-distance material, lowers the camera, raises building/tree proportions, extends the distant river beyond the frame, and adjusts the tilted wipe grid with two surviving landscape routes. The first movie is retained as `output/paris_reference_rebuild_v1_1440p.mp4`; its completed render/encode jobs were `257514` and `257527` in the previous run directory without the `_r2` suffix.

All Blender GPU jobs in this project must request `gpu:L4:1`. Check **all** RUNNING and PENDING jobs owned by `zhichaoz` before any new GPU submission or resubmission. Do not change unrelated jobs. L40S is prohibited for this project's future jobs.

The remote EEVEE support shim and shared libraries are existing render infrastructure, symlinked into this run. They contain no reference visuals or inherited city content.

## Production verification and recovery

1. Read `RUN_STATUS.json` and inspect only this run's jobs/logs and frame counts.
2. Stay quiet if nothing actionable changed; do not repeatedly report an unchanged queue.
3. Let the successful render trigger the dependent encode. On failure, diagnose logs and resume only incomplete frames with the same scene hash; preserve successful frames.
4. Download the final MP4, `video-probe.json` and `sha256.txt` to this worktree's `output/`.
5. Verify the downloaded hash, 2560 x 1440 resolution, 30 fps, 5,400 frames and 180-second duration. The remote encoder already performs a complete decode check.
6. Inspect extracted movie frames around 6, 24, 54, 80, 127, 165 and 173 seconds and check transitions for broken water, missing assets, disappearing labels or temporal artifacts. Extracting inspection frames locally is allowed; full local rendering is not.
7. Update the status document and deliver clickable local movie/scene links. Stop further follow-up checks once delivery is complete.

## Fidelity limits

This is a new geometric reconstruction of the supplied film's miniature map effect and era progression. Street parcels are procedural interpretations of traced major routes. It is not an exact reproduction of every source building, historical boundary, landmark detail or camera pose. The current film is silent. Do not claim frame-perfect or historically surveyed equivalence.
