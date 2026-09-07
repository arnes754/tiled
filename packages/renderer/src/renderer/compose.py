"""Masks and final composite."""


def paintable_mask(surface_mask, occluder_masks, feather_px=1.5):
    """paintable = surface AND NOT union(occluders), with a feathered edge.

    The subtraction is what makes a cabinet look like it is standing ON the
    new tile instead of buried under it. Skipping it is the difference
    between a render and an obvious paste job.
    """
    raise NotImplementedError


def composite(original_bgr, rendered_bgr, mask_alpha):
    """Alpha-blend at full resolution."""
    raise NotImplementedError


def before_after(original_bgr, rendered_bgr):
    """Return the pair the UI slider consumes."""
    raise NotImplementedError
