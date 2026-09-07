"""Shared types. Coordinate spaces are named explicitly everywhere:

    plane_mm   millimetres on the physical surface, origin at the layout datum
    image_px   pixels in the source photograph
    canvas_px  pixels in the flat plane-space texture canvas before warping
"""

from dataclasses import dataclass, field


@dataclass
class TileSpec:
    """One SKU, as the renderer needs it."""

    sku: str
    size_mm: tuple[float, float]          # nominal face size
    texture_paths: list[str]              # one or more shade variants
    grout_width_mm: float = 3.0
    grout_color: str = "#C9C4BA"
    pattern: str = "stack"                # stack | running_half | herringbone
    rotation_deg: float = 0.0
    gloss: float = 0.0                    # 0 matte .. 1 polished
    normal_map_path: str | None = None

    # TODO: validate size_mm against the texture aspect ratio on load - a
    # 300x600 texture declared as 600x600 silently renders wrong.


@dataclass
class Plane:
    """A flat surface in the photo, and the mapping to real-world mm."""

    quad_image_px: list[tuple[float, float]]   # 4 corners, clockwise from top-left
    width_mm: float                            # real width of the quad's top edge
    height_mm: float
    kind: str = "floor"                        # floor | wall
    datum_px: tuple[float, float] | None = None  # layout origin; for walls, the floor line

    # TODO: derive width_mm/height_mm from metric depth when available, so the
    # user does not have to supply a reference measurement.


@dataclass
class RenderRequest:
    photo_path: str
    planes: list[Plane]
    tile: TileSpec
    masks: dict[str, str] = field(default_factory=dict)  # name -> mask png path
    offset_mm: tuple[float, float] = (0.0, 0.0)
    supersample: int = 3
