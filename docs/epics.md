# Epics

The **what**. This document breaks the strategic roadmap in
[`phases.md`](./phases.md) into epics you can plan and ticket against.

- `phases.md` owns the **why / when** — strategy, sequencing, time estimates,
  open retailer questions. It stays the source of truth for that.
- This file owns the **what** — the units of deliverable work per phase.
- [`backlog.md`](./backlog.md) owns the **how** — full-spec tickets, and is
  currently detailed for **P1 only**.
- [`dev-route.md`](./dev-route.md) owns the **order** — the recommended build
  sequence and the architecture guardrails that constrain it.

Ticket detail exists for P1. P2–P5 are held at epic level (feature lists +
entry criteria) and get ticketed when their entry criteria are met, so we
don't plan work that earlier phases will reshape.

---

## P1 — Floors, manual corners, ten SKUs  *(current target)*

Strategy: [`phases.md` §P1](./phases.md). No models at all. The bar is a
single question — *does the render convince?* — answered before any GPU spend.
Split into five sub-epics.

### P1-A — Renderer core
The pure numpy/opencv pipeline that turns a tile + a floor quad into a lit,
composited before/after. No torch, no I/O, no downloads (per `CLAUDE.md`).
Layout → geometry → warp → lighting → compose → pipeline → CLI.
Tickets: `T-A1`–`T-A7`.

### P1-B — Catalogue & textures
The tile library the renderer draws from: fetched CC0 seamless test textures
with known scale, ~10 SKU specs conforming to `catalogue/schema.json`, and a
loader that validates them into `TileSpec`. Per the texture README, this
library — not the code — is usually the critical path.
Tickets: `T-B1`–`T-B3`.

### P1-C — API orchestration
Thin FastAPI layer that wraps the proven pipeline: mount routes + CORS, photo
upload (EXIF strip, auto-rotate, resize, validate), tile listing, render
request, and static serving of stored photos/renders. Routes validate → call
the renderer → return; no rendering logic lives here.
Tickets: `T-C1`–`T-C5`.

### P1-D — Web UI & live preview
The user journey: upload with capture guidance, a draggable four-corner editor
with a metric-scale reference and 60fps WebGL live preview, a tile picker with
pattern/grout controls, a before/after slider, and the two pages that wire it
together.
Tickets: `T-D1`–`T-D7`.

### P1-E — Integration & quality gate
Prove the whole loop end-to-end and hold it to the P1 bar: an end-to-end smoke
path over the API, the visual convincingness checklist, and the documented
local dev setup.
Tickets: `T-E1`–`T-E3`.

**P1 exit criteria:** a sample room renders end-to-end with a real SKU, the
before/after slider sells the result, and the visual quality gate (`T-E2`)
passes — the go/no-go for investing in ML.

---

## P2 — Automatic detection

Strategy: [`phases.md` §P2](./phases.md). Models propose the quad and the
occlusion masks; the P1 manual handles stay forever as the correction path.

**Features**
- `perception/segment.py` — floor/wall/occluder masks (SAM backends).
- `perception/depth.py` — depth + normals (Depth Anything 3).
- `perception/cache.py` — disk cache keyed by SHA-256 photo hash; segmentation
  and depth run **once per photo**, never per tile (`CLAUDE.md`).
- Auto-propose the floor quad from segmentation + depth, pre-filling the
  `CornerEditor` instead of starting blank.
- Occluder masks feed `compose.paintable_mask` so furniture/feet aren't tiled.
- `scripts/precompute_masks.py` — warm the cache for a test photo offline.
- Instrument how often manual handles are touched — the real accuracy metric.

**Entry criteria:** P1 exit criteria met.

**Guardrails:** all model use stays inside `packages/perception`, behind the
cache boundary — `packages/renderer` must remain model-free.
**Licence:** SegFormer weights are NVIDIA non-commercial — dev only, must be
swapped before launch (see [`licences.md`](./licences.md)). SAM 3's Meta
licence must be read before commercial use.

---

## P3 — Walls

Strategy: [`phases.md` §P3](./phases.md). Multi-plane rendering — meaningfully
harder than floors, which is why it's its own phase.

**Features**
- Per-wall quads and multi-plane composition in one render.
- Floor line as the layout datum; courses run upward from it.
- Correct behaviour at internal corners, around windows, and behind fixtures
  (e.g. the vanity).
- Wall-aware `use: ["wall"]` handling in layout and catalogue filtering.

**Entry criteria:** P1 floor rendering is convincing and P2 detection is
reliable enough that per-plane quads aren't purely manual.

---

## P4 — Catalogue & commerce

Strategy: [`phases.md` §P4](./phases.md). Where the retailer gets its return.

**Features**
- Full SKU import (beyond the ~10 hand-authored P1 specs) and richer filtering
  (colour, size, format, room).
- m² calculator from detected floor area.
- Save and share a visualisation.
- Hand-off to a quote or a showroom appointment.

**Entry criteria:** the retailer open questions in
[`phases.md`](./phases.md#open-questions-for-the-retailer) are answered —
asset format, SKU count and who produces textures, deployment surface, and the
success metric all shape this phase's scope.

---

## P5 — Generative finish

Strategy: [`phases.md` §P5](./phases.md). Optional polish, ongoing.

**Features**
- Lighting harmonisation and contact shadows — **lighting only**, never
  pattern or colour (`CLAUDE.md`).
- Side-by-side quality gate: generative output vs the geometric render; ship
  the generative pass only when it clearly wins.
- Per-SKU opt-out.

**Entry criteria:** the geometric render is the trusted baseline; generative
work must beat it on the quality gate to ship.

**Licence:** FLUX `dev` weights are non-commercial — testing only. Any
production image-edit provider must be licence-cleared first.
