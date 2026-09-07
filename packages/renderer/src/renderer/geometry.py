"""Homographies and plane maths. No models here - if the caller supplies four
corners this module is all the geometry the product needs.
"""

import numpy as np


def homography_from_quad(quad_image_px, width_mm, height_mm, px_per_mm):
    """Map plane_mm -> image_px.

    The plane rectangle (0,0)..(width_mm, height_mm) is sent to the four
    image corners. `px_per_mm` sets the resolution of the intermediate
    canvas, not the output.

    Returns (H_canvas_to_image, canvas_size_px).
    """
    raise NotImplementedError  # cv2.getPerspectiveTransform


def plane_from_normals(depth_map, mask, intrinsics):
    """RANSAC-fit a plane to the surface normals inside `mask`.

    Optional path: used when a depth model is available, to *propose* a quad
    the user can then correct. Never the only path - automatic fitting fails
    on reflective floors, heavy occlusion, and wide-angle distortion.
    """
    raise NotImplementedError


def scale_from_reference(p0_image_px, p1_image_px, known_mm, H):
    """Recover mm-per-unit from a user-drawn reference of known length.

    Without this a homography gives the plane's *shape* but not its size, and
    600mm tiles will render at whatever size looks plausible. Getting this
    wrong is the single most common way the output is subtly, confidently
    incorrect.
    """
    raise NotImplementedError


def intrinsics_from_exif(exif: dict, image_size) -> np.ndarray | None:
    """Approximate camera matrix from focal length + sensor size, if present."""
    raise NotImplementedError
