"""Masks and final composite.

Image convention: BGR float32, 0..255 for the blend; the before/after pair is
returned as uint8 (the boundary). Alpha is float32 (H, W, 1), 0..1.
"""

import cv2
import numpy as np


def paintable_mask(surface_mask, occluder_masks, feather_px=1.5):
    """paintable = surface AND NOT union(occluders), with a feathered edge.

    The subtraction is what makes a cabinet look like it is standing ON the
    new tile instead of buried under it. Skipping it is the difference
    between a render and an obvious paste job.

    Returns float32 alpha of shape (H, W, 1), values in 0..1.
    """
    surface = _to_bool(surface_mask)
    paintable = surface.copy()
    for occ in occluder_masks or []:
        paintable &= ~_to_bool(occ, surface.shape)

    alpha = paintable.astype(np.float32)
    if feather_px and feather_px > 0:
        alpha = cv2.GaussianBlur(alpha, (0, 0), sigmaX=float(feather_px), sigmaY=float(feather_px))
    return np.clip(alpha, 0.0, 1.0)[..., None]


def composite(original_bgr, rendered_bgr, mask_alpha):
    """Alpha-blend at full resolution: original*(1-a) + rendered*a."""
    a = mask_alpha
    if a.ndim == 2:
        a = a[..., None]
    base = original_bgr.astype(np.float32)
    top = rendered_bgr.astype(np.float32)
    out = base * (1.0 - a) + top * a
    return np.clip(out, 0.0, 255.0)


def before_after(original_bgr, rendered_bgr):
    """Return the pair the UI slider consumes, as uint8 BGR (before, after)."""
    before = np.clip(original_bgr, 0.0, 255.0).astype(np.uint8)
    after = np.clip(rendered_bgr, 0.0, 255.0).astype(np.uint8)
    return before, after


def _to_bool(mask, shape=None):
    """Coerce a mask (bool / uint8 / float / (H,W,1)) to boolean (H, W)."""
    m = np.asarray(mask)
    if m.ndim == 3:
        m = m[..., 0]
    return m > (127 if m.dtype == np.uint8 else 0.5)
