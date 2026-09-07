"""Geometry tests should use synthetic quads with known answers, so a
regression in the homography is caught without eyeballing a render.

  - a square quad maps to an identity-ish transform
  - round-tripping plane_mm -> image_px -> plane_mm is within a pixel
  - scale_from_reference recovers a known 1000mm span
"""

import pytest


@pytest.mark.skip(reason="geometry.homography_from_quad not implemented")
def test_roundtrip():
    ...
