"""Monocular depth and surface normals.

Depth Anything 3 (ByteDance) - Apache-2.0 on both code and weights, which is
unusually clean for a model this capable, so this one carries no launch risk.

Used only to PROPOSE a floor quad. The user's four draggable corners stay the
authority, because automatic plane fitting fails often enough on reflective
floors, heavy occlusion and wide-angle phone lenses that a product cannot
depend on it.
"""

DEFAULT_MODEL = "depth-anything/DA3-BASE"


def estimate_depth(image_bgr, model: str = DEFAULT_MODEL, device: str = "mps"):
    """Per-pixel depth. On Apple Silicon use device='mps'."""
    raise NotImplementedError


def normals_from_depth(depth, intrinsics):
    """Surface normals by finite differences on the back-projected points."""
    raise NotImplementedError
