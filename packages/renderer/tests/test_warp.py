"""Warp maps the plane-space canvas into image space. Synthetic checks:
  - identity homography returns the canvas unchanged
  - a quad warp fills the quad interior and leaves the outside black
  - supersampling reduces far-field aliasing versus point sampling
"""

import cv2
import numpy as np

from renderer import geometry, warp


def test_identity_returns_canvas():
    canvas = np.full((40, 60, 3), 200.0, np.float32)
    h = np.eye(3, dtype=np.float64)
    out = warp.warp_to_image(canvas, h, (60, 40), supersample=1)
    assert out.shape == (40, 60, 3)
    assert np.allclose(out, canvas, atol=1e-3)


def test_quad_fills_interior_leaves_outside_black():
    canvas = np.full((200, 200, 3), 255.0, np.float32)
    quad = [(60.0, 40.0), (300.0, 60.0), (320.0, 300.0), (40.0, 280.0)]
    h, _ = geometry.homography_from_quad(quad, width_mm=200.0, height_mm=200.0, px_per_mm=1.0)
    out = warp.warp_to_image(canvas, h, (400, 360), supersample=1)

    # centroid of the quad is inside -> white; a far corner is outside -> black
    cx = int(sum(p[0] for p in quad) / 4)
    cy = int(sum(p[1] for p in quad) / 4)
    assert out[cy, cx, 0] > 200
    assert out[5, 395, 0] < 10


def test_supersample_reduces_aliasing():
    # A high-frequency checkerboard canvas warped into a strongly foreshortened
    # quad: point sampling shimmers, supersampling averages it toward mid-grey.
    n = 400
    checker = np.indices((n, n)).sum(axis=0) % 2
    canvas = (checker[..., None] * np.float32(255.0)).repeat(3, axis=2).astype(np.float32)
    quad = [(10.0, 10.0), (390.0, 120.0), (390.0, 160.0), (10.0, 300.0)]
    h, _ = geometry.homography_from_quad(quad, width_mm=n, height_mm=n, px_per_mm=1.0)

    aliased = warp.warp_to_image(canvas, h, (400, 320), supersample=1)
    smoothed = warp.warp_to_image(canvas, h, (400, 320), supersample=4)

    # far (compressed) band, inside the quad
    band_a = aliased[110:150, 200:380]
    band_s = smoothed[110:150, 200:380]
    # supersampling pulls the compressed region toward the 127 mean -> less spread
    assert band_s.std() < band_a.std()
