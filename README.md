# tilevis

A room tile visualizer. Upload a photo of a room, pick a tile from the
catalogue, get a before/after with that exact tile rendered onto the floor
and walls in correct perspective, at true scale, under the room's own light.

The tile pixels always come from the product's real texture. Models are used
to *understand* the room (which pixels are floor, where the plane sits), never
to draw the tile. That is what makes the output defensible to a retailer.

## Layout

    apps/web            Next.js UI - upload, corner editor, tile picker, slider
    apps/api            FastAPI - orchestrates renders, serves catalogue
    packages/renderer   The image pipeline. Pure CPU: geometry, layout, warp,
                        lighting, composite. No models, no network.
    packages/perception  The model wrappers: segmentation + depth, with a disk
                        cache so they run once per photo, never in the dev loop.
    catalogue           SKU definitions and textures
    data                Gitignored: test photos, mask/depth cache, renders
    docs                Pipeline explanation, licence notes, build phases

## Local development

Nothing here costs money and nothing needs an API key.

    # renderer only - the fast loop, no GPU, no models
    cd packages/renderer && pip install -e ".[dev]"
    python -m renderer.cli --help

    # api
    cd apps/api && pip install -e . && uvicorn app.main:app --reload

    # web
    cd apps/web && pnpm install && pnpm dev

## Phase 1 target

Manual corners, floors only, ten SKUs, no models at all. If the output does
not look convincing with four hand-placed corners, no amount of ML fixes it.
See docs/phases.md.
