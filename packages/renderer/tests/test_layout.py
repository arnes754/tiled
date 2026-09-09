"""Layout is pure arithmetic, so it is fully testable without a photo.

Cases worth having before the implementation exists:
  - a 600mm tile with 3mm grout produces a 603mm period
  - running_half offsets alternate rows by exactly half a period
  - variant choice is deterministic across runs and reasonably uniform
  - a tile field renders edge to edge with no seam at the canvas boundary
"""

import numpy as np

from renderer import TileSpec
from renderer import layout


def _solid_texture(bgr, size=64):
    img = np.empty((size, size, 3), np.float32)
    img[:] = np.asarray(bgr, np.float32)
    return img


def test_period_includes_grout():
    # 100mm white tile, 10mm black grout -> 110mm period.
    tile = TileSpec(
        sku="t", size_mm=(100.0, 100.0), texture_paths=["x"],
        grout_width_mm=10.0, grout_color="#000000", pattern="stack",
    )
    tex = _solid_texture([255, 255, 255])
    canvas = layout.tile_canvas(
        tile, [tex], width_mm=210.0, height_mm=100.0, px_per_mm=1.0,
    )
    mid = canvas[50]  # a horizontal scanline through tile row 0
    assert mid[50, 0] > 200      # inside first tile [0, 100)
    assert mid[105, 0] < 50      # grout gap [100, 110)
    assert mid[150, 0] > 200     # inside second tile [110, 210)


def test_running_bond_offset():
    period = 110.0
    assert layout.cell_offset("stack", 0, period) == 0.0
    assert layout.cell_offset("stack", 1, period) == 0.0
    assert layout.cell_offset("running_half", 0, period) == 0.0
    assert layout.cell_offset("running_half", 1, period) == period / 2
    assert layout.cell_offset("running_half", 2, period) == 0.0
    assert layout.cell_offset("running_third", 1, period) == period / 3
    assert layout.cell_offset("running_third", 3, period) == 0.0


def test_variant_deterministic_and_uniform():
    a = [layout.variant_for_cell(c, r, 4) for c in range(12) for r in range(12)]
    b = [layout.variant_for_cell(c, r, 4) for c in range(12) for r in range(12)]
    assert a == b                       # stable across runs
    assert set(a) == {0, 1, 2, 3}       # every variant gets used
    assert layout.variant_for_cell(5, 7, 1) == 0   # single variant -> always 0


def test_edge_to_edge_no_gap():
    # grout 0 + white tiles => the whole canvas must be white, including the
    # partial tiles at the right/bottom edges (137 and 89 are not multiples).
    tile = TileSpec(
        sku="t", size_mm=(50.0, 50.0), texture_paths=["x"],
        grout_width_mm=0.0, grout_color="#000000", pattern="stack",
    )
    tex = _solid_texture([255, 255, 255])
    canvas = layout.tile_canvas(
        tile, [tex], width_mm=137.0, height_mm=89.0, px_per_mm=1.0,
    )
    assert (canvas > 200).all()
