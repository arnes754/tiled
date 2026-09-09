# P1 Backlog

Full-spec tickets for **P1 — Floors, manual corners, ten SKUs**. Grouped by
the five sub-epics in [`epics.md`](./epics.md), listed in dependency order.
Build order and parallelisation live in [`dev-route.md`](./dev-route.md).

Ticket IDs are stable (`T-<epic><n>`) — reference them in commits and PRs.
Estimates are t-shirt sizes: **S** ≈ ½–1 day, **M** ≈ 1–2 days, **L** ≈ 3–5 days.

> **Standing guardrails** (from `CLAUDE.md`, apply to every ticket):
> `packages/renderer` imports **no** torch/transformers/model and does **no**
> I/O — arrays in, arrays out. Layout is reasoned in **plane space (mm)** and
> converted to image space exactly once via the homography. Type hints
> everywhere; `float32` for image math, `uint8` only at boundaries. Every
> geometry function names its coordinate space (`plane_mm`, `image_px`,
> `normalised`) in the docstring. Room photos are never committed.

---

## P1-A — Renderer core

### T-A1 — Layout engine (plane-space tile canvas)
- **Epic:** P1-A Renderer core
- **Goal:** Produce a flat, perspective-free tiled surface in plane-mm from a `TileSpec`, pattern, and grout settings.
- **Key files:** `packages/renderer/src/renderer/layout.py`, `packages/renderer/tests/test_layout.py`
- **Implementation notes:**
  - `period = tile_mm + grout_mm`; `col, row = floor(x/period), floor(y/period)`.
  - Deterministic variant pick: `variant = variants[hash(col, row) % n]` — kills visible repetition without randomness that breaks reproducibility.
  - `u, v = x % period, y % period`; grout fill where `u > tile_mm or v > tile_mm`.
  - Bonds: `stack` (no offset), `running_half`/`running_third` (offset row by `phase * period`). Herringbone/basketweave are out of P1 scope unless trivial.
  - Pure `float32`; `uint8` only at the boundary. Docstring declares `plane_mm`.
- **Acceptance criteria:**
  - `stack` and `running_half`/`running_third` yield correct offsets, asserted against a known small grid.
  - Variant selection is deterministic across runs; grout width and colour honoured.
  - No torch / no model imports; function is pure (arrays in, arrays out).
- **Dependencies:** none (`types.py` complete).
- **Test plan:** unit tests in `test_layout.py` — period math, bond offsets, variant determinism (same seed → same grid), edge seaming at canvas borders.
- **Risk:** weak variant hashing → visible tiling; verify visually with `n=1` vs `n=4`.
- **Estimate:** M

### T-A2 — Geometry (homography from quad)
- **Epic:** P1-A Renderer core
- **Goal:** Build the homography `H` mapping plane-mm to image-px from four corners, plus canvas-sizing helpers.
- **Key files:** `packages/renderer/src/renderer/geometry.py`, `packages/renderer/tests/test_geometry.py`
- **Implementation notes:**
  - `homography_from_quad(quad_image_px, width_mm, height_mm)` via `cv2.getPerspectiveTransform`.
  - Helper to derive canvas size (px) from plane extent and a target `px_per_mm`.
  - Optional RANSAC plane-fit helper may be deferred to P2; keep the P1 path purely from the four manual corners.
  - Docstrings name both spaces explicitly (`plane_mm` → `image_px`).
- **Acceptance criteria:**
  - Round-trip a synthetic quad with a known answer: plane corners map to the expected image corners within tolerance.
  - `H` is invertible; inverse maps image corners back to plane corners.
- **Dependencies:** none (can run parallel to T-A1).
- **Test plan:** `test_geometry.py` — synthetic quads with hand-computed homographies; forward and inverse mapping assertions.
- **Risk:** corner ordering ambiguity (which corner is which) → fix and document a canonical order.
- **Estimate:** M

### T-A3 — Warp (plane canvas → image)
- **Epic:** P1-A Renderer core
- **Goal:** Warp the plane-space tile canvas into photo space with anti-aliasing.
- **Key files:** `packages/renderer/src/renderer/warp.py`
- **Implementation notes:**
  - `warp_to_image(canvas, H, out_size, supersample=3)` — render supersampled then downsample (box filter) to tame far-floor aliasing.
  - Use `cv2.warpPerspective`; keep `float32` throughout.
