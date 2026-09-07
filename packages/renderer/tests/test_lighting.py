"""Lighting transfers the room's own illumination onto the tile.
  - shading tracks a brightness gradient and averages to ~1.0 over the mask
  - neutral shading (all ones) leaves the tile unchanged
  - specular_pass is a no-op at gloss 0 and brightens highlights above it
"""

import numpy as np

from renderer import lighting


def _gradient_bgr(w=200, h=80):
    ramp = np.linspace(40.0, 210.0, w, dtype=np.float32)
    img = np.repeat(ramp[None, :], h, axis=0)
    return np.repeat(img[..., None], 3, axis=2)


def test_shading_tracks_gradient_and_normalises():
    img = _gradient_bgr()
    shading = lighting.shading_layer(img, mask=None)
    assert shading.shape == (img.shape[0], img.shape[1], 1)
    # mean brightness inside the mask maps to 1.0
    assert abs(float(shading.mean()) - 1.0) < 0.05
    # dark left < 1 < bright right
    assert shading[:, :20].mean() < 1.0 < shading[:, -20:].mean()


def test_apply_shading_neutral_is_identity():
    tiled = np.full((30, 40, 3), 120.0, np.float32)
    ones = np.ones((30, 40, 1), np.float32)
    out = lighting.apply_shading(tiled, ones)
    assert np.allclose(out, tiled, atol=1e-4)


def test_apply_shading_follows_room_light():
    img = _gradient_bgr()
    shading = lighting.shading_layer(img, mask=None)
    tiled = np.full(img.shape, 120.0, np.float32)  # flat tile
    lit = lighting.apply_shading(tiled, shading)
    assert lit[:, -20:].mean() > lit[:, :20].mean()  # inherits the gradient


def test_specular_zero_gloss_is_noop():
    tiled = np.full((30, 40, 3), 120.0, np.float32)
    shading = np.full((30, 40, 1), 1.5, np.float32)  # bright
    out = lighting.specular_pass(tiled, shading, gloss=0.0)
    assert np.allclose(out, tiled, atol=1e-4)


def test_specular_brightens_highlights():
    tiled = np.full((30, 40, 3), 120.0, np.float32)
    shading = np.full((30, 40, 1), 1.5, np.float32)
    matte = lighting.specular_pass(tiled, shading, gloss=0.1)
    gloss = lighting.specular_pass(tiled, shading, gloss=0.9)
    assert gloss.mean() > matte.mean() > tiled.mean()
