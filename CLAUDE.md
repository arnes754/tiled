# tilevis

Room tile visualizer. Photo in, before/after out, with the retailer's real
tile rendered in perspective under the room's own lighting.

# Commands

- Renderer tests: `cd packages/renderer && pytest`
- Renderer CLI: `python -m renderer.cli render --photo X --tile Y --corners ...`
- API: `cd apps/api && uvicorn app.main:app --reload`
- Web: `cd apps/web && pnpm dev`
- Precompute masks for a test photo: `python scripts/precompute_masks.py <photo>`

# Architecture rules

- **`packages/renderer` must not import torch, transformers, or any model.**
  It is pure numpy/opencv and must run on a CPU with no downloads. This is
  what keeps the dev loop fast and the per-render cost near zero.
- All model use lives in `packages/perception`, behind a disk cache keyed by
  photo hash. Segmentation and depth run ONCE per photo, never per tile.
- Tile pixels come from the SKU texture. A model never generates tile.
  The optional finish pass may only touch lighting, never pattern or colour.
- Work in plane space (millimetres) for layout; convert to image space once,
  via the homography. Never reason about tiles in pixel coordinates.

# Conventions

- Renderer functions are pure: arrays in, arrays out, no I/O. I/O lives in
  `cli.py` and the API layer.
- Every geometry function documents its coordinate space in the docstring:
  `plane_mm`, `image_px`, or `normalised`.
- Tests next to the code in `packages/renderer/tests/`, `test_*.py`.
- Type hints everywhere in Python. `float32` for image math, uint8 only at
  the boundaries.

# Licence discipline

Model licences are not all permissive and this ships commercially one day.
Before adding any model, record its licence in `docs/licences.md`.
Known: Depth Anything 3 Apache-2.0 (fine). SAM 3 custom Meta licence
(commercial allowed, read it). SegFormer weights NVIDIA non-commercial
(dev only, must be swapped before launch).

# Data

- Room photos are pictures of the inside of people's homes. Never commit one.
  `data/` is gitignored in full.
- Do not send photos to a third-party API without an explicit consent path.
