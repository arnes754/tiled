"""Compose builds the paintable alpha and blends the render over the photo.
  - occluders are subtracted from the surface
  - the edge is feathered (intermediate alpha), not a hard step
  - composite is original at alpha 0 and render at alpha 1
  - before_after returns a uint8 BGR pair
"""

import numpy as np

from renderer import compose


def test_occluder_is_subtracted():
    surface = np.ones((100, 100), np.uint8) * 255
    occ = np.zeros((100, 100), np.uint8)
    occ[30:70, 30:70] = 255
    alpha = compose.paintable_mask(surface, [occ], feather_px=0.0)
    assert alpha[50, 50, 0] == 0.0        # inside the occluder -> not paintable
    assert alpha[5, 5, 0] == 1.0          # away from it -> paintable


def test_feather_softens_the_edge():
    surface = np.zeros((100, 100), np.uint8)
    surface[:, :50] = 255                 # sharp vertical edge at x=50
    alpha = compose.paintable_mask(surface, [], feather_px=3.0)
    edge = alpha[50, 46:54, 0]
    assert edge.min() > 0.0 and edge.max() < 1.0   # a ramp, not a step


def test_composite_endpoints():
    original = np.full((10, 10, 3), 30.0, np.float32)
    rendered = np.full((10, 10, 3), 200.0, np.float32)
    zero = np.zeros((10, 10, 1), np.float32)
    one = np.ones((10, 10, 1), np.float32)
    assert np.allclose(compose.composite(original, rendered, zero), original)
    assert np.allclose(compose.composite(original, rendered, one), rendered)


def test_before_after_is_uint8_pair():
    original = np.full((8, 8, 3), 30.0, np.float32)
    rendered = np.full((8, 8, 3), 300.0, np.float32)  # over-range, must clip
    before, after = compose.before_after(original, rendered)
    assert before.dtype == np.uint8 and after.dtype == np.uint8
    assert after.max() == 255
