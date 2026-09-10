"""Tile layout in plane space (millimetres). Pure arithmetic - this is where
bond patterns, grout, and shade variation live. Nothing here knows about
perspective.

Purity: textures arrive as arrays (loaded by the I/O boundary in cli.py / the
API), never as paths. `TileSpec` is used only for metadata - size, grout,
pattern, rotation. Image convention throughout the renderer: BGR, float32,
range 0..255.
"""

import cv2
import numpy as np


def tile_canvas(tile, textures, width_mm, height_mm, px_per_mm, offset_mm=(0.0, 0.0)):
    """Render the flat, head-on tiled surface as a canvas_px array.

    Coordinate space: the output is ``canvas_px`` - plane millimetres scaled by
    ``px_per_mm``, no perspective. Returns BGR float32, shape (H, W, 3).

    period = tile_size + grout_width. For each cell:
      - pick a shade variant deterministically from (col, row) so the same
        request always renders identically, but the field does not visibly
        repeat
      - draw grout in the gap

    ``textures`` is a non-empty list of BGR float32 arrays (one per shade
    variant); each array is treated as a single tile face. ``offset_mm`` shifts
    the pattern origin, letting the caller slide the grid under the room.
    """
    if not textures:
        raise ValueError("tile_canvas needs at least one texture array")

    tile_w_mm, tile_h_mm = float(tile.size_mm[0]), float(tile.size_mm[1])
    grout_mm = float(tile.grout_width_mm)
    period_x = tile_w_mm + grout_mm
    period_y = tile_h_mm + grout_mm

    width_px = max(1, int(round(width_mm * px_per_mm)))
    height_px = max(1, int(round(height_mm * px_per_mm)))
    canvas = np.empty((height_px, width_px, 3), dtype=np.float32)
    canvas[:] = _hex_to_bgr(tile.grout_color)

    face_w = max(1, int(round(tile_w_mm * px_per_mm)))
    face_h = max(1, int(round(tile_h_mm * px_per_mm)))
    faces = [_prep_face(t, face_w, face_h, tile.rotation_deg) for t in textures]
    n_variants = len(faces)

    off_x, off_y = float(offset_mm[0]), float(offset_mm[1])

    # Iterate the tile rows/cols whose plane span can intersect the canvas.
    # A one-cell margin each side, plus paste-time clipping, covers the partial
    # tiles at the top/left/right/bottom edges (edge-to-edge, no seam).
    row_lo = int(np.floor((0.0 + off_y) / period_y)) - 1
    row_hi = int(np.ceil((height_mm + off_y) / period_y)) + 1
    for row in range(row_lo, row_hi + 1):
        y0_px = int(round((row * period_y - off_y) * px_per_mm))
        x_shift = cell_offset(tile.pattern, row, period_x)
        col_lo = int(np.floor((0.0 + off_x - x_shift) / period_x)) - 1
        col_hi = int(np.ceil((width_mm + off_x - x_shift) / period_x)) + 1
        for col in range(col_lo, col_hi + 1):
            x0_px = int(round((col * period_x + x_shift - off_x) * px_per_mm))
            face = faces[variant_for_cell(col, row, n_variants)]
            _paste(canvas, face, x0_px, y0_px)

    return canvas


def cell_offset(pattern: str, row: int, period_mm: float) -> float:
    """Horizontal shift for a given row. stack=0, running_half=period/2, ...

    Coordinate space: plane_mm. The shift is applied to a whole row of tiles.
    """
    if pattern in ("stack", "", None):
        return 0.0
    if pattern == "running_half":
        return (row % 2) * (period_mm / 2.0)
    if pattern == "running_third":
        return (row % 3) * (period_mm / 3.0)
    if pattern == "herringbone":
        raise ValueError("herringbone is handled by layout.herringbone, not cell_offset")
    raise ValueError(f"unknown pattern {pattern!r}")


