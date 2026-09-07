"""Transferring the room's own light onto the new surface.

This is the step that decides whether the render is believable. A correctly
warped tile with flat lighting reads as fake instantly; a slightly wrong tile
with the room's real light and shadows reads as a photograph.
"""


def shading_layer(image_bgr, mask, radius=60, eps=1e-3):
    """Extract the low-frequency lighting of the original surface.

    The room's illumination is the LOW frequency content of the floor - the
    window gradient, the soft shadow under the vanity. The old tile's pattern
    is the HIGH frequency content, which must be discarded.

    Use a guided or bilateral filter, NOT a gaussian blur. A gaussian smears
    the shadow boundaries along with the grout lines, and the crisp contact
    shadow where an object meets the floor is a large part of what sells the
    image.

    Returns a float32 multiplier normalised so 1.0 is the mean brightness
    inside the mask.
    """
    raise NotImplementedError  # cv2.ximgproc.guidedFilter


def apply_shading(tiled_bgr, shading):
    """tiled * shading, clipped. Multiplicative, in linear-ish space."""
    raise NotImplementedError


def specular_pass(tiled_bgr, shading, gloss: float):
    """Screen-blend the bright end of the shading layer back on top.

    A matte porcelain gets almost none of this; polished marble gets a lot.
    Without it every finish looks identically flat and customers cannot tell
    a matte SKU from a gloss one - which is a product failure, not a visual
    nicety.
    """
    raise NotImplementedError
