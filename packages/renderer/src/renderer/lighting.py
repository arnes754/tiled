"""Transferring the room's own light onto the new surface.

This is the step that decides whether the render is believable. A correctly
warped tile with flat lighting reads as fake instantly; a slightly wrong tile
with the room's real light and shadows reads as a photograph.

Image convention: BGR float32, range 0..255. Shading is returned as a
single-channel (H, W, 1) float32 multiplier so it broadcasts over BGR.
"""

import cv2
import numpy as np


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
    inside the mask, shape (H, W, 1).
    """
    gray = cv2.cvtColor(image_bgr.astype(np.float32), cv2.COLOR_BGR2GRAY) / 255.0

    # Edge-preserving smooth: the image guides itself, so shadow boundaries
    # survive while the tile pattern (high frequency) is flattened out.
    smoothed = cv2.ximgproc.guidedFilter(guide=gray, src=gray, radius=int(radius), eps=float(eps))

    m = _mask_bool(mask, image_bgr.shape[:2])
    mean = float(smoothed[m].mean()) if m.any() else float(smoothed.mean())
    mean = max(mean, 1e-4)

    shading = (smoothed / mean).astype(np.float32)
    return shading[..., None]


def apply_shading(tiled_bgr, shading):
    """tiled * shading, clipped. Multiplicative, in linear-ish space."""
    lit = tiled_bgr.astype(np.float32) * shading
    return np.clip(lit, 0.0, 255.0)


def specular_pass(tiled_bgr, shading, gloss: float):
    """Screen-blend the bright end of the shading layer back on top.

    A matte porcelain gets almost none of this; polished marble gets a lot.
    Without it every finish looks identically flat and customers cannot tell
    a matte SKU from a gloss one - which is a product failure, not a visual
    nicety.
    """
    g = float(np.clip(gloss, 0.0, 1.0))
    if g == 0.0:
        return np.clip(tiled_bgr.astype(np.float32), 0.0, 255.0)

    # Highlight = how much brighter than the mean the surface is, scaled by
    # gloss, rendered as a white layer to screen-blend on top.
    highlight = np.clip(shading - 1.0, 0.0, None) * g
    spec = np.clip(highlight, 0.0, 1.0) * 255.0

    base = tiled_bgr.astype(np.float32)
    screened = 255.0 - (255.0 - base) * (255.0 - spec) / 255.0
    return np.clip(screened, 0.0, 255.0)


def _mask_bool(mask, shape):
    """Coerce a mask (None / bool / uint8 / float) to a boolean (H, W) array."""
    if mask is None:
        return np.ones(shape, dtype=bool)
    m = np.asarray(mask)
    if m.ndim == 3:
        m = m[..., 0]
    return m > (127 if m.dtype == np.uint8 else 0.5)