- **Acceptance criteria:**
  - Output aligns to the quad (warped canvas corners land on the input image corners).
  - Far-field (top of floor) shows no shimmer/moiré at `supersample=3` vs visible aliasing at `supersample=1`.
- **Dependencies:** T-A1 (canvas), T-A2 (`H`).
- **Test plan:** unit test that a solid-colour canvas warps to fill exactly the quad polygon; visual check of supersample effect via CLI once T-A7 lands.
- **Risk:** supersample memory/time at 1600px → cap factor, benchmark.
- **Estimate:** M

### T-A4 — Lighting (shading transfer + specular)
- **Epic:** P1-A Renderer core
- **Goal:** Lift the room's own low-frequency illumination onto the tile, plus a gloss-scaled specular pass.
- **Key files:** `packages/renderer/src/renderer/lighting.py`
- **Implementation notes:**
  - `shading_layer(original_bgr, mask)` — extract low-frequency illumination over the floor region (guided/bilateral filter, `cv2.ximgproc.guidedFilter`).
  - `apply_shading(tiled_bgr, shading)` — multiply tile by normalised shading.
  - `specular_pass(lit_bgr, shading, gloss)` — add a highlight term scaled by the SKU's `gloss`/`finish`.
- **Acceptance criteria:**
  - A tile placed under a room with a bright window inherits that gradient (mean brightness follows the shading field).
  - `gloss=0` produces no specular term; higher gloss visibly increases highlights.
- **Dependencies:** T-A3 (tiled image), floor mask (P1: from the quad polygon; P2: from segmentation).
- **Test plan:** synthetic gradient shading → assert output brightness tracks it; `gloss` monotonicity check.
- **Risk:** `cv2.ximgproc` requires `opencv-contrib-python` (already a renderer dep) — confirm import.
- **Estimate:** L

### T-A5 — Compose (mask, blend, before/after)
- **Epic:** P1-A Renderer core
- **Goal:** Feather the paintable region and blend the lit tile over the original at full resolution, returning the before/after pair.
- **Key files:** `packages/renderer/src/renderer/compose.py`
- **Implementation notes:**
  - `paintable_mask(surface_mask, occluder_masks)` — subtract occluders, feather edges. In P1 `surface_mask` is the quad polygon and `occluder_masks` is empty.
  - `composite(original_bgr, lit_bgr, alpha)` — alpha blend, `float32` math.
  - `before_after(original_bgr, output_bgr)` — the UI slider pair.
- **Acceptance criteria:**
  - Feathered edges show no hard seam at the quad boundary.
  - `before_after` returns two same-size images (original, rendered).
- **Dependencies:** T-A4 (lit tile).
- **Test plan:** unit test alpha=0 → original unchanged, alpha=1 → full tile; feather width honoured.
- **Estimate:** M

### T-A6 — Pipeline (orchestration)
- **Epic:** P1-A Renderer core
- **Goal:** Wire A1–A5 into `render(RenderRequest)` in the documented order (see `docs/pipeline.md`).
- **Key files:** `packages/renderer/src/renderer/pipeline.py`, `packages/renderer/src/renderer/__init__.py`
- **Implementation notes:**
  - Order: geometry → layout → warp → shading → apply_shading → specular → paintable_mask → composite → before_after.
  - Pure function: takes arrays + `RenderRequest`, returns before/after arrays. No I/O.
- **Acceptance criteria:**
  - Given an in-memory photo, `TileSpec`, and quad, returns a plausible before/after pair without touching disk.
  - No model imports anywhere in the call graph.
- **Dependencies:** T-A1–T-A5.
- **Test plan:** integration test on a synthetic photo + solid texture → output differs from input only inside the quad.
- **Estimate:** M

### T-A7 — CLI (renderer I/O boundary)
- **Epic:** P1-A Renderer core
- **Goal:** `python -m renderer.cli render --photo X --tile Y --corners ...` — load inputs, call `pipeline.render`, write before/after.
- **Key files:** `packages/renderer/src/renderer/cli.py`
- **Implementation notes:**
  - This is the **only** renderer module that does I/O (loads photo + texture, parses corners, writes PNGs).
  - Parse a tile spec JSON (via the T-B3 loader) and corner coordinates from args.
