# Blender reference reconstruction

Source: `reference/source.mp4`, the only visual reference. 2560 x 1440, 30 fps, 179.994 seconds.

The user requested a fresh worktree and a Blender reconstruction of the supplied Paris evolution film. Existing compositions, city generators, camera paths, and reports are deliberately excluded from the sparse checkout. The two explicitly permitted landmark meshes are available for inspection and reuse.

## Deliverables

- An editable, self-contained Blender scene and reproducible Python sources.
- A complete film following the reference's 180-second progression and continuous camera retreat.
- Reference/render comparison frames and a building model inspection sheet.

## Visual direction from the supplied video

Olive terrain; softly reflective teal river with pale banks; cream limestone and terracotta early roofs; intricate pale and slate street walls in later centuries; numerous small, varied trees; warm sunlight from the upper right; long coherent shadows; restrained miniature depth of field. Geography remains continuous through all eras. Housing is arranged along streets with interior courtyards, changing roof types, modest height variation, chimneys, cornices and window rhythms.

## Construction

Trace river geometry, city envelope, major routes, landmark placement and camera framing from source frames. Procedurally model ordinary buildings anew. Use spatial construction dates and demolition dates, with smooth localized growth. Keep the reference's bottom-left English era labels and bottom-right year counter. Finish with the reference's return to undeveloped terrain.

This is a visual reconstruction from a rendered film, not a surveyed historical GIS dataset. Record approximation and visual verification honestly.

## Runtime

Blender 4.5.10. The user explicitly restricts local rendering to individual inspection frames. The complete film and its encoding must run through `ssh minerva`. Every Minerva render/probe uses only `gpu:L4:1` per task. Check all RUNNING/PENDING jobs owned by `zhichaoz` before each GPU submission. Do not modify or cancel unrelated jobs.
