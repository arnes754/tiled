"""Layout is pure arithmetic, so it is fully testable without a photo.

Cases worth having before the implementation exists:
  - a 600mm tile with 3mm grout produces a 603mm period
  - running_half offsets alternate rows by exactly half a period
  - variant choice is deterministic across runs and reasonably uniform
  - a tile field renders edge to edge with no seam at the canvas boundary
"""

import numpy as np
import pytest

from renderer.layout import (
    _hex_to_bgr,
    cell_offset,
    herringbone,
    tile_canvas,
    variant_for_cell,
)
from renderer.types import TileSpec

PX_PER_MM = 0.5  # 2mm per pixel - fast, and still resolves a 3mm grout line


def solid(bgr, size_px=64):
    """A flat single-colour texture, so a pixel's colour identifies its variant."""
    tex = np.zeros((size_px, size_px, 3), dtype=np.float32)
    tex[:, :] = bgr
    return tex


def spec(**kw) -> TileSpec:
    base = {
        "sku": "TEST-600",
        "size_mm": (600.0, 600.0),
        "texture_paths": ["a.png"],
        "grout_width_mm": 3.0,
        "grout_color": "#C9C4BA",
        "pattern": "stack",
    }
    base.update(kw)
    return TileSpec(**base)


def smallest_period(seq):
    """Smallest p that tiles the whole sequence, or None if aperiodic."""
    for p in range(1, len(seq) // 2 + 1):
        if all(seq[i] == seq[i % p] for i in range(len(seq))):
            return p
    return None


# --------------------------------------------------------------------------
# period and bond offsets
# --------------------------------------------------------------------------


def test_period_includes_grout():
    """600mm tile + 3mm grout is a 603mm period, so cell 1 starts at 603mm."""
    tile = spec()
    assert tile.size_mm[0] + tile.grout_width_mm == 603.0

    canvas = tile_canvas(tile, [solid((10, 20, 30))], 603.0, 603.0, 1.0)
    assert canvas.shape == (603, 603, 3)

    # Grout occupies the last 3mm of the period; the face occupies the rest.
    assert np.allclose(canvas[0, 601], _hex_to_bgr(tile.grout_color))
    assert np.allclose(canvas[0, 100], (10, 20, 30))


def test_stack_has_no_row_offset():
    assert cell_offset("stack", 0, 603.0) == 0.0
    assert cell_offset("stack", 7, 603.0) == 0.0


def test_running_bond_offset():
    """running_half shifts alternate rows by exactly half a period."""
    period = 603.0
    assert cell_offset("running_half", 0, period) == 0.0
    assert cell_offset("running_half", 1, period) == pytest.approx(period / 2)
    assert cell_offset("running_half", 2, period) == 0.0
    assert cell_offset("running_half", 3, period) == pytest.approx(period / 2)


def test_running_third_offset():
    got = [cell_offset("running_third", r, 300.0) for r in range(4)]
    assert got == pytest.approx([0.0, 100.0, 200.0, 0.0])


def test_unknown_pattern_is_rejected():
    with pytest.raises(ValueError, match="unknown pattern"):
        cell_offset("basketweave", 0, 603.0)


def test_herringbone_is_out_of_scope_but_explicit():
    """Both entry points must say so rather than silently doing something else."""
    with pytest.raises(ValueError, match="layout.herringbone"):
        cell_offset("herringbone", 0, 603.0)
    with pytest.raises(NotImplementedError, match="out of P1 scope"):
        herringbone(spec(), 600.0, 600.0, PX_PER_MM)


def test_running_bond_visibly_shifts_the_grid():
    """The vertical grout line in row 1 must not sit under the one in row 0."""
    tile = spec(pattern="running_half", grout_width_mm=10.0)
    period = 610.0
    canvas = tile_canvas(tile, [solid((10, 20, 30))], 3 * period, 2 * period, PX_PER_MM)
    grout = _hex_to_bgr(tile.grout_color)

    def grout_columns(y_mm):
        y = int(y_mm * PX_PER_MM)
        return set(np.flatnonzero(np.all(np.isclose(canvas[y], grout), axis=-1)).tolist())

    row0 = grout_columns(300.0)  # inside the first course
    row1 = grout_columns(915.0)  # inside the second course
    assert row0 and row1
    assert row0 != row1, "running_half rendered the same grid as stack"


# --------------------------------------------------------------------------
# variant selection
# --------------------------------------------------------------------------


def test_variant_is_deterministic():
    """Same cell, same answer - across calls and across processes."""
    first = [variant_for_cell(c, r, 4) for c in range(8) for r in range(8)]
    second = [variant_for_cell(c, r, 4) for c in range(8) for r in range(8)]
    assert first == second


def test_variant_matches_known_values():
    """Pin the hash. If this changes, every previously saved render changes."""
    assert [variant_for_cell(c, 0, 4) for c in range(6)] == [2, 3, 0, 1, 3, 2]


def test_variant_has_no_short_period():
    """Regression: the field must not visibly repeat.

    The original hash reduced with `% n_variants`, which reads only the low
    bits - and those barely moved, so every row walked 0,1,2,3,0,1,2,3. The
    distribution was perfectly uniform, so a counting test passed while the
    render showed obvious diagonal banding at a 4-tile pitch.

    Uniformity is not enough; check for periodicity directly.
    """
    for name, seq in (
        ("row", [variant_for_cell(c, 0, 4) for c in range(64)]),
        ("column", [variant_for_cell(0, r, 4) for r in range(64)]),
        ("diagonal", [variant_for_cell(i, i, 4) for i in range(64)]),
        ("off-row", [variant_for_cell(c, 5, 4) for c in range(64)]),
    ):
        period = smallest_period(seq)
        assert period is None, f"{name} repeats every {period} cells: {seq[:16]}"


def test_variant_is_in_range_and_uses_every_shade():
    vals = [variant_for_cell(c, r, 4) for c in range(40) for r in range(40)]
    assert min(vals) >= 0 and max(vals) <= 3
    counts = [vals.count(i) for i in range(4)]
    assert min(counts) > len(vals) / 8, f"uneven variant spread: {counts}"


def test_variant_handles_negative_coordinates():
    """Offsets can push the datum negative; the hash must still be stable."""
    assert variant_for_cell(-3, -7, 4) == variant_for_cell(-3, -7, 4)
    assert 0 <= variant_for_cell(-3, -7, 4) <= 3
    assert 0 <= variant_for_cell(0, -1, 4) <= 3


def test_single_variant_is_always_zero():
    assert variant_for_cell(5, 9, 1) == 0
    assert variant_for_cell(0, 0, 0) == 0


def test_variants_actually_reach_the_canvas():
    """Four flat textures must produce more than one shade in the field."""
    tile = spec(texture_paths=["a", "b", "c", "d"], grout_width_mm=0.0)
    textures = [solid((v, v, v)) for v in (0, 80, 160, 240)]
    canvas = tile_canvas(tile, textures, 6 * 600.0, 6 * 600.0, PX_PER_MM)
    shades = np.unique(canvas[:, :, 0])
    assert len(shades) >= 3, f"variant selection collapsed to {shades}"


# --------------------------------------------------------------------------
# grout
# --------------------------------------------------------------------------


def test_grout_colour_is_honoured():
    assert np.allclose(_hex_to_bgr("#FF0000"), (0.0, 0.0, 255.0))  # red -> BGR
    tile = spec(grout_color="#FF0000")
    canvas = tile_canvas(tile, [solid((10, 20, 30))], 1206.0, 603.0, 1.0)
    assert np.allclose(canvas[0, 601], (0.0, 0.0, 255.0))


def test_grout_width_is_honoured():
    """A 20mm grout line is 20mm wide, measured at 1px/mm."""
    tile = spec(grout_width_mm=20.0)
    canvas = tile_canvas(tile, [solid((10, 20, 30))], 1240.0, 620.0, 1.0)
    row = np.all(np.isclose(canvas[10], _hex_to_bgr(tile.grout_color)), axis=-1)
    assert row[600:620].all()
    assert not row[599] and not row[620]


def test_zero_grout_draws_no_grout():
    tile = spec(grout_width_mm=0.0)
    canvas = tile_canvas(tile, [solid((10, 20, 30))], 1200.0, 1200.0, PX_PER_MM)
    assert np.allclose(canvas, np.array((10, 20, 30), dtype=np.float32))


def test_bad_grout_colour_is_rejected():
    with pytest.raises(ValueError, match="#RRGGBB"):
        _hex_to_bgr("red")


# --------------------------------------------------------------------------
# canvas shape, dtype, edges
# --------------------------------------------------------------------------


def test_canvas_shape_and_dtype():
    canvas = tile_canvas(spec(), [solid((10, 20, 30))], 3200.0, 2400.0, PX_PER_MM)
    assert canvas.shape == (1200, 1600, 3)
    assert canvas.dtype == np.float32


def test_edge_to_edge_no_gap():
    """A canvas that is not a whole number of periods must still be fully painted.

    A partial tile at the edge is correct; an unpainted strip is not.
    """
    tile = spec(grout_width_mm=0.0)
    canvas = tile_canvas(tile, [solid((10, 20, 30))], 1000.0, 1000.0, PX_PER_MM)
    assert canvas.min() > 0, "unpainted pixels at the canvas edge"
    for edge in (canvas[0], canvas[-1], canvas[:, 0], canvas[:, -1]):
        assert np.all(edge > 0)


def test_offset_shifts_the_field():
    tile = spec(grout_width_mm=10.0)
    args = ([solid((10, 20, 30))], 1220.0, 1220.0, PX_PER_MM)
    assert not np.allclose(
        tile_canvas(tile, *args), tile_canvas(tile, *args, offset_mm=(305.0, 0.0))
    ), "offset_mm had no effect"


def test_non_square_tile():
    """A 300x600 plank has a different period on each axis."""
    tile = spec(size_mm=(300.0, 600.0), grout_width_mm=0.0)
    canvas = tile_canvas(tile, [solid((10, 20, 30))], 900.0, 1200.0, 1.0)
    assert canvas.shape == (1200, 900, 3)


def test_empty_textures_rejected():
    with pytest.raises(ValueError, match="at least one texture"):
        tile_canvas(spec(), [], 600.0, 600.0, PX_PER_MM)


# --------------------------------------------------------------------------
# face rotation
# --------------------------------------------------------------------------


def test_rotation_turns_the_tile_face():
    """rotation_deg rotates the face within its cell, not the lay grid.

    Directional textures (wood-effect planks) need this. Diagonal *lay* is a
    different feature and is not implemented.
    """
    tex = np.zeros((64, 64, 3), dtype=np.float32)
    tex[:32, :] = 255.0  # top half white, so a quarter turn moves it to a side
    tile = spec(grout_width_mm=0.0)
    straight = tile_canvas(tile, [tex], 600.0, 600.0, PX_PER_MM)
    turned = tile_canvas(
        spec(grout_width_mm=0.0, rotation_deg=90.0), [tex], 600.0, 600.0, PX_PER_MM
    )
    assert not np.allclose(straight, turned)


def test_rotation_must_be_a_right_angle():
    with pytest.raises(ValueError, match="multiple of 90"):
        tile_canvas(spec(rotation_deg=45.0), [solid((10, 20, 30))], 600.0, 600.0, PX_PER_MM)


# --------------------------------------------------------------------------
# guardrails
# --------------------------------------------------------------------------


def test_renderer_imports_no_models():
    """CLAUDE.md: packages/renderer must never pull in torch or transformers."""
    import sys

    import renderer.layout  # noqa: F401

    assert not {"torch", "transformers"} & set(sys.modules)
