"""Orchestration: RenderRequest in, before/after out.

Steps 3-7 of docs/pipeline.md. Steps 1-2 (segmentation, depth) happen in
`tilevis-perception` and arrive here as cached arrays - which is why trying
forty tiles on one photo costs forty CPU renders and zero GPU seconds.
"""

from .types import RenderRequest


def render(request: RenderRequest):
    """
    for each plane:
        H, canvas_size = geometry.homography_from_quad(...)
        canvas         = layout.tile_canvas(...)
        tiled          = warp.warp_to_image(canvas, H, ...)
        shading        = lighting.shading_layer(original, plane_mask)
        lit            = lighting.apply_shading(tiled, shading)
        lit            = lighting.specular_pass(lit, shading, tile.gloss)
        alpha          = compose.paintable_mask(plane_mask, occluders)
        out            = compose.composite(out, lit, alpha)
    return compose.before_after(original, out)
    """
    raise NotImplementedError