- **Acceptance criteria:**
  - Running the command on a sample room + real SKU writes a before/after pair to disk.
  - `--help` documents all args.
- **Dependencies:** T-A6, and T-B2/T-B3 for a real SKU to render.
- **Test plan:** manual — this is the P1 "CLI proof point" (see dev-route step 3).
- **Risk:** none blocking; keep arg parsing thin.
- **Estimate:** S

---

## P1-B — Catalogue & textures

### T-B1 — Fetch CC0 test textures
- **Epic:** P1-B Catalogue & textures
- **Goal:** Populate `catalogue/textures/` with ~6 seamless, scale-known CC0 materials for development.
- **Key files:** `scripts/fetch_test_textures.sh`, `catalogue/textures/`
- **Implementation notes:**
  - Pull from ambientCG / Poly Haven (CC0). Record px-per-100mm scale per the texture README.
  - Textures must be seamless and flat-lit (no baked shadows — lighting is added at render time).
- **Acceptance criteria:**
  - Script fetches the materials idempotently; scale recorded for each.
  - Downloaded textures are **not** committed if large — respect `.gitignore`; commit only references/metadata as the repo already does.
- **Dependencies:** none.
- **Test plan:** run the script on a clean checkout; verify files + scale metadata land.
- **Risk:** licence drift — confirm each asset is CC0 and note it (see `licences.md`).
- **Estimate:** S

### T-B2 — Author ~10 SKU specs
- **Epic:** P1-B Catalogue & textures
- **Goal:** Hand-author ~10 tile JSON specs conforming to `catalogue/schema.json`.
- **Key files:** `catalogue/tiles/*.json` (model on `catalogue/tiles/example-600x600-matte.json`)
- **Implementation notes:**
  - Cover a range: sizes (e.g. 300, 600), finishes (matte/gloss), floor vs wall `use`.
  - Reference the T-B1 textures; set `size_mm`, `grout_default`, `patterns`, `gloss`/`finish`.
- **Acceptance criteria:**
  - Each file validates against `catalogue/schema.json`.
  - At least one floor SKU is render-ready for the T-A7 proof point.
- **Dependencies:** T-B1.
- **Test plan:** validate each JSON against the schema (jsonschema).
- **Estimate:** S

### T-B3 — Catalogue loader
- **Epic:** P1-B Catalogue & textures
- **Goal:** Read + validate tile JSONs into `TileSpec` objects, usable by both the CLI and the API.
- **Key files:** new loader module (renderer-side helper or `apps/api` service — see note), `catalogue/schema.json`
- **Implementation notes:**
  - Validate against `schema.json`; construct `renderer.types.TileSpec`.
  - **Placement:** keep it renderer-adjacent but I/O-free where possible — actual file reading may live in `cli.py`/API. Decide during implementation to preserve renderer purity (`CLAUDE.md`).
- **Acceptance criteria:**
  - Loads all T-B2 specs; rejects a malformed spec with a clear error.
  - Returned `TileSpec` carries texture paths + scale for the renderer.
- **Dependencies:** T-B2.
- **Test plan:** unit test — valid dir loads N specs; a deliberately broken spec raises.
- **Estimate:** M

---

## P1-C — API orchestration

### T-C1 — App bootstrap (routes, CORS, errors)
- **Epic:** P1-C API orchestration
- **Goal:** Mount the photo/render/catalogue routers, enable dev CORS, add error handling.
- **Key files:** `apps/api/app/main.py`, `apps/api/app/config.py`
- **Implementation notes:**
  - Uncomment/mount `routes.photos`, `routes.renders`, `routes.catalogue`.
  - CORS for the web dev origin; consistent error responses.
- **Acceptance criteria:**
  - `/health` still returns `{"ok": true}`; all three routers mount and respond (even if endpoints are stubbed pending C2–C4).
  - Web dev origin can call the API without CORS errors.
- **Dependencies:** none (unblocks C2–C5).
- **Test plan:** `uvicorn app.main:app --reload`; hit `/health` and each router root.
- **Estimate:** S

