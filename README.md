# Paris and London — 3D Timelapse

[English](README.md) | [简体中文](README.zh-CN.md)

Two maintained Blender projects live on `main`:

| Project | Selected source | Entry point |
| --- | --- | --- |
| Paris video replica | `worktree-video-replica` at `88ccaed` | [replica/README.md](replica/README.md) |
| London v30 | `london` at `45e156b` | [london/README.md](london/README.md) |

Paris keeps its existing `replica/` directory so pipeline paths remain stable. Its ten imported landmark models are now included in `replica/assets/models/`; the loader no longer depends on an old absolute workspace path. London retains the v30 scene, geography, history, model sources and render scripts, including the latest marsh, Walbrook and dock corrections.

## Running the projects

Start in `replica/` or `london/` and follow that project's README. Both include geographic inputs, building scripts and server render scripts. Use Blender 4.5, Python with NumPy, SciPy, Shapely and Pillow, and FFmpeg for post-processing; inspect individual script imports for optional tooling. London model regeneration also uses Node.js and the package in `london/assets/model_src/`.

Generated caches, Blender scenes, movies, raw OSM downloads and installed dependencies are excluded from Git. Run growth generation before assembling a scene. The optional Paris comparison tool expects `reference/PARIS-original-IFhKB5zHWFg.mp4`, which is not distributed in Git. Rendering on Minerva must follow the user's current `minerva-slurm` skill.

## Consolidation

The former Paris v50 (`master`) and reference reconstruction (`codex/blender-reference-rebuild`) are retired from the maintained file tree. All branch histories are retained by the consolidation merge; original branches and existing worktrees remain available. Old catalog thumbnails and release inventories have been removed from `main`. Historical downloads remain in the repository's existing GitHub Releases.

Existing ignored local media is preserved; it is not part of either selected source project. This consolidation verifies source syntax, data and model dependencies, but does not rerender either film.
