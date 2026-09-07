"""Geometry tests should use synthetic quads with known answers, so a
regression in the homography is caught without eyeballing a render.

  - a square quad maps to an identity-ish transform
  - round-tripping plane_mm -> image_px -> plane_mm is within a pixel
  - scale_from_reference recovers a known 1000mm span
"""

import cv2
import numpy as np

from renderer import geometry


def _map(h, pts):
    """Apply a 3x3 homography to an (N, 2) array of points."""
    pts = np.asarray(pts, dtype=np.float32).reshape(1, -1, 2)
    return cv2.perspectiveTransform(pts, np.asarray(h, dtype=np.float64))[0]


def test_square_quad_is_identity_up_to_scale():
    # A quad that is exactly the canvas (px_per_mm=1) => canvas->image is identity.
    quad = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    h, size = geometry.homography_from_quad(quad, width_mm=100.0, height_mm=100.0, px_per_mm=1.0)
    assert size == (100, 100)
    mapped = _map(h, [[0, 0], [100, 0], [100, 100], [0, 100]])
    assert np.allclose(mapped, np.array(quad), atol=1e-3)


def test_roundtrip_within_a_pixel():
    # A perspective (trapezoid) quad: canvas corners must map to it and back.
    quad = [(120.0, 880.0), (1450.0, 760.0), (1600.0, 1290.0), (40.0, 1340.0)]
    h, (w, h_px) = geometry.homography_from_quad(
        quad, width_mm=3200.0, height_mm=2400.0, px_per_mm=0.25,
    )
    corners = np.array([[0, 0], [w, 0], [w, h_px], [0, h_px]], dtype=np.float32)
    forward = _map(h, corners)
    assert np.allclose(forward, np.array(quad), atol=1.0)

    inv = np.linalg.inv(h)
    back = _map(inv, forward)
    assert np.allclose(back, corners, atol=1.0)


def test_scale_from_reference_recovers_1000mm():
    # px_per_mm = 2 => 1mm is 2 canvas px => mm-per-canvas-px should be 0.5.
    quad = [(120.0, 880.0), (1450.0, 760.0), (1600.0, 1290.0), (40.0, 1340.0)]
    px_per_mm = 2.0
    h, _ = geometry.homography_from_quad(
        quad, width_mm=3200.0, height_mm=2400.0, px_per_mm=px_per_mm,
    )
    # two canvas points exactly 1000mm apart horizontally
    span_canvas = np.array([[10.0, 10.0], [10.0 + 1000.0 * px_per_mm, 10.0]], dtype=np.float32)
    span_image = _map(h, span_canvas)
    mm_per_px = geometry.scale_from_reference(span_image[0], span_image[1], 1000.0, h)
    assert abs(mm_per_px - 1.0 / px_per_mm) < 1e-3