### T-C2 — POST /photos (upload + validate + normalise)
- **Epic:** P1-C API orchestration
- **Goal:** Accept a photo upload, normalise it, validate it, store it, and return a `photo_id`.
- **Key files:** `apps/api/app/routes/photos.py`, `apps/api/app/schemas.py`, `apps/api/app/config.py`
- **Implementation notes:**
  - Strip EXIF, auto-rotate, resize to ~1600px working copy (per `docs/pipeline.md` ingest step).
  - Reject < 1MP and motion-blurred images early.
  - Store under `DATA_DIR` (gitignored); `photo_id` keys later renders and (in P2) the perception cache.
- **Acceptance criteria:**
  - Valid upload returns a `photo_id` and persists the normalised copy.
  - Under-resolution / blurred uploads are rejected with a clear message.
  - Add the missing `PhotoIn`/`PhotoOut` schema.
- **Dependencies:** T-C1.
- **Test plan:** curl a sample image → get `photo_id`; curl a tiny image → get a 4xx.
- **Risk:** never forward photos to third parties without a consent path (`CLAUDE.md`).
- **Estimate:** M

### T-C3 — GET /tiles (catalogue)
- **Epic:** P1-C API orchestration
- **Goal:** Serve the catalogue from the T-B3 loader.
- **Key files:** `apps/api/app/routes/catalogue.py`, `apps/api/app/schemas.py`
- **Implementation notes:**
  - Minimal filtering for P1 (return all; colour/size/format filters are P4).
  - Add a `TileSpec` response schema mirroring the catalogue.
- **Acceptance criteria:**
  - `GET /tiles` returns the ~10 SKUs with texture references and dimensions.
- **Dependencies:** T-B3, T-C1.
- **Test plan:** curl `/tiles` → JSON list matches `catalogue/tiles/`.
- **Estimate:** S

### T-C4 — POST /renders (hot path)
- **Epic:** P1-C API orchestration
- **Goal:** Turn a render request into a before/after via `renderer.pipeline.render`, persist outputs, return URLs + m².
- **Key files:** `apps/api/app/routes/renders.py`, `apps/api/app/schemas.py` (`RenderIn`/`RenderOut` exist)
- **Implementation notes:**
  - Load the normalised photo by `photo_id`, resolve the `TileSpec`, build the quad from `PlaneIn`, call the pure renderer.
  - Compute area m² from plane dimensions. Persist before/after under `DATA_DIR`.
  - Keep it cheap — no model loading (P1 has none; P2 reads cached perception).
- **Acceptance criteria:**
  - A valid request returns `render_id`, before/after URLs, and area_m2.
  - Rendering logic stays in the renderer package; the route only orchestrates.
- **Dependencies:** T-A6, T-B3, T-C2, T-C5.
- **Test plan:** end-to-end curl: upload photo → request render → fetch returned URLs.
- **Estimate:** M

### T-C5 — Static serving for photos/renders
- **Epic:** P1-C API orchestration
- **Goal:** Serve stored photos and renders over HTTP so the web app can display them.
- **Key files:** `apps/api/app/main.py`
- **Implementation notes:**
  - Mount a static route over `DATA_DIR` (or a dedicated renders subdir). URLs returned by C4 must resolve here.
- **Acceptance criteria:**
  - A render URL from C4 loads in the browser.
- **Dependencies:** T-C1.
- **Test plan:** open a returned before/after URL directly.
- **Estimate:** S

---

## P1-D — Web UI & live preview

### T-D1 — API client (`lib/api.ts`)
- **Epic:** P1-D Web UI & live preview
- **Goal:** Typed client for the FastAPI backend.
- **Key files:** `apps/web/lib/api.ts` (types mirror `apps/api/app/schemas.py`)
- **Implementation notes:**
  - `uploadPhoto(file)`, `listTiles()`, `requestRender(req)`; go through the Next rewrite (`/api/*` → `:8000`) already in `next.config.ts`.
  - Error handling surfaced to callers.
- **Acceptance criteria:**
  - All three functions typed and callable; a smoke call to `/health`/`/tiles` succeeds against a running API.
- **Dependencies:** T-C1 (API reachable); pairs with C2/C3/C4.
- **Test plan:** call `listTiles()` from a scratch page against the running API.
- **Estimate:** S

