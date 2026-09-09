# Development route

The **order**. How to build [`epics.md`](./epics.md) / [`backlog.md`](./backlog.md)
so each layer is testable before the next depends on it.

## Principle

**Build bottom-up.** The pure renderer proves the product's core claim —
*convincing without ML* ([`phases.md` §P1](./phases.md)) — before any API or
UI exists. This isn't just tidy layering; it's the cheapest place to discover
that the geometry/lighting doesn't convince, which is the whole P1 gate.

This order also falls out of the `CLAUDE.md` architecture rules:

- `packages/renderer` is pure (no torch, no I/O, no downloads) → it's the most
  unit-testable layer → build and prove it first.
- Layout is reasoned in **plane space (mm)** and converted to image space
  exactly once via the homography → geometry + layout are the foundation
  everything else warps on top of.
- All model use is deferred to `packages/perception` behind a photo-hash cache
  → **P1 has no models at all**, so none of that is on the P1 route.

## Sequence

```
1. P1-A Renderer core   ──►  2. P1-B Catalogue   ──►  3. CLI proof point
        (pure, tested)          (real SKU+texture)      (does it convince?)
                                                              │
                                                              ▼
                                    5. P1-D Web  ◄──  4. P1-C API (thin)
                                              │
                                              ▼
                                    6. P1-E Integration + quality gate
```

1. **Renderer core (P1-A) first.** Pure, unit-testable, and where the
   plane-space discipline gets validated. Internal order:
   `T-A1` layout **‖** `T-A2` geometry (independent) → `T-A3` warp →
   `T-A4` lighting → `T-A5` compose → `T-A6` pipeline → `T-A7` CLI.
2. **Catalogue (P1-B) alongside/after A.** The CLI (`T-A7`) needs a real SKU
   and texture to render, so `T-B1` (textures) → `T-B2` (specs) → `T-B3`
   (loader) unblock the first real output. B can start in parallel with A's
   early tickets since it shares no code with the renderer math.
3. **CLI proof point.** Render a sample room from disk, end-to-end, **before
   touching the server**. This is the earliest, cheapest answer to "does it
   convince?" — a partial run of the `T-E2` gate. If it fails here, fix the
   renderer/lighting before building anything on top.
4. **API (P1-C).** Wrap the *proven* pipeline. Routes stay thin — validate →
   call renderer → return (`CLAUDE.md`). `T-C1` bootstrap unblocks the rest;
   `T-C2` photos and `T-C4` renders are the substance; `T-C3` tiles + `T-C5`
   static serving are small.
5. **Web (P1-D).** `T-D1` API client first, then `T-D2` upload. The heavy
   WebGL live-preview track (`T-D3` homography → `T-D4` corner editor) runs
   **in parallel** with the lighter picker/slider track (`T-D5`, `T-D6`).
   `T-D7` page wiring lands last, once the components exist.
6. **Integration + gate (P1-E).** `T-E1` end-to-end smoke → `T-E2` visual
   convincingness gate (the P2 go/no-go) → `T-E3` dev-setup docs.

## Dependency graph (P1)

```
T-A1 layout ─┐
T-A2 geom ───┴─► T-A3 warp ─► T-A4 light ─► T-A5 compose ─► T-A6 pipeline ─► T-A7 CLI
                                                                  ▲              ▲
T-B1 tex ─► T-B2 specs ─► T-B3 loader ────────────────────────────┴──────────────┘

T-C1 bootstrap ─► T-C2 photos ─┐
               ├─► T-C3 tiles   ├─► T-C4 renders ─► (needs T-A6, T-B3)
               └─► T-C5 static ─┘

T-D1 api-client ─► T-D2 upload ─► T-D4 corner-editor ─► T-D7 wiring
T-D3 homography ──────────────────┘                     ▲
T-D5 picker (needs T-C3/T-C4) ──────────────────────────┤
T-D6 before/after ──────────────────────────────────────┘

T-A7 + P1-C + P1-D ─► T-E1 smoke ─► T-E2 quality gate ─► T-E3 docs
```

## What can run in parallel

- **`T-A1` ‖ `T-A2`** — layout and geometry share no code; two people/sessions.
- **P1-B ‖ early P1-A** — texture/spec work is independent of renderer math
  until the CLI proof point needs them together.
- **`T-D3`/`T-D4` (WebGL) ‖ `T-D5`/`T-D6` (picker/slider)** — the live-preview
  track is the long pole; the picker and slider can be built against
  placeholder data meanwhile.
- **`T-C3` ‖ `T-C2`** — tiles and photos endpoints are independent once `T-C1`
  mounts the routers.

## Guardrails to hold at every step

- **Renderer isolation** — no torch/transformers/model import ever reaches
  `packages/renderer`; it must run on CPU with no downloads. This is what
  keeps the dev loop fast and per-render cost near zero.
- **Plane-space discipline** — reason about tiles in millimetres; convert to
  pixels exactly once via the homography. Never reason in pixel coordinates.
- **Purity** — renderer functions are arrays-in/arrays-out; all I/O lives in
  `cli.py` and the API layer.
- **Coordinate-space docstrings** — every geometry function names its space
  (`plane_mm`, `image_px`, `normalised`).
- **Data safety** — room photos are never committed; `data/` is gitignored;
  no photo goes to a third-party API without an explicit consent path.

## Looking past P1 (route implications)

- **P2 (detection)** slots *behind* the existing manual path: perception fills
  the quad/masks that the P1 `CornerEditor` and `compose.paintable_mask`
  already consume. Build the **photo-hash disk cache boundary** first so
  segmentation/depth run once per photo, never per tile.
- **Licence gates before launch** — SegFormer (NVIDIA non-commercial) must be
  swapped; FLUX `dev` weights (non-commercial) are testing only; SAM 3's Meta
  licence must be read. Track in [`licences.md`](./licences.md).
- **P4 scope waits on the retailer** — asset format, SKU count, deployment
  surface, and success metric (see the open questions in `phases.md`) all
  reshape the catalogue/commerce work; don't hard-plan it before those land.