def herringbone(tile, width_mm, height_mm, px_per_mm):
    """Herringbone needs per-cell rotation, so it does not fit the simple
    modulo grid. Kept separate deliberately.
    """
    raise NotImplementedError("herringbone is out of P1 scope (see docs/epics.md)")


def variant_for_cell(col: int, row: int, n_variants: int) -> int:
    """Deterministic pseudo-random variant choice. Must be stable across runs.

    Uses a fixed integer hash (independent of Python's randomised str hashing)
    so the same (col, row) always maps to the same variant, in any process.
    """
    if n_variants <= 1:
        return 0

    # Two things matter here and both bite in practice.
    #
    # 1. Mix properly. The obvious `(col*p1) ^ (row*p2) % n` looks fine - the
    #    distribution is perfectly uniform - but the shades still walk
    #    0,1,2,3,0,1,2,3 straight across every row, because `% n` reads only
    #    the low bits and those products barely disturb them. On 600mm tiles
    #    that is a motif repeating every 2.4m. splitmix64's finalizer
    #    avalanches every input bit into the whole word.
    # 2. Reduce off the HIGH bits (Lemire), not `% n`. The low bits of any
    #    multiply-xor hash are the weakest part of it.
    h = (int(col) * 0x9E3779B97F4A7C15) ^ (int(row) * 0xC2B2AE3D27D4EB4F)
    h = (h ^ 0x165667B19E3779F9) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 30
    h = (h * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 27
    h = (h * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 31
    return (h * n_variants) >> 64


# --- helpers (pure, no I/O) -------------------------------------------------


def _hex_to_bgr(color: str) -> np.ndarray:
    """'#RRGGBB' -> BGR float32 (0..255)."""
    s = color.lstrip("#")
    if len(s) != 6:
        raise ValueError(f"grout_color must be #RRGGBB, got {color!r}")
    r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    return np.array([b, g, r], dtype=np.float32)


def _prep_face(texture: np.ndarray, face_w: int, face_h: int, rotation_deg: float) -> np.ndarray:
    """Resize a texture to one tile face (face_w x face_h px), applying a
    90-degree rotation multiple if requested. Returns contiguous BGR float32.
    """
    t = texture
    if t.ndim == 2:
        t = cv2.cvtColor(t.astype(np.float32), cv2.COLOR_GRAY2BGR)
    t = t.astype(np.float32, copy=False)

    r = int(round(rotation_deg)) % 360
    if r in (90, 270):
        # swap target dims so the final face lands at face_w x face_h
        face = cv2.resize(t, (face_h, face_w), interpolation=cv2.INTER_AREA)
        face = np.rot90(face, 1 if r == 90 else 3)
    elif r == 180:
        face = cv2.resize(t, (face_w, face_h), interpolation=cv2.INTER_AREA)
        face = np.rot90(face, 2)
    elif r == 0:
        face = cv2.resize(t, (face_w, face_h), interpolation=cv2.INTER_AREA)
    else:
        raise ValueError(f"rotation_deg must be a multiple of 90 for now, got {rotation_deg}")

    if face.shape[1] != face_w or face.shape[0] != face_h:
        face = cv2.resize(face, (face_w, face_h), interpolation=cv2.INTER_AREA)
    return np.ascontiguousarray(face, dtype=np.float32)


def _paste(canvas: np.ndarray, face: np.ndarray, x0: int, y0: int) -> None:
    """Paste ``face`` at (x0, y0) into ``canvas``, clipped to canvas bounds."""
    h, w = canvas.shape[:2]
    fh, fw = face.shape[:2]
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(w, x0 + fw), min(h, y0 + fh)
    if cx0 >= cx1 or cy0 >= cy1:
        return
    fx0, fy0 = cx0 - x0, cy0 - y0
    canvas[cy0:cy1, cx0:cx1] = face[fy0:fy0 + (cy1 - cy0), fx0:fx0 + (cx1 - cx0)]