### T-D2 — PhotoUpload component
- **Epic:** P1-D Web UI & live preview
- **Goal:** File input with capture guidance and client-side validation, posting to `/photos`.
- **Key files:** `apps/web/components/PhotoUpload.tsx`
- **Implementation notes:**
  - Guidance UI: stand in the doorway, get two opposite corners in frame, lights on, hold still.
  - Client-side reject of obviously-too-small images before upload; call `api.uploadPhoto`.
- **Acceptance criteria:**
  - Selecting a valid photo uploads it and yields a `photo_id`; guidance is visible; small images are flagged client-side.
- **Dependencies:** T-D1, T-C2.
- **Test plan:** manual upload flow in `pnpm dev`.
- **Estimate:** M

### T-D3 — Homography + WebGL preview (`lib/homography.ts`)
- **Epic:** P1-D Web UI & live preview
- **Goal:** Client-side 4-point homography solver + WebGL warp for 60fps live preview (no server round-trip).
- **Key files:** `apps/web/lib/homography.ts`
- **Implementation notes:**
  - Solve the source→destination-quad homography (SVD or direct 8-DOF solve).
  - Render via WebGL for correct mipmapping / anisotropic filtering (fixes far-floor aliasing in-browser). Server render (C4) stays the source of truth for the saved image.
- **Acceptance criteria:**
  - Given a texture and four dragged corners, the preview warps correctly and updates smoothly (~60fps).
- **Dependencies:** none (can run parallel to D5/D6).
- **Test plan:** manual — drag corners, confirm the warp tracks and stays crisp in the far field.
- **Risk:** WebGL setup is the heaviest P1 web item — timebox and keep the shader minimal.
- **Estimate:** L

### T-D4 — CornerEditor component
- **Epic:** P1-D Web UI & live preview
- **Goal:** Four draggable corner handles + a metric-scale reference, with live preview via `lib/homography.ts`.
- **Key files:** `apps/web/components/CornerEditor.tsx`
- **Implementation notes:**
  - Handles over the photo; a "drag to known width" control sets metric scale.
  - Feed quad + scale into the T-D3 preview; hold quad/scale in component state.
- **Acceptance criteria:**
  - Corners drag; the metric reference sets scale; live preview updates as corners move.
- **Dependencies:** T-D3, T-D2 (needs an uploaded photo).
- **Test plan:** manual — drag all four corners and the scale handle; confirm preview.
- **Estimate:** M

### T-D5 — TilePicker component
- **Epic:** P1-D Web UI & live preview
- **Goal:** Browse the catalogue, pick pattern and grout, trigger a render.
- **Key files:** `apps/web/components/TilePicker.tsx`
- **Implementation notes:**
  - Grid from `listTiles()`; pattern (stack/running/…) and grout width/colour selectors.
  - On selection, call `api.requestRender` with the current quad + scale.
- **Acceptance criteria:**
  - Tiles list from the API; selecting one (with pattern/grout) requests a render and shows the result.
- **Dependencies:** T-D1, T-C3, T-C4.
- **Test plan:** manual — pick a tile, see the render appear.
- **Estimate:** M

### T-D6 — BeforeAfter slider
- **Epic:** P1-D Web UI & live preview
- **Goal:** Draggable split slider revealing the render over the original at full resolution.
- **Key files:** `apps/web/components/BeforeAfter.tsx`
- **Implementation notes:**
  - Two stacked images, draggable divider, slider position in state.
- **Acceptance criteria:**
  - Dragging the divider wipes between original and render smoothly at full res.
- **Dependencies:** T-C4 output (before/after URLs); can be built with placeholder images (parallel to D3/D4/D5).
- **Test plan:** manual — drag the divider across a returned before/after pair.
- **Estimate:** S

### T-D7 — Page wiring (landing + visualize)
- **Epic:** P1-D Web UI & live preview
- **Goal:** Assemble the journey across the two pages with shared state.
- **Key files:** `apps/web/app/page.tsx`, `apps/web/app/visualize/page.tsx`
- **Implementation notes:**
  - Landing: `PhotoUpload` + sample-room options → navigate to `/visualize` with `photo_id`.
  - Visualize: `CornerEditor` | `TilePicker` on top, `BeforeAfter` | m²+price readout below.
