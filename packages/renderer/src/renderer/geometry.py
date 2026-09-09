"""Homographies and plane maths. No models here - if the caller supplies four
corners this module is all the geometry the product needs.
"""

import cv2
import numpy as np


def homography_from_quad(quad_image_px, width_mm, height_mm, px_per_mm):
    """Map canvas_px -> image_px for a plane defined by four image corners.

    The plane rectangle (0,0)..(width_mm, height_mm), discretised into a
    canvas of ``width_mm * px_per_mm`` by ``height_mm * px_per_mm`` pixels, is
    sent to the four image corners. ``px_per_mm`` sets the resolution of the
    intermediate canvas, not the output.

    ``quad_image_px`` is four (x, y) corners in image_px, clockwise from
    top-left - the same order as ``Plane.quad_image_px``.

    Returns (H_canvas_to_image, canvas_size_px) where canvas_size_px is
    (width_px, height_px) and H is a 3x3 float64 matrix.
    """
    quad = np.asarray(quad_image_px, dtype=np.float32)
    if quad.shape != (4, 2):
        raise ValueError(f"quad_image_px must be 4 (x, y) points, got shape {quad.shape}")

    width_px = max(1, int(round(width_mm * px_per_mm)))
    height_px = max(1, int(round(height_mm * px_per_mm)))
    canvas_corners = np.array(
        [[0.0, 0.0], [width_px, 0.0], [width_px, height_px], [0.0, height_px]],
        dtype=np.float32,
    )  # clockwise from top-left, matching quad order

    h_canvas_to_image = cv2.getPerspectiveTransform(canvas_corners, quad)
    return h_canvas_to_image, (width_px, height_px)


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

    ``p0``/``p1`` are the endpoints in image_px of a reference the user drew
    over something of known real length ``known_mm``. ``H`` is a
    canvas_px -> image_px homography. Returns mm-per-canvas-pixel: multiply a
    canvas-space distance by this to get millimetres.
    """
    inv = np.linalg.inv(np.asarray(H, dtype=np.float64))
    pts_image = np.array([[p0_image_px, p1_image_px]], dtype=np.float32)
    pts_canvas = cv2.perspectiveTransform(pts_image, inv)[0]
    dist_canvas_px = float(np.linalg.norm(pts_canvas[1] - pts_canvas[0]))
    if dist_canvas_px == 0.0:
        raise ValueError("reference endpoints map to the same canvas point")
    return known_mm / dist_canvas_px


def intrinsics_from_exif(exif: dict, image_size) -> np.ndarray | None:
    """Approximate camera matrix from focal length + sensor size, if present."""
    raise NotImplementedError
