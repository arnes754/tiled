# How a render is made

Less AI than it appears. The models understand the room; plain geometry draws
the tile. Every tile pixel comes from the SKU's own texture, warped and lit -
which is what lets a retailer put their name on the output.

## 1. Ingest          `apps/api/app/routes/photos.py`
Strip EXIF, auto-rotate, keep a ~1600px working copy and the original.
Reject under ~1MP or heavily blurred, with a message saying what to reshoot.

## 2. Segment  (model)   `packages/perception/segment.py`
Masks for `floor`, `wall`, and each occluder. The paintable region is
`floor AND NOT union(occluders)` - the subtraction is what makes a cabinet
stand ON the new tile instead of being buried under it.

## 3. Geometry  (no model, or optional)   `packages/renderer/geometry.py`
A homography H maps plane millimetres to image pixels. Either the user drags
four corners (exact, free, instant) or a depth model proposes the plane and
the user corrects it. Scale needs an anchor either way: four unlabelled
corners give the plane's shape, not that it is 3.2m wide. Get this wrong and
600mm tiles render at 400mm - plausible-looking and completely incorrect.

## 4. Layout   `packages/renderer/layout.py`
In plane space, in millimetres, with no perspective to think about:

    period = tile_mm + grout_mm
    col, row = floor(x / period), floor(y / period)
    variant  = variants[hash(col, row) % n]     # kills visible repetition
    u, v     = x % period, y % period
    px       = grout if (u > tile_mm or v > tile_mm) else variant[v, u]

Bond patterns are row offsets on this grid; herringbone needs per-cell
rotation and is handled separately.

## 5. Warp   `packages/renderer/warp.py`
One `warpPerspective` puts the whole canvas into the photo. The trap is
aliasing: OpenCV does no mipmapping, so the far end of a floor shimmers.
Supersample and downsample, or do this pass in WebGL where the GPU handles
it correctly for free.

## 6. Light   `packages/renderer/lighting.py`
The room's illumination is the LOW frequency of the original surface; the old
tile pattern is the high frequency to discard.

    L       = LAB luminance of the original
    shading = guidedFilter(L, radius=60)      # NOT a gaussian
    shading /= mean(shading[paintable])
    lit      = tiled * shading

A gaussian blur smears the shadow edges along with the grout lines, and the
crisp contact shadow where an object meets the floor is a large part of what
makes the image read as a photograph. Then a specular pass scaled by the
SKU's gloss, or every finish looks identically flat.

## 7. Composite   `packages/renderer/compose.py`
Feather 1-2px, blend at full resolution, return the before/after pair.

## 8. Finish pass  (model, optional)
Low strength, instruction confined to lighting and contact shadows, never
pattern or colour. Keep the un-polished render and compare - if the model
reinvented the grout, ship the geometric one.

## Where the AI is

| Step | Model? | Doing what |
|---|---|---|
| Segmentation | yes | finds floor, walls, occluders |
| Plane recovery | optional | proposes geometry the user corrects |
| Layout, warp, lighting, composite | no | arithmetic and signal processing |
| Finish pass | optional | harmonises light only |