- **Acceptance criteria:**
  - A user can go upload → corners → tile → before/after entirely through the UI.
- **Dependencies:** T-D2, T-D4, T-D5, T-D6.
- **Test plan:** full manual walkthrough (feeds T-E1).
- **Estimate:** M

---

## P1-E — Integration & quality gate

### T-E1 — End-to-end smoke path
- **Epic:** P1-E Integration & quality gate
- **Goal:** One repeatable path: sample room → corners → tile → render → slider, over the real API.
- **Key files:** test/script under `scripts/` or `apps/api`; uses a committed sample room reference (not a real home photo).
- **Implementation notes:**
  - Prefer a scripted API-level smoke (upload → render → assert outputs) plus a manual UI pass.
- **Acceptance criteria:**
  - The scripted path produces a before/after without manual intervention; the UI pass matches.
- **Dependencies:** all of P1-A/B/C/D.
- **Test plan:** run the smoke script in CI-like local conditions.
- **Estimate:** S

### T-E2 — Visual convincingness gate
- **Epic:** P1-E Integration & quality gate
- **Goal:** A written checklist that answers the P1 question — *does it convince without ML?* (`phases.md` §P1).
- **Key files:** `docs/` (a `quality-gate.md` or a section appended here).
- **Implementation notes:**
  - Checklist: perspective correct, grout scale believable, lighting matches the room, edges seamless, no far-field shimmer, no visible texture repetition.
  - Review against several sample rooms; record pass/fail + notes. This is the go/no-go for P2.
- **Acceptance criteria:**
  - Checklist exists and is run against ≥3 sample rooms with recorded verdicts.
- **Dependencies:** T-E1.
- **Test plan:** the checklist itself is the test.
- **Estimate:** S

### T-E3 — Dev setup / run docs
- **Epic:** P1-E Integration & quality gate
- **Goal:** One-command-ish local loop documented (or a Makefile) so the full stack runs reproducibly.
- **Key files:** `README.md`, optional `Makefile`, `scripts/`
- **Implementation notes:**
  - Consolidate: renderer tests, CLI render, API (`uvicorn`), web (`pnpm dev`), texture fetch. Mirror the commands in `CLAUDE.md`.
- **Acceptance criteria:**
  - A fresh clone can reach the end-to-end demo by following the doc.
- **Dependencies:** touches all P1 areas; finalise last.
- **Test plan:** follow the doc on a clean checkout.
- **Estimate:** S

---

## Coverage check

Every P1 ticket maps to a stubbed file, and every stubbed P1 file is ticketed:

| Stubbed file | Ticket |
|---|---|
| `renderer/layout.py` (+ `test_layout.py`) | T-A1 |
| `renderer/geometry.py` (+ `test_geometry.py`) | T-A2 |
| `renderer/warp.py` | T-A3 |
| `renderer/lighting.py` | T-A4 |
| `renderer/compose.py` | T-A5 |
| `renderer/pipeline.py`, `renderer/__init__.py` | T-A6 |
| `renderer/cli.py` | T-A7 |
| `scripts/fetch_test_textures.sh` | T-B1 |
| `catalogue/tiles/*.json` | T-B2 |
| catalogue loader (`schema.json`) | T-B3 |
| `api/app/main.py`, `config.py` | T-C1, T-C5 |
| `api/routes/photos.py` | T-C2 |
| `api/routes/catalogue.py` | T-C3 |
| `api/routes/renders.py` | T-C4 |
| `web/lib/api.ts` | T-D1 |
| `web/components/PhotoUpload.tsx` | T-D2 |
| `web/lib/homography.ts` | T-D3 |
| `web/components/CornerEditor.tsx` | T-D4 |
| `web/components/TilePicker.tsx` | T-D5 |
| `web/components/BeforeAfter.tsx` | T-D6 |
| `web/app/page.tsx`, `app/visualize/page.tsx` | T-D7 |

Not in P1 (deferred to P2+ per `epics.md`): `perception/segment.py`,
`perception/depth.py`, `perception/cache.py`, `scripts/precompute_masks.py`.
