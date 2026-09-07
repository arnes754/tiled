"""Tile layout in plane space (millimetres). Pure arithmetic - this is where
bond patterns, grout, and shade variation live. Nothing here knows about
perspective.
"""


def tile_canvas(tile, width_mm, height_mm, px_per_mm, offset_mm=(0.0, 0.0)):
    """Render the flat, head-on tiled surface as a canvas_px array.

    period = tile_size + grout_width. For each cell:
      - pick a shade variant deterministically from (col, row) so the same
        request always renders identically, but the field does not visibly
        repeat
      - draw grout in the gap
    """
    raise NotImplementedError


def cell_offset(pattern: str, row: int, period_mm: float) -> float:
    """Horizontal shift for a given row. stack=0, running_half=period/2, ..."""
    raise NotImplementedError


def herringbone(tile, width_mm, height_mm, px_per_mm):
    """Herringbone needs per-cell rotation, so it does not fit the simple
    modulo grid. Kept separate deliberately.
    """
    raise NotImplementedError


def variant_for_cell(col: int, row: int, n_variants: int) -> int:
    """Deterministic pseudo-random variant choice. Must be stable across runs."""
    raise NotImplementedError
